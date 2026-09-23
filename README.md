# Monitor de viviendas Plan Vive (EVHA) — Alicante

Vigila el buscador de `www.evha.es/PLAN-VIVE` (fases: en licitación,
adjudicadas, en construcción, terminadas), filtra por provincia y
modalidad, y te avisa por email cuando una promoción es nueva o cambia
de fase.

## ⚠️ Antes de nada — un aviso honesto

- `planvivecv.es` (dominio "bonito" que redirige a `evha.es/PLAN-VIVE`)
  tiene un `robots.txt` que desaconseja el rastreo automatizado. Son
  datos públicos y el uso aquí es personal (no comercial, no redistribuido,
  frecuencia baja), pero legalmente el robots.txt no es vinculante —
  aun así, por respeto al sitio: **no bajes la frecuencia de menos de
  unas horas**, identifícate en el `User-Agent` con un contacto real, y
  si algún día EVHA publica un feed o API oficial, usa eso en su lugar.
- El scraping se basa en la estructura HTML actual (clases `.card-proyecto`,
  `.disponibilidad-box`, etc.). **Si EVHA rediseña la web, el parseo se
  romperá** y tendrás que ajustar los selectores en `main.py`
  (función `parse_promociones`).

## Qué hace

1. Cada 6 horas (configurable), descarga las 4 fases:
   `?fase=SL` (licitación), `?fase=SA` (adjudicadas), `?fase=CO`
   (construcción), `?fase=TE` (terminadas).
2. Parsea cada tarjeta de promoción y extrae: expediente (identificador
   único, ej. `A-ECSA-25/00101`), municipio, provincia, dirección,
   modalidad(es) y nº de viviendas.
3. Filtra por `PROVINCIA_FILTRO` y `MODALIDADES_FILTRO` (editables al
  principio de `main.py`).
4. Compara cada expediente con lo guardado en Firestore (colección
   `promociones`). Si es nuevo, o si cambió de fase respecto a la
   última comprobación, lo marca como "cambio".
5. Si hay cambios, escribe un documento en la colección `mail`, que la
   extensión oficial **Trigger Email** de Firebase recoge y envía.

## Despliegue paso a paso

### 1. Requisitos
- Cuenta de Google / proyecto de Firebase (plan **Blaze**, de pago por
  uso — necesario porque las funciones programadas y las llamadas
  salientes a internet no están disponibles en el plan gratuito Spark).
- Python 3.12, Firebase CLI y sus dependencias instaladas desde
  `requirements.txt`.

### 2. Crear el proyecto
```bash
firebase login
firebase projects:create tu-proyecto-id   # o usa uno existente
cd planvive-monitor
firebase use --add   # selecciona tu proyecto
```
Esto genera un fichero `.firebaserc` con el ID de tu proyecto (no lo
incluyo yo porque depende de ti).

### 3. Activar Firestore
En la consola de Firebase (console.firebase.google.com) → Firestore
Database → Crear base de datos (modo producción, la región que
prefieras, p. ej. `eur3`).

### 4. Instalar la extensión "Trigger Email"
En la consola → Extensions → busca **"Trigger Email"** (de Firebase) →
instálala. Te pedirá:
- Un servidor SMTP. Opciones sencillas:
  - **Gmail**: usa una "contraseña de aplicación" de tu cuenta de
    Google (no tu contraseña normal) — actívala en
    myaccount.google.com/apppasswords.
  - **SendGrid** (más robusto para uso continuado): crea una API key
    gratuita.
- El nombre de la colección donde escribirás los correos: pon `mail`
  (coincide con lo que usa el código).

### 5. Configurar el email de destino
Edita `main.py` y cambia:
```python
EMAIL_DESTINO = "TU_EMAIL@ejemplo.com"
```
Cambia también el contacto en el `User-Agent` (buena práctica).
Ajusta si quieres `PROVINCIA_FILTRO` y `MODALIDADES_FILTRO`.

### 6. Instalar dependencias y desplegar
```bash
python3 -m pip install -r requirements.txt
firebase deploy --only functions,firestore:rules
```

Para probar solo el scraping sin Java ni Firestore:
```bash
python3 -c "import main; print(sum(len(main.fetch_fase(fase)) for fase in main.FASES))"
```

Los emuladores de Firebase siguen necesitando Java 21 o superior aunque
el runtime de la función sea Python, porque el emulador de Firestore está
implementado en Java.

### 7. Probar sin esperar 6 horas
Tras el despliegue, Firebase te da una URL para
`comprobarViviendasManual`, algo como:
```
https://europe-west1-tu-proyecto-id.cloudfunctions.net/comprobarViviendasManual
```
Ábrela en el navegador o con `curl`. Debería devolver un JSON tipo
`{"total": X, "cambios": Y}` y, si `Y > 0`, deberías recibir un email
en pocos minutos. La primera vez `cambios` será igual a `total` porque
todo es "nuevo" (no había nada guardado antes en Firestore).

### 8. Revisar logs
```bash
firebase functions:log
```
o desde la consola de Firebase → Functions → Logs.

## Estructura del proyecto
```
planvive-monitor/
├── firebase.json
├── firestore.rules
├── README.md
├── main.py            ← toda la lógica (scraping, comparación, email)
└── requirements.txt
```

## Posibles mejoras futuras
- Página web (Firebase Hosting) que lea Firestore y muestre el
  histórico de cambios, en vez de depender solo del email.
- Guardar un histórico de cambios en una colección `cambios` además de
  sobrescribir `promociones`, para tener trazabilidad completa.
- Añadir Slack/Telegram como canal adicional de aviso.
