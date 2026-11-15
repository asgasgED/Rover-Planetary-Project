# TerraRover — Contrato técnico de integración y límites científicos

## Entrada geoespacial

`<REGION>/DEM.tif` es el raster numérico de elevaciones (Float32, una banda, CRS del cuerpo). `Mapa_2D.tiff` es una imagen RGBA para geovisualización; **no** debe usarse para calcular elevaciones. `Mapa_2D.png` es la miniatura. `Terreno_3D.html` utiliza Plotly y referencia `../plotly.min.js` desde la carpeta regional. `Terreno_3D.obj` es una malla con alturas locales `z = z_real - z_mínima`. `metadatos.json` contiene descripción y procedencia, que deben contrastarse con el raster final si presentan campos heredados de una versión anterior.

El catálogo toma las características directamente de `DEM.tif`, nunca de los colores de `Mapa_2D.tiff`. El generador no modifica las fuentes y solo importa carpetas con seis entregables completos y dimensiones exactamente 5.000 × 5.000 m.

## Estados de evidencia

| Estado | Significado |
|---|---|
| `disponible` | Se copiaron los seis archivos y se comprobó el raster físico en el generador. |
| `auditoria_historica` | Región presente en auditoría previa (19 conjuntos); fuente completa no incluida en la web. |
| `cli_reportada` | Región marciana presente en salidas de terminal compartidas (8 conjuntos). |
| `pendiente` | Región prevista; no hay salida final revisada (seis lunares adicionales). |

### Nota sobre los primeros cinco DEM

Timanfaya procede de una carpeta final aportada por el equipo. La Joya, MDRS Utah, Jezero y Mare Tranquillitatis se reprocesaron como muestras **a partir de archivos fuente originales compartidos**, usando los scripts del proyecto geoespacial y validándose geométricamente a 5.000 × 5.000 m. Se incluyeron para probar una web que requiere DEM reales, y **no sustituyen automáticamente las entregas canónicas de otros integrantes**.

## Algoritmo de comparación v0

El algoritmo calcula siete indicadores geomorfológicos. `skew` de elevación se obtiene con SciPy, el filtro local de 3 píxeles mide diferencia frente a media espacial y el TPI usa 15 píxeles. El coseno se calcula sobre el vector sin escalado estadístico entre rasgos. La puntuación no equivale a probabilidad ni validación de similitud. Por ello, la UI usa un **índice sin unidad**, no un porcentaje de certeza.

### Restricción de escala

El DEM terrestre típico (~30 m), lunar SLDEM (~59 m) y marciano MOLA (~463 m) pueden tener áreas idénticas de 5 km pero distinto contenido geomorfológico observable. La primera versión bloquea la comparación morfológica fina si una fuente tiene paso nativo >250 m. Este umbral es una **regla operativa conservadora del producto**, no un estándar científico establecido. En una siguiente versión debe ajustarse con protocolo de evaluación multiescala, resolución efectiva y bandas de incertidumbre.

## Contrato futuro de simulación

**No implementado:** importar telemetría real y reproducir trayectorias. La pantalla existe solo como lugar de conexión futura.

Asegurar compatibilidad con los campos que entregue el rol de Robotics & Rover Simulation Engineer:

```text
JSON: distance_travelled, average_speed, elapsed_time_sec,
      maximum_slope, max_roll_deg, max_pitch_deg,
      max_uninterrupted_distance, stall_events,
      stability_loss_events, route_completion

CSV:  time_sec, x, y, z, speed_ms, roll_deg, pitch_deg,
      slope_deg, uninterrupted_dist_m, stall_flag,
      instability_flag, progress_pct
```

La simulación futura debe referenciar el DEM/versiones de entrada, parámetros físicos del rover, fecha, estado, tiempo de ejecución y trazabilidad de archivos. No llamar "validada" a una ejecución visual sin controles y resultados independientes.

## Próximos pasos

1. Importar todas las carpetas reales de `entrega_5km` con `scripts/preparar_catalogo.py` y verificar el número de seis archivos por terreno.
2. Reconciliar los campos antiguos de metadatos con el GeoTIFF final, especialmente celdas y resolución después de remuestreo.
3. Ejecutar evaluación morfométrica multiescala, máscaras de agua, normalización de variables y baselines.
4. Integrar nuevos DEM de alta resolución de Marte/Luna antes de comparar obstáculos finos.
5. Conectar archivos JSON/CSV/PNG de simulación reales sin mezclar resultados con estimaciones del navegador.
6. Probar accesibilidad y respuesta en navegador real y desplegar en GitHub Pages o Vercel.
