# Tarea: desplegar y probar en local el proyecto "planvive-monitor"

## Contexto

Tengo un proyecto de **Firebase Cloud Functions** ya generado en la carpeta
`planvive-monitor/` (está en la raíz de este workspace, o pégalo ahí si
no lo está). Su función es hacer scraping periódico del buscador de
viviendas de protección pública del Plan Vive de la Generalitat
Valenciana (`www.evha.es/PLAN-VIVE`), detectar cambios (promociones
nuevas o cambios de fase: en licitación → adjudicadas → en construcción
→ terminadas) filtrando por provincia de Alicante y modalidad de venta,
y avisar por email cuando hay cambios.

Estructura del proyecto:
```
planvive-monitor/
├── firebase.json       ← config de Firebase, incluye bloque "emulators"
├── firestore.rules      ← reglas de Firestore (bloqueadas para clientes)
├── README.md            ← documentación completa del proyecto
└── functions/
    ├── index.js          ← toda la lógica: fetch, parseo con cheerio,
    │                        comparación en Firestore, envío de email
    └── package.json      ← dependencias (cheerio, firebase-admin,
                             firebase-functions)
```

Quiero **probarlo en local con los emuladores de Firebase**, sin
desplegarlo todavía a producción ni gastar cuota real.

## Lo que necesito que hagas, paso a paso

1. **Comprueba requisitos**: verifica que existan `node` (v20+) y
   `firebase-tools` instalados (`node -v`, `firebase --version`). Si
   falta `firebase-tools`, instálalo globalmente
   (`npm install -g firebase-tools`).

2. **Instala las dependencias** de las funciones:
   ```
   cd planvive-monitor/functions
   npm install
   cd ..
   ```

3. **Asocia un proyecto de Firebase** (puede ser uno de prueba, no hace
   falta que sea el definitivo, y para probar en local con emuladores
   **no** hace falta tener el plan de pago Blaze activado):
   ```
   firebase login
   firebase use --add
   ```
   Si no tengo todavía ningún proyecto de Firebase creado, dime cómo
   crear uno gratis desde la CLI o guíame para crearlo desde
   console.firebase.google.com antes de este paso.

4. **Arranca los emuladores** de Functions y Firestore (la config ya
   está en `firebase.json`, con Functions en el puerto 5001, Firestore
   en el 8080, y la UI de emuladores en el 4000):
   ```
   firebase emulators:start --only functions,firestore
   ```

5. **Prueba la función manualmente.** El proyecto expone un endpoint
   HTTP pensado exactamente para esto, `comprobarViviendasManual`, que
   hace todo el ciclo (descarga las 4 fases reales de evha.es, parsea,
   filtra, compara con Firestore y escribe en la colección `mail` si
   hay cambios) sin tener que esperar a la ejecución programada (que en
   el emulador no se dispara sola). La URL será del tipo:
   ```
   http://127.0.0.1:5001/<PROJECT_ID>/europe-west1/comprobarViviendasManual
   ```
   Averigua el `<PROJECT_ID>` real (aparece en el log al arrancar los
   emuladores) y haz la petición con `curl` o abriéndola en el
   navegador. Debería devolver un JSON tipo `{"total": N, "cambios": M}`.

6. **Verifica los resultados en la Emulator UI**
   (`http://127.0.0.1:4000/firestore`):
   - Comprueba que la colección `promociones` tiene documentos con
     campos `expediente`, `municipio`, `provincia`, `direccion`,
     `disponibilidad`, `fase`.
   - Comprueba que la colección `mail` (si `cambios > 0`) tiene
     documentos con `to`, `message.subject` y `message.text`/`html`
     con contenido legible sobre las promociones.

7. **Revisa los logs** de la terminal donde corren los emuladores en
   busca de warnings tipo `"Promoción sin expediente detectada"`. Si
   aparecen muchos, es señal de que el parseo de `functions/index.js`
   (función `parsePromociones`) necesita ajuste — en ese caso dime
   cuántos y en qué campos falla, y ayúdame a corregir los selectores
   de `cheerio` comparándolos con el HTML real que te puedo pegar.

8. **No pruebes el envío real de email en local** — la extensión
   "Trigger Email" de Firebase no está instalada/emulada en este
   proyecto todavía; basta con confirmar que el documento en la
   colección `mail` se genera correctamente. El envío real se
   comprobará ya en producción, tras instalar la extensión desde la
   consola de Firebase.

## Restricciones importantes

- El emulador **no** simula la web de EVHA: las peticiones de scraping
  salen de verdad a `https://www.evha.es`. No pongas la función en un
  bucle de pruebas repetido sin necesidad — con 1-2 ejecuciones
  manuales por sesión de pruebas es suficiente. No reduzcas la
  frecuencia por debajo de unas horas ni elimines el `User-Agent`
  identificativo que hay en el código.
- No modifiques `EMAIL_DESTINO`, `PROVINCIA_FILTRO` ni
  `MODALIDADES_FILTRO` en `functions/index.js` salvo que yo te lo pida
  explícitamente.
- No ejecutes `firebase deploy` en esta tarea — es solo para pruebas
  locales.

## Resultado esperado

Al terminar, quiero:
- Confirmación de que los emuladores arrancan sin errores.
- Confirmación de que `comprobarViviendasManual` responde con un JSON
  válido y con `total > 0`.
- Una captura o resumen de qué hay en las colecciones `promociones` y
  `mail` tras la primera ejecución.
- Si el parseo falla en algún campo, un resumen claro de qué falla y
  una propuesta de corrección en `parsePromociones`.
