import json
import os
import sys
from pathlib import Path

import requests

FIELDS = {
    "municipio": "municipio",
    "provincia": "provincia",
    "fase": "código de fase",
    "fase_nombre": "fase",
    "estado_inscripcion": "estado de inscripción",
    "promotor": "constructora",
    "direccion": "calle",
    "barrio": "barrio",
    "disponibilidad": "viviendas/modalidad",
}


def format_availability(value: object) -> str:
    if not value:
        return "No indicado"
    if not isinstance(value, list):
        return str(value)
    return ", ".join(
        f"{item.get('unidades', 'No indicado')} viviendas en {item.get('modalidad', 'No indicado')}"
        for item in value
        if isinstance(item, dict)
    ) or "No indicado"


def format_value(field: str, value: object) -> str:
    if value is None or value == "":
        return "No indicado"
    if field == "disponibilidad":
        return format_availability(value)
    return str(value)


def format_promotion(promotion: dict) -> str:
    return "\n".join(
        [
            f"  Expediente: {format_value('expediente', promotion.get('expediente'))}",
            f"  Municipio: {format_value('municipio', promotion.get('municipio'))}",
            f"  Provincia: {format_value('provincia', promotion.get('provincia'))}",
            f"  Zona/barrio: {format_value('barrio', promotion.get('barrio'))}",
            f"  Calle: {format_value('direccion', promotion.get('direccion'))}",
            f"  Fase: {format_value('fase_nombre', promotion.get('fase_nombre'))}",
            f"  Estado de inscripción: {format_value('estado_inscripcion', promotion.get('estado_inscripcion'))}",
            f"  Constructora: {format_value('promotor', promotion.get('promotor'))}",
            f"  Disponibilidad: {format_value('disponibilidad', promotion.get('disponibilidad'))}",
        ]
    )


def load_promotions(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return {item["expediente"]: item for item in data.get("promociones", [])}


def describe_changes(previous: dict[str, dict], current: dict[str, dict]) -> list[str]:
    changes = []
    for expediente, promotion in current.items():
        if expediente not in previous:
            changes.append("NUEVA PROMOCIÓN\n" + format_promotion(promotion))
            continue
        old = previous[expediente]
        changed_fields = [
            (field, label)
            for field, label in FIELDS.items()
            if old.get(field) != promotion.get(field)
        ]
        if changed_fields:
            details = [
                f"CAMBIO EN PROMOCIÓN: {expediente}",
                f"  Municipio: {format_value('municipio', promotion.get('municipio'))}",
                f"  Provincia: {format_value('provincia', promotion.get('provincia'))}",
                f"  Zona/barrio: {format_value('barrio', promotion.get('barrio'))}",
                f"  Calle: {format_value('direccion', promotion.get('direccion'))}",
                "  Datos modificados:",
            ]
            details.extend(
                f"    - {label}: {format_value(field, old.get(field))} -> "
                f"{format_value(field, promotion.get(field))}"
                for field, label in changed_fields
            )
            changes.append("\n".join(details))
    for expediente, promotion in previous.items():
        if expediente not in current:
            changes.append("PROMOCIÓN RETIRADA\n" + format_promotion(promotion))
    return changes


def send_telegram(message: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("Telegram no configurado; se omite el aviso.")
        return
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": message},
        timeout=30,
    )
    response.raise_for_status()


def build_messages(changes: list[str]) -> list[str]:
    if not changes:
        return ["EVHA Tracker: no hay nada nuevo en la actualización."]

    prefix = "EVHA Tracker: cambios detectados\n\n"
    messages = []
    current = prefix
    for change in changes:
        separator = "" if current == prefix else "\n\n"
        candidate = current + separator + change
        if len(candidate) > 3900 and current != prefix:
            messages.append(current)
            current = prefix + change
        else:
            current = candidate
    messages.append(current)
    return messages


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--test":
        send_telegram("EVHA Tracker: mensaje de prueba recibido correctamente.")
        print("Aviso de prueba preparado.")
        return
    if len(sys.argv) != 3:
        raise SystemExit("Uso: notify_changes.py datos-anteriores.json datos-nuevos.json")
    changes = describe_changes(load_promotions(Path(sys.argv[1])), load_promotions(Path(sys.argv[2])))
    for message in build_messages(changes):
        send_telegram(message)
    print(f"Aviso preparado: {len(changes)} cambios relevantes.")


if __name__ == "__main__":
    main()
