# TerraRover — guía rápida (español)

**TerraRover** es una plataforma de investigación de **Killa Coders** para explorar modelos de elevación de la Tierra, Marte y la Luna y estudiar posibles analogías topográficas. La interfaz pública está en inglés; esta guía resume cómo funciona.

## ¿Qué puedo hacer?

- **Planet Explorer:** visualizar dónde están las regiones del catálogo.
- **Terrain Catalog:** buscar lugares y consultar sus fichas, mapas 2D, relieve 3D y descargas disponibles.
- **Morphological Analysis / Planetary Comparator:** comparar pendientes, distribución de alturas y otras métricas derivadas de los **GeoTIFF numéricos**.
- **Find Analog Sites:** explorar candidatos terrestres frente a una región lunar/marciana. Es un ranking **exploratorio**, no una certeza geológica.
- **Submit a DEM:** subir un GeoTIFF numérico de 5 × 5 km, solo si el administrador habilitó la función. Al aceptarse, el archivo se hace **público** y queda marcado como **sin verificación científica**.
- **Rover Simulation:** apartado reservado para integración futura; actualmente no ejecuta ningún rover.

## Estructura de los datos

Cada carpeta final del equipo contiene: `DEM.tif` (alturas numéricas), `Mapa_2D.tiff` (visualización coloreada georreferenciada), `Mapa_2D.png`, `Terreno_3D.html`, `Terreno_3D.obj` y `metadatos.json`.

El proyecto contempla **33 entradas**: 17 Tierra, 9 Marte y 7 Luna. Que aparezcan en el catálogo no significa que todas estén importadas con sus archivos finales en una copia nueva. La instalación local del equipo puede tener los 33 DEM; siempre hay que verificar `data/catalog.json` y las carpetas reales.

## Puesta en marcha (Windows)

Ejecuta en la raíz del **proyecto con código**, no en este ZIP de documentación:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-backend.txt
.\.venv\Scripts\python.exe -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

Abre `http://127.0.0.1:8000/`. Si vas a importar los entregables de tu equipo, consulta [Catálogo y datos](CATALOG_AND_DATA.md) y [Instalación](SETUP_AND_RUN.md).

## Advertencias científicas

El DEM terrestre típico tiene ~30 m de paso nativo, el lunar SLDEM ~59 m y el marciano MOLA ~463 m. Aunque las áreas finales sean 5 × 5 km, la resolución no es equivalente. El índice de coseno **no representa un porcentaje de similitud geológica**, y un DEM no permite determinar por sí solo la composición, cohesión, fricción o transitabilidad de un rover.

## Publicación

Para desplegar toda la plataforma se requiere un servidor de **Python/FastAPI**; **GitHub Pages por sí solo** no ejecuta el backend. Antes de publicarla, desactiva la subida comunitaria o incorpora autenticación, moderación y límites persistentes. Además, coordina con el equipo la licencia y derechos de los logos, imágenes y datos.
