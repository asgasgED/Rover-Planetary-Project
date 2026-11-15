# TerraRover v2.0 — Cambios del frontend

## Lo implementado
- Portada cinematográfica original con planetas de Tierra, Marte y Luna, selección con botones, movimientos suaves y tres accesos visuales.
- Paleta espacial oscura manteniendo el rojo/cian del proyecto; tema claro disponible.
- Panel lateral contraíble en escritorio y desplegable en móvil.
- Metodología horizontal antes del hero; al abrirla explica el flujo de los datos.
- Eliminadas del menú las rutas «Resultados y auditoría», «Metodología» y «Simulación». Las antiguas URL de esas secciones regresan al inicio.
- Catálogo, explorador, detalle geoespacial, gráficos y comparación existentes permanecen accesibles.
- Sección de composición solo dentro de cada ficha. Cinco entradas de estudios/muestras tienen datos preliminares del material del equipo; las otras indican pendiente.
- Explicación de la escala general del coseno [-1,1] y de que la cifra no es un porcentaje geológico.
- Carpeta `datos_para_importar/entrega_5km/` con 33 nombres listos para recibir los seis archivos por región; script de importación reutilizado y probado.
- Gráficos planetarios optimizados a WebP a partir de las imágenes de referencia proporcionadas por el usuario. No son imágenes científicas del DEM local.

## Fuera de esta versión
- Simulación de rover / telemetría Webots.
- El nuevo algoritmo de verificación y clasificación geológica calibrado, todavía en desarrollo.
- 28 DEM completos que no se proporcionaron para esta revisión: el catálogo incluye sus nombres, no se simulan archivos.
- Valores de composición química no asociados a muestras o aún sin verificar.

## QA
- 33 entradas catalogadas; cinco fuentes DEM reales comprobadas a 5.000 × 5.000 m.
- 33 directorios de importación creados.
- Importador probado con un terreno real, genera siete métricas, seis archivos publicables y dependencia Plotly.
- Pruebas Node de rutas/algoritmo y pruebas Python de catálogo; CSS analizado sin errores sintácticos.
- La inspección gráfica con navegador headless fue bloqueada por las restricciones del entorno. Recomendamos verificación final en Chrome/Edge/Firefox antes del despliegue.
