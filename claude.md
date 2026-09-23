# EVHA Tracker - Contexto del proyecto

## Proposito

Aplicacion pequena en Python y HTML que monitoriza promociones de vivienda del Plan Vive de EVHA. Muestra promociones de venta de los municipios Alicante/Alacant y San Vicente del Raspeig, en la provincia de Alicante.

La web publicada es:
https://albertosanchez22.github.io/evha-tracker-alicante/

Repositorio:
https://github.com/albertosanchez22/evha-tracker-alicante

## Estructura

- `main.py`: scraping de las cuatro fases de EVHA, parseo HTML, filtros y enriquecimiento de barrios mediante Nominatim.
- `scripts/generate_data.py`: ejecuta el scraping, aplica los filtros finales y genera `public/data.json`.
- `scripts/notify_changes.py`: compara el JSON anterior y el nuevo y envia avisos por Telegram.
- `public/index.html`: interfaz publica, filtros, tabla y contador de actualizacion.
- `public/data.json`: datos generados; no editarlo manualmente salvo para una prueba puntual.
- `.github/workflows/update-promociones.yml`: actualizacion automatica cada 6 horas y publicacion.
- `.github/workflows/deploy-pages.yml`: despliegue de `public/` en GitHub Pages despues de cada push a `main`.
- `requirements.txt`: `requests` y `beautifulsoup4`.

## Filtros actuales

- Provincia: `ALICANTE`.
- Municipios: `ALICANTE/ALACANT` y `SAN VICENTE DEL RASPEIG`.
- Modalidad: `VENTA`.
- Fases: `SL`, `SA`, `CO` y `TE`.

## Flujo de actualizacion

1. GitHub Actions copia el JSON anterior a `/tmp/data-anterior.json`.
2. `python scripts/generate_data.py` descarga EVHA y escribe un nuevo JSON con `ultimaActualizacion` y `proximaActualizacion` seis horas despues.
3. `scripts/notify_changes.py` compara promociones nuevas, retiradas y cambios en fase, estado de inscripcion, constructora, calle, barrio o disponibilidad.
4. Telegram envia un mensaje en cada ejecucion cuando existen `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`. Si no hay cambios, envia `EVHA Tracker: no hay nada nuevo en la actualizacion.`
5. El workflow hace commit si cambia `public/data.json` y hace push. Ese push dispara el despliegue de Pages.

## Contador del frontend

`public/index.html` usa `proximaActualizacion` del JSON. Cuando vence:

- muestra `Actualizando...`;
- intenta descargar `data.json` con cache-busting;
- si el servidor todavia devuelve el JSON viejo, espera 60 segundos antes de repetir;
- cuando llega un JSON nuevo, vuelve a mostrar la cuenta atras normal.

La espera de 60 segundos evita recargas continuas mientras GitHub Actions o GitHub Pages terminan de publicar.

## Comandos locales

Crear entorno e instalar dependencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Generar datos:

```bash
python scripts/generate_data.py
```

Servir la web localmente:

```bash
python -m http.server 8000 --directory public
```

Validar sintaxis Python:

```bash
python3 -m py_compile main.py scripts/generate_data.py scripts/notify_changes.py
```

Probar Telegram manualmente:

```bash
python scripts/notify_changes.py --test
```

Comparar dos JSON:

```bash
python scripts/notify_changes.py datos-anteriores.json datos-nuevos.json
```

## Variables y secretos

Telegram necesita estos secretos en GitHub Actions:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Nunca guardar tokens, credenciales ni datos sensibles en el repositorio.

## Reglas para futuros cambios

- Mantener los filtros actuales salvo peticion expresa.
- No modificar manualmente `public/data.json` como solucion permanente; corregir el generador.
- Respetar la frecuencia baja del scraping y la pausa de Nominatim.
- Usar `apply_patch` para editar archivos existentes.
- Ejecutar una validacion enfocada despues de cada cambio.
- No hacer commit automaticamente desde el agente salvo peticion expresa.
- Si cambia la estructura HTML de EVHA, revisar primero `parse_promociones` en `main.py`.
- Si cambia la logica de avisos, actualizar tambien esta documentacion y `README.md`.
