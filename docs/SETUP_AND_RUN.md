# Setup and local use

## Prerequisites

- Windows with PowerShell and VS Code, or another system with a compatible Python environment.
- Python 3.11 is a tested/used project target; Python 3.11–3.13 may work if compatible Rasterio/GDAL wheels are installed. This is a compatibility expectation, not a guarantee for every platform.
- Disk space for the application plus published DEMs and Plotly JS. Planetary *source* products can be much larger than the processed deliverables.
- Node.js **optional**, only for JavaScript syntax/tests. The site does not need npm to install its runtime web dependencies.

## Install dependencies (PowerShell)

Open the actual code repository root `TerraRover_Plataforma/`:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-backend.txt
```

Never copy `.venv/` between operating systems; recreate it locally. The `.venv` folder is **not** where any public scientific DEM or shared API endpoint belongs.

## Load data

Place the team-delivered six-file region folders into:

```text
datos_para_importar/entrega_5km/<REGION_ID>/
```

Place `plotly.min.js` at `datos_para_importar/entrega_5km/plotly.min.js` if it accompanies the supplied 3D HTML views. If available, the upstream `auditoria/auditoria.json` may be referenced explicitly during a manual catalog build.

**Explicit first import:**

```powershell
.\.venv\Scripts\python.exe scripts/preparar_catalogo.py --source "datos_para_importar/entrega_5km"
```

**With historical audit:**

```powershell
.\.venv\Scripts\python.exe scripts/preparar_catalogo.py --source "datos_para_importar/entrega_5km" --audit "datos_para_importar/entrega_5km/auditoria/auditoria.json"
```

This is an **administrative/local** step, not a visitor-facing web action. A normal backend startup also detects complete new team folders and adds missing entries incrementally. It does not modify the upstream original folders.

**Important:** The explicit `preparar_catalogo.py` rebuild writes a new catalog from its inputs; on a live instance with community submissions, back up `data/catalog.json` and `data/regions/` before rebuilding to avoid accidentally dropping existing community records.

## Start the server

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

Go to `http://127.0.0.1:8000/`. Check `http://127.0.0.1:8000/api/health` for a minimal health response. For development only, `--reload` can be appended. The site is not fully functional via double-clicking `index.html` or `python -m http.server` because scientific comparisons require the API.

## Deployment-related setting

```powershell
$env:TERRAROVER_PUBLIC_UPLOADS = "false"
```

Set this **before** starting Uvicorn if public community uploads should be disabled. The current code defaults to enabled when this setting is unset. Do not expose that default to an unrestricted public internet audience without additional authentication, moderation, quotas and storage controls.

## Verify a dataset import

1. Check `data/catalog.json` and identify the region's `status` and `assets` paths.
2. Confirm that `data/regions/<REGION_ID>/DEM.tif` actually exists.
3. View the terrain detail page; open 2D and 3D views, where present.
4. Run a comparison between two regions that both have published numeric rasters.
5. Remember that passing import checks does not independently validate geology, chemistry or rover safety.

## Deployment compatibility

GitHub Pages can host static frontend files but cannot run this Python/FastAPI backend. For a public site, use a host for a persistent Python process or a separate API service and place the `/api/*` paths behind a compatible reverse proxy. Avoid exposing this prototype's upload endpoint directly before security hardening.
