# Troubleshooting

## `No existe: datos_para_importar/entrega_5km`

Confirm the terminal's current working directory is the actual **`TerraRover_Plataforma/`** root and check spelling. Use:

```powershell
Get-Location
Test-Path "datos_para_importar/entrega_5km"
```

If the folder is elsewhere, supply its actual absolute path as `--source`. An extra character at the end of `entrega_5km` is enough to make the path invalid.

## `ModuleNotFoundError` or Rasterio/GDAL import failure

Install the project's dependencies using the **same interpreter** used to start Uvicorn:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-backend.txt
.\.venv\Scripts\python.exe -c "import fastapi, rasterio, scipy; print('Dependencies OK')"
```

On Python versions without available GDAL/Rasterio binary wheels, use a compatible supported interpreter rather than copying binary packages between environments.

## Web loads but catalog is empty or some terrain says not imported

- Verify the catalog is reachable at `/data/catalog.json`.
- Confirm the region actually exists in `data/regions/<REGION_ID>/` with an authentic numeric `DEM.tif`.
- A named region can exist with `status=pendiente`, `auditoria_historica` or `cli_reportada`; a label is not proof of file delivery.
- The startup importer only accepts complete six-file *team* bundles and does not overwrite already published complete entries.
- If you manually rebuild the catalog, first back up community data; rebuilding is not the same as incremental import.

## 3D viewer not rendering

The regional `Terreno_3D.html` expects a Plotly JS file in its **parent** directory. Confirm `data/regions/plotly.min.js` is accessible and that the viewer's relative path is preserved. Open the web through Uvicorn, not `file://` double-click.

## No score / unsupported comparison

Two **different** published numeric DEMs are required. The backend reports resolution warnings for coarse Martian MOLA sources. Scores are exploratory and may be absent for invalid or degenerate vectors. Never fill missing values with a fake score.

## Scientific map looks like a photo or calculations seem wrong

`Mapa_2D.tiff` is a **color** map. Only `DEM.tif` should be passed to the numeric science engine. Re-check NoData flags, projection units, vertical datum, and whether stale `metadatos.json` fields mismatch raster properties.

## 404 for `/api/interpret` or AMD status disappeared

This is intentional in **public v4.2**. The public API removes AMD routes, diagnostics and credentials. Numeric analysis and charts do not need any external AI endpoint.

## Upload returns 403 / 413 / 422 / 429 / 507

| Error | Common cause |
|---|---|
| 403 | `TERRAROVER_PUBLIC_UPLOADS=false` on the server |
| 413 | File exceeds 16 MiB |
| 422 | Invalid/nonnumeric GeoTIFF, wrong extent/CRS/coverage, invalid title |
| 429 | Basic upload count exceeded in the process-local rate limiter |
| 507 | Maximum community dataset count (30) reached |

A valid upload is **public**, not private. Use a stronger moderation and storage policy for real public deployment.

## Light UI text is readable only when selected

This indicates a CSS contrast regression, not a data issue. Inspect `src/styles.css`, `src/v3_palette.css`, `src/v4_light.css` and `src/public.css` cascade order. Check default and active states of links, tabs, badges and buttons on the actual viewport; high-contrast focus/hover styling cannot substitute for readable default text.

## GitHub Pages deployment missing analysis endpoints

GitHub Pages does **not** execute Python. Host `/api/*` on a separate Python service or use another platform capable of running Uvicorn. Ensure browser routes and static/public assets resolve properly.
