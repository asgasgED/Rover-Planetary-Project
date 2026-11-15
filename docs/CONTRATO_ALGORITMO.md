# TerraRover — Contrato del algoritmo de comparación

## Estado

La plataforma integra el **algoritmo morfológico inicial v0**, suministrado por el equipo, y calcula siete características a partir de `DEM.tif`. **No incorpora** todavía la siguiente versión del algoritmo de verificación de analogías ni una clasificación geológica validada.

La interfaz actualmente utiliza:

- `src/analysis.js`: comparación por similitud coseno y restricciones (en particular el caso MOLA).
- `scripts/preparar_catalogo.py`: extrae siete métricas, perfiles e histogramas desde GeoTIFF numéricos.
- `data/catalog.json`: almacena las métricas publicadas que consume la interfaz.

## Formato de un terreno importado

La estructura del catálogo por región contiene `id`, `title`, `body`, `source`, `status`, `native_resolution_m`, `elevation_min_m`, `elevation_max_m`, `assets`, `metrics`, `profile`, `histogram` y advertencias.

```json
{
  "id": "La_Joya_NASADEM",
  "body": "Tierra",
  "native_resolution_m": 30.87,
  "metrics": {
    "integral_hipsometrica": null,
    "pendiente_media_deg": null,
    "pendiente_std_deg": null,
    "asimetria_elevacion": null,
    "razon_area_3d2d": null,
    "tri_normalizado": null,
    "tpi_std_normalizado": null
  }
}
```

**Nota:** los `null` anteriores son solo un ejemplo de contrato y **no son mediciones**. El preparador coloca números calculados a partir del raster real.

## Integración futura propuesta (NO implementada)

Para integrar una nueva versión, aislar el cálculo de puntuación detrás de una función de comparación que reciba los dos perfiles, un protocolo y su compatibilidad de resolución, y devuelva un objeto con `status`, `score`, `method`, `metrics`, `uncertainty` y `warnings`. Mantener el método v0 separado para poder compararlo con el nuevo. No presentar un valor de coseno como porcentaje de equivalencia geológica.

El algoritmo debe rechazar comparaciones sin datos suficientes; no inventar resultados. La simulación del rover y su telemetría no son parte de esta versión.
