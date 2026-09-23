import json
import os
import sys
from pathlib import Path

import requests

FIELDS = {
    "fase_nombre": "fase",
    "estado_inscripcion": "estado de inscripción",
    "promotor": "constructora",
    "direccion": "calle",
    "barrio": "barrio",
    "disponibilidad": "viviendas/modalidad",
}


def load_promotions(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text())
    return {item["expediente"]: item for item in data.get("promociones", [])}


def describe_changes(previous: dict[str, dict], current: dict[str, dict]) -> list[str]:
    changes = []
    for expediente, promotion in current.items():
        if expediente not in previous:
            changes.append(
                f"NUEVA promoción: {expediente} - {promotion.get('municipio', 'sin municipio')}"
            )
            continue
        old = previous[expediente]
        for field, label in FIELDS.items():
            if old.get(field) != promotion.get(field):
                changes.append(
                    f"{expediente}: {label} cambió de "
                    f"'{old.get(field, 'No indicado')}' a '{promotion.get(field, 'No indicado')}'"
                )
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


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--test":
        send_telegram("EVHA Tracker: mensaje de prueba recibido correctamente.")
        print("Aviso de prueba preparado.")
        return
    if len(sys.argv) != 3:
        raise SystemExit("Uso: notify_changes.py datos-anteriores.json datos-nuevos.json")
    changes = describe_changes(load_promotions(Path(sys.argv[1])), load_promotions(Path(sys.argv[2])))
    if not changes:
        print("Sin cambios relevantes.")
        return
    message = "EVHA Tracker: cambios detectados\n\n" + "\n".join(changes)
    send_telegram(message[:3900])
    print(f"Avisos preparados: {len(changes)}")


if __name__ == "__main__":
    main()
