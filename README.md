# EVHA Tracker Alicante

Scraper y tabla pública de promociones del Plan Vive de EVHA. La web muestra promociones en los municipios de Alicante/Alacant y San Vicente del Raspeig, provincia de Alicante, con modalidad de venta.

## Cómo funciona

1. `scripts/generate_data.py` descarga las cuatro fases del buscador de EVHA.
2. `main.py` extrae expediente, municipio, provincia, dirección, promotora, modalidades y estado de inscripción.
3. Las coordenadas públicas de EVHA se consultan en OpenStreetMap/Nominatim para obtener el barrio cuando está disponible.
4. El script genera `public/data.json`.
5. GitHub Actions ejecuta la actualización cada 6 horas.
6. GitHub Pages sirve `public/index.html`, con búsqueda, filtro por fase y cuenta atrás hasta la siguiente actualización.

## Probar localmente

Requisitos: Python 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/generate_data.py
python -m http.server 8000 --directory public
```

Abre `http://localhost:8000`.

## Publicación

El repositorio público es:

`https://github.com/albertosanchez22/evha-tracker-alicante`

La web está publicada en:

`https://albertosanchez22.github.io/evha-tracker-alicante/`

Los workflows de `.github/workflows/` publican la web al hacer push y regeneran los datos cada 6 horas. También se pueden ejecutar manualmente desde la pestaña **Actions** de GitHub.

## Avisos gratuitos por Telegram

El workflow compara cada actualización con la anterior y detecta promociones nuevas, retiradas y cambios en fase, estado de inscripción, constructora, calle, barrio o viviendas/modalidad. Envía un mensaje en cada ejecución; si no hay cambios, indica que no hay nada nuevo. Para activar avisos:

1. Crea un bot con `@BotFather` en Telegram y copia su token.
2. Envía un mensaje al bot y obtiene tu `chat_id` con `https://api.telegram.org/bot<TOKEN>/getUpdates`.
3. En GitHub, abre **Settings → Secrets and variables → Actions** y crea los secretos `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`.

Sin esos secretos, el workflow actualiza la web normalmente y simplemente omite el aviso.

## Configuración

Los filtros principales están en `scripts/generate_data.py`:

- `MUNICIPIOS_FILTRO`
- Provincia `ALICANTE`
- Modalidad `VENTA`

El scraping respeta una frecuencia baja y usa un `User-Agent` identificativo. Nominatim se consulta con una pausa y solo para coordenadas no guardadas en la ejecución actual.

## Nota sobre los datos

Los selectores dependen del HTML actual de EVHA. Si la web cambia su estructura, habrá que revisar `parse_promociones` en `main.py`. Los barrios pueden aparecer como `No indicado` cuando EVHA no publica coordenadas o OpenStreetMap no tiene cartografiada la ubicación.
