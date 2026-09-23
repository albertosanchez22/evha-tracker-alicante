import logging
import time
from urllib.parse import parse_qs, urlparse
from typing import Any

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.evha.es/PLAN-VIVE/castellano/buscador_viv.php"
FASES = {
    "SL": "En licitacion",
    "SA": "Adjudicadas",
    "CO": "En construccion",
    "TE": "Terminadas",
}
PROVINCIA_FILTRO = "ALICANTE"
MODALIDADES_FILTRO = ["VENTA"]
USER_AGENT = (
    "MonitorViviendasAlicante/1.0 "
    "(uso personal, sin fines comerciales)"
)
GEOCODER_USER_AGENT = "EvhaTracker/1.0 (uso personal)"
_BARRIOS_CACHE: dict[str, str] = {}
BARRIOS_MANUALES = {
    "A-ECSA-24/00003": "Complejo Vistahermosa",
    "A-ECSA-24/00006": "El Baver",
    "A-ECSA-26/00001": "El Baver",
    "A-ECSA-25/00096": "Rabassa",
    "A-ECSA-25/00095": "Rabassa",
    "A-ECSA-25/00094": "Rabassa",
    "A-ECSA-24/00008": "Joan Pau II / Juan Pablo II",
    "A-ECSA-24/00009": "El Pau",
}


def fetch_fase(codigo_fase: str) -> list[dict[str, Any]]:
    response = requests.get(
        f"{BASE_URL}?fase={codigo_fase}",
        headers={"User-Agent": USER_AGENT},
        timeout=30,
    )
    response.raise_for_status()
    return parse_promociones(response.text, codigo_fase)


def parse_promociones(content: str, codigo_fase: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(content, "html.parser")
    resultados = []

    for card in soup.select(".card-proyecto"):
        title = " ".join(card.select_one(".card-title").get_text(" ").split()) if card.select_one(".card-title") else ""
        municipio, provincia = title, ""
        if title.endswith(")") and "(" in title:
            municipio, provincia = title.rsplit("(", 1)
            municipio = municipio.strip()
            provincia = provincia[:-1].strip()

        promotor_node = card.select_one(".card-text.small.text-muted strong")
        direccion_node = card.select_one(".card-text.small:not(.text-muted) strong")
        estado_node = card.select_one(".inscripcion-title")
        mapa_node = card.select_one('a[href*="google.com/maps"]')
        promotor = promotor_node.get_text(" ").strip() if promotor_node else ""
        direccion = direccion_node.get_text(" ").strip() if direccion_node else ""
        coordenadas = _extraer_coordenadas(mapa_node.get("href", "") if mapa_node else "")
        estado_inscripcion = (
            " ".join(estado_node.get_text(" ").split())
            if estado_node
            else "No indicado"
        )

        expediente = None
        for text_node in card.select_one(".d-grid").contents if card.select_one(".d-grid") else []:
            if getattr(text_node, "name", None) is None:
                candidate = str(text_node).strip()
                if candidate and _es_expediente(candidate):
                    expediente = candidate
                    break

        disponibilidad = []
        for span in card.select(".disponibilidad-box span"):
            text = " ".join(span.get_text(" ").split())
            parts = text.split(" en ", 1)
            if len(parts) == 2 and parts[0].isdigit():
                disponibilidad.append({
                    "unidades": int(parts[0]),
                    "modalidad": parts[1].strip().upper(),
                })

        if not expediente:
            logging.warning(
                "Promocion sin expediente detectada, se omite: %s, %s",
                municipio,
                direccion,
            )
            continue

        resultados.append({
            "expediente": expediente,
            "municipio": municipio,
            "provincia": provincia,
            "promotor": promotor,
            "direccion": direccion,
            "coordenadas": coordenadas,
            "estado_inscripcion": estado_inscripcion,
            "disponibilidad": disponibilidad,
            "fase": codigo_fase,
        })

    return resultados


def _es_expediente(value: str) -> bool:
    parts = value.split("-")
    return (
        len(parts) == 3
        and len(parts[0]) == 1
        and parts[0].isupper()
        and parts[1].isupper()
        and "/" in parts[2]
        and parts[2].replace("/", "").isdigit()
    )


def _extraer_coordenadas(url: str) -> tuple[float, float] | None:
    valores = parse_qs(urlparse(url).query).get("q", [])
    if not valores:
        return None
    try:
        latitud, longitud = valores[0].split(",", 1)
        return float(latitud), float(longitud)
    except (ValueError, IndexError):
        return None


def enriquecer_barrios(promociones: list[dict[str, Any]]) -> None:
    for promocion in promociones:
        if promocion["expediente"] in BARRIOS_MANUALES:
            promocion["barrio"] = BARRIOS_MANUALES[promocion["expediente"]]
            continue
        coordenadas = promocion.get("coordenadas")
        if not coordenadas:
            promocion["barrio"] = "No indicado"
            continue
        clave = f"{coordenadas[0]:.6f},{coordenadas[1]:.6f}"
        if clave not in _BARRIOS_CACHE:
            if _BARRIOS_CACHE:
                time.sleep(1.1)
            try:
                response = requests.get(
                    "https://nominatim.openstreetmap.org/reverse",
                    params={
                        "lat": coordenadas[0],
                        "lon": coordenadas[1],
                        "format": "jsonv2",
                        "addressdetails": 1,
                        "zoom": 18,
                    },
                    headers={"User-Agent": GEOCODER_USER_AGENT},
                    timeout=30,
                )
                response.raise_for_status()
                address = response.json().get("address", {})
                _BARRIOS_CACHE[clave] = (
                    address.get("neighbourhood")
                    or address.get("suburb")
                    or address.get("quarter")
                    or address.get("city_district")
                    or "No indicado"
                )
            except (requests.RequestException, ValueError):
                logging.warning("No se pudo obtener el barrio para %s", clave)
                _BARRIOS_CACHE[clave] = "No indicado"
        promocion["barrio"] = _BARRIOS_CACHE[clave]


def pasa_filtro(promocion: dict[str, Any]) -> bool:
    if PROVINCIA_FILTRO and promocion["provincia"].upper() != PROVINCIA_FILTRO:
        return False
    if MODALIDADES_FILTRO and not any(
        modalidad in detalle["modalidad"]
        for detalle in promocion["disponibilidad"]
        for modalidad in MODALIDADES_FILTRO
    ):
        return False
    return True


