import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main

OUTPUT = Path(__file__).resolve().parents[1] / "public" / "data.json"
MUNICIPIOS_FILTRO = {"ALICANTE/ALACANT", "SAN VICENTE DEL RASPEIG"}


def siguiente_actualizacion(now: datetime) -> datetime:
    siguiente_minuto = 5 - now.minute % 5
    return now.replace(second=0, microsecond=0) + timedelta(minutes=siguiente_minuto)


def main_script() -> None:
    promociones = []
    vistos = set()
    for codigo_fase in main.FASES:
        for promocion in main.fetch_fase(codigo_fase):
            if not main.pasa_filtro(promocion):
                continue
            if promocion["provincia"].upper() != "ALICANTE":
                continue
            if promocion["municipio"].upper() not in MUNICIPIOS_FILTRO:
                continue
            if not any("VENTA" in item["modalidad"] for item in promocion["disponibilidad"]):
                continue
            if promocion["expediente"] in vistos:
                continue
            vistos.add(promocion["expediente"])
            promocion["fase_nombre"] = main.FASES[codigo_fase]
            promociones.append(promocion)

    main.enriquecer_barrios(promociones)
    now = datetime.now(timezone.utc)
    data = {
        "promociones": sorted(promociones, key=lambda item: item["expediente"]),
        "ultimaActualizacion": now.isoformat(),
        "proximaActualizacion": siguiente_actualizacion(now).isoformat(),
    }
    for promocion in data["promociones"]:
        promocion.pop("coordenadas", None)

    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print(f"Generadas {len(promociones)} promociones en {OUTPUT}")


if __name__ == "__main__":
    main_script()
