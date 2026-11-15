# TerraRover v4 — Actualización de interfaz clara y AMD TokenLab

**Fecha:** 15 de noviembre de 2026  
**Alcance:** reparación de la interfaz existente, sin alterar los DEM ni la simulación.

## 1. Qué cambió

- Interfaz **solo clara**: fondo blanco/gris, texto oscuro y tarjetas científicas negras con texto blanco; se retiró el interruptor de modo oscuro.
- Contraste revisado por reglas CSS: navegación, botones, mapa, catálogo, detalles, formularios, paneles científicos y alertas. Paleta de referencia: `#000000`, `#FFFFFF`, `#626262`, `#2F28FB` (reservado como acento menor), `#FC3C23`, `#FC3E00`, `#B80C09`.
- Logos de Killa Coders y NASA Space Apps Challenge en variantes PNG con transparencia, dentro de `assets/brand/`. El logo NASA Space Apps identifica el evento, no implica aval oficial de la aplicación.
- Comparación con MOLA: se muestra **coseno exploratorio regional** si existen métricas reales, en lugar de «No score». Se mantiene la advertencia de incompatibilidad a escala fina y nunca se interpreta el coseno como porcentaje de equivalencia geológica.
- API AMD: petición multimodal según ejemplo SDK de AMD TokenLab, sin parámetro opcional `reasoning_effort`; al fallar una solicitud de imagen con errores recuperables, intenta una vez con información **numérica** solamente.
- Errores AMD separados por HTTP 401, 403, 404, 429, 5xx y conexión. Un HTTP 500 del proveedor **no demuestra por sí solo** que la clave sea incorrecta.
- Botón `Test AMD connection` en el comparador: prueba real, **texto solamente**, con una solicitud breve (puede consumir cuota).
- Si falla AMD, el análisis numérico continúa visible. El frontend aplica límite de espera para evitar cargadores indefinidos.
- Mejoras responsive para el explorador y el comparador en tablet y teléfono.

## 2. Instalación recomendada si **YA IMPORTASTE LOS 33 DEM**

**Usa `TerraRover_v4_ACTUALIZACION_SIN_DATOS.zip`**, no sobrescribas el proyecto completo con un ZIP nuevo.

1. **Detén Uvicorn** en VS Code con `Ctrl + C`.
2. Haz copia de tu carpeta `TerraRover_Plataforma`.
3. Extrae el ZIP de actualización y **copia su contenido sobre** los archivos homónimos de tu `TerraRover_Plataforma` actual.
4. **No borres, no muevas y no sobrescribas**:
   - `datos_para_importar/entrega_5km/`
   - `data/regions/`
   - `data/catalog.json`
   - `.env`
   - `.venv/`
5. Inicia de nuevo el backend:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

6. Abre `http://127.0.0.1:8000/#/comparador`, actualiza con `Ctrl + F5` para invalidar el CSS guardado por Chrome.

**No necesitas regenerar el catálogo si los 33 DEM ya aparecen como «DEM imported».** Si no aparecen como disponibles, ejecuta el script de importación del paquete anterior, no este parche.

## 3. Dónde colocar la clave de AMD

En la raíz `TerraRover_Plataforma/.env` (mismo nivel de `index.html`):

```dotenv
AMD_BASE_URL=https://api.tokenlab.amd.com/v1
AMD_MODEL=Qwen3.8-27B
AMD_API_KEY=TU_CLAVE_PRIVADA_AQUI
ENVIAR_A_IA=true
```

**No colocarla en `.venv`, JavaScript, HTML o JSON.** `.venv` es el entorno virtual de Python y `.env` almacena la configuración privada del servidor. Si editas `.env`, reinicia Uvicorn.

El backend usa `OpenAI(base_url=AMD_BASE_URL, api_key=AMD_API_KEY)`, `client.chat.completions.create(model=AMD_MODEL, messages=[...])`, y añade un gráfico en formato `image_url` con `data:image/png;base64,...` en la solicitud multimodal. Solo si es necesario utiliza la recuperación numérica sin imagen.

**No subir `.env` a GitHub.** `.gitignore` lo excluye, pero debes comprobar que no haya sido añadido previamente al índice de Git.

## 4. Diagnóstico: «AMD TokenLab request failed (InternalServerError)»

1. Navega a `http://127.0.0.1:8000/api/health`. Busca `ai_enabled:true` y `ai_key_configured:true`. No muestra tu clave.
2. En **Planetary Comparator**, pulsa **Test AMD connection**. Esto envía una petición mínima de texto al modelo; no requiere un DEM.
3. Interpreta el resultado:

| Respuesta | Significado recomendado |
|---|---|
| `401` | Clave rechazada; revisa `AMD_API_KEY`. |
| `403` | Sin permiso de modelo o cuenta. |
| `404` | Modelo o endpoint incorrecto; verifica los IDs en AMD TokenLab. |
| `429` | Límite de peticiones o cuota. |
| `500`, `502`, `503`, `504` | Error del proveedor o servicio; **puede ocurrir con clave válida**. Reintenta o consulta su estado. |
| Error de conexión | Comprueba conectividad, firewall, proxy y dominio. |
| Prueba de texto OK, interpretación visual falla | Puede ser incompatibilidad del modelo, formato multimodal o carga del servidor; el backend intenta con métricas sin imagen. |

No podemos confirmar la disponibilidad en vivo de tu cuenta de AMD ni probar la clave desde el paquete. Nunca publiques capturas con tu API key.

## 5. Por qué algunos terrenos antes decían «No score»

El código anterior devolvía `ok:false` cuando una fuente superaba **250 m/celda**. Eso bloqueaba **todos** los resultados de Marte MOLA, incluso aunque el DEM de 5 × 5 km y sus siete indicadores estuvieran calculados. La v4 distingue:

- **Sin datos numéricos**: no se calcula ningún score, porque falta `DEM.tif` o un perfil válido.
- **Con datos, pero MOLA muy grueso**: muestra un coseno **regional exploratorio** acompañado de advertencias grandes. No verifica semejanza topográfica fina ni transitabilidad.
- **Con resoluciones más próximas**: muestra el coseno **no calibrado** y permite ejecutar análisis numérico más detallado. El índice sigue sin ser un porcentaje de similitud geológica.

Para una comparación físicamente más sólida necesitarán el algoritmo multiescala del equipo y, preferentemente, DEM planetarios más detallados. El frontend seguirá preparado para sustituir la fórmula heredada.

## 6. Archivos modificados por el parche

```text
index.html
assets/earth-vector.svg
assets/brand/killa-coders-transparent.png
assets/brand/space-apps-transparent.png
src/app.js
src/analysis.js
src/live_analysis.js
src/v4_light.css
backend/api.py
docs/V4_SETUP_AND_FIXES.md
```

Se preservan `backend/analysis_engine.py`, el catálogo científico, los datos originales y las muestras incluidas, sin modificarlos.

## 7. Verificaciones realizadas

- 16 pruebas automáticas de Python: análisis DEM, seguridad de rutas, comparación regional, disponibilidad de datos, errores de AMD y recuperación numérica con respuesta simulada.
- Pruebas de JavaScript sobre flujo de comparación y navegación, y chequeo sintáctico de módulos.
- **No** se comprobó la API TokenLab real por ausencia de tu clave ni el renderizado automático de Chromium por una restricción del navegador de pruebas. Inspecciona visualmente escritorio/móvil en tu equipo antes de publicar.


## TerraRover v4.1 — UI polish and AMD timeout mitigation

**Apply the v4.1 no-data patch on top of v4; retain `.env`, `.venv`, `data/catalog.json`, `data/regions/` and all `datos_para_importar/entrega_5km/` folders.**

1. Scores now show `cos(θ)` **on a separate row** below the numerical value, with responsive spacing.
2. All/Earth/Mars/Moon are white-text pills on black (red for selected); catalog Details is permanently red, never dependent on hover.
3. Region detail tabs/labels are high-contrast black/white with red accents, respecting the original DEM colors.
4. AMD connection test checks only a small text query. A successful check does **not** verify the longer scientific request.
5. Qwen3.8-27B uses `reasoning_effort=low` by default in the integration; AMD's model documentation notes omitted reasoning effort means `xhigh` thinking. Full scientific interpretation is text-only by default, grounded in numeric metrics; the optional image checkbox enables multimodal input.
6. The scientific analysis runs independently of the AI provider. Timeouts/provider errors never generate an invented AI interpretation.

In `TerraRover_Plataforma/.env`, add optional lines (other existing AMD settings remain):

```dotenv
AMD_REASONING_EFFORT=low
AMD_AI_TIMEOUT_SECONDS=90
```

After applying the patch, **restart** Uvicorn and hard-refresh the browser with `Ctrl + F5`.

If TokenLab continues timing out while the short connection test passes, the model/service is accepting basic requests but not finishing generation within the configured timeout. Review model capacity, account limits and try text-only mode. Do not publish the API key or interpret this as proof that the key is invalid.
