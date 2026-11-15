"""Community GeoTIFF submission and auto-publication for TerraRover.

No submissions replace Killa Coders' curated datasets. Public upload is restricted
in size and number, requires consent, and is identified as unreviewed.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from io import BytesIO
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import tempfile
import threading
import time

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.warp import transform as transform_coordinates
from fastapi import File, Form, HTTPException, Request, UploadFile
from pydantic import ValidationError

from scripts.preparar_catalogo import SIX, apply_source, default_entry, compute_features

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / 'data' / 'catalog.json'
REGIONS = ROOT / 'data' / 'regions'
IMPORT_SOURCE = ROOT / 'datos_para_importar' / 'entrega_5km'
LOCK = threading.RLock()
REQUESTS = defaultdict(list)
MAX_FILE = 16 * 1024 * 1024


def _read_catalog():
    try:
        data = json.loads(CATALOG.read_text(encoding='utf-8'))
        if not isinstance(data.get('items'), list):
            raise ValueError('Catalog missing items')
        return data
    except (ValueError, OSError) as exc:
        raise HTTPException(503, 'The terrain catalog is temporarily unavailable.') from exc


def _save_catalog(data):
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    tmp = CATALOG.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')
    os.replace(tmp, CATALOG)


def import_new_team_deliverables():
    """Add only unseen complete 6-file 5 km folders at server startup.

    Existing published catalog rows and user uploads remain untouched.
    """
    if not IMPORT_SOURCE.is_dir() or not CATALOG.is_file():
        return 0
    with LOCK:
        catalog = _read_catalog()
        byid = {entry.get('id'): entry for entry in catalog['items']}
        count = 0
        for folder in sorted(IMPORT_SOURCE.iterdir()):
            if not folder.is_dir() or not all((folder / fn).is_file() for fn in SIX):
                continue
            if folder.name in byid and byid[folder.name].get('status') == 'disponible':
                continue
            if not re.fullmatch(r'[A-Za-z0-9_-]{3,100}', folder.name):
                continue
            entry = byid.get(folder.name) or default_entry(folder.name)
            if not apply_source(entry, folder, REGIONS.parent, 'original verified team deliverable'):
                continue
            if folder.name not in byid:
                catalog['items'].append(entry)
            count += 1
        if count:
            src_js = IMPORT_SOURCE / 'plotly.min.js'
            if src_js.is_file():
                shutil.copy2(src_js, REGIONS / 'plotly.min.js')
            _save_catalog(catalog)
        return count


def _check_rate(request: Request):
    # Basic in-process backstop, not a replacement for public deployment controls.
    ip = request.client.host if request.client else 'unknown'
    now = time.monotonic()
    requests = REQUESTS[ip]
    requests[:] = [t for t in requests if now - t < 3600]
    if len(requests) >= 3:
        raise HTTPException(429, 'Upload limit reached for this hour. Please try later.')
    requests.append(now)


def _read_and_validate(tiff: Path):
    try:
        with rasterio.open(tiff) as ds:
            if ds.driver != 'GTiff' or ds.count != 1:
                raise ValueError('Submit a single-band numeric GeoTIFF (not a color TIFF).')
            if ds.crs is None or not ds.crs.is_projected:
                raise ValueError('The DEM must declare a projected, metric coordinate system.')
            unit = ds.crs.linear_units
            if unit and unit.lower() not in ('metre', 'meter', 'metres', 'meters', 'm'):
                raise ValueError('The raster coordinate unit must be meters.')
            if ds.width < 3 or ds.height < 3 or ds.width * ds.height > 2_000_000:
                raise ValueError('Raster grid must contain 3–2,000,000 elevation cells.')
            extent_x = abs(ds.res[0] * ds.width)
            extent_y = abs(ds.res[1] * ds.height)
            if abs(extent_x - 5000) > 1 or abs(extent_y - 5000) > 1:
                raise ValueError('Please submit a 5,000 × 5,000 m DEM. The scientific footprint is not 5 × 5 km.')
            band = ds.read(1, masked=True).astype(np.float64)
            mask = ~np.ma.getmaskarray(band) & np.isfinite(np.asarray(band))
            if mask.mean() < 0.5:
                raise ValueError('At least half the terrain must contain valid elevation samples.')
            if not np.issubdtype(np.dtype(ds.dtypes[0]), np.number):
                raise ValueError('Terrain elevations must use a numeric band.')
            center = (ds.bounds.left + ds.bounds.right) / 2, (ds.bounds.top + ds.bounds.bottom) / 2
            crs = ds.crs
            data = np.asarray(band)
            # Raster preview is a relative elevation visualization; not a satellite image.
            elev = np.where(mask, data, np.nan)
            center_xy = center
            cell_m = (abs(ds.res[0]), abs(ds.res[1]))
            return elev, center_xy, crs, cell_m
    except (rasterio.errors.RasterioError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc


def _preview(elevation: np.ndarray, output: Path):
    fig, ax = plt.subplots(figsize=(6.6, 5.6), dpi=115)
    im = ax.imshow(elevation, cmap='terrain', origin='upper', interpolation='nearest')
    ax.set_title('Relative terrain visualization · submitted DEM', fontsize=10)
    ax.set_xlabel('Raster column')
    ax.set_ylabel('Raster row')
    cb = fig.colorbar(im, ax=ax, fraction=.043, pad=.035)
    cb.set_label('Elevation (m)')
    fig.tight_layout()
    fig.savefig(output, format='png', dpi=115, facecolor='white')
    plt.close(fig)


def submit_community_dem(request: Request, file: UploadFile, title: str, body: str, public_consent: str):
    if os.getenv('TERRAROVER_PUBLIC_UPLOADS', 'true').lower() not in ('true', '1', 'yes'):
        raise HTTPException(403, 'Public DEM submissions are disabled on this deployment.')
    if public_consent not in ('true', 'on', 'yes'):
        raise HTTPException(400, 'Explicit consent is required before publishing an openly accessible DEM.')
    title = title.strip()
    if not 3 <= len(title) <= 80:
        raise HTTPException(422, 'Choose a terrain title between 3 and 80 characters.')
    if body not in ('Tierra', 'Marte', 'Luna'):
        raise HTTPException(422, 'Choose Earth, Mars or Moon.')
    if Path(file.filename or '').suffix.lower() not in ('.tif', '.tiff'):
        raise HTTPException(415, 'Only numeric .tif and .tiff files are supported.')
    _check_rate(request)
    with tempfile.TemporaryDirectory(prefix='terrarover_upload_') as td:
        temp = Path(td) / 'candidate.tif'
        total = 0
        with temp.open('wb') as out:
            while True:
                part = file.file.read(1024 * 1024)
                if not part:
                    break
                total += len(part)
                if total > MAX_FILE:
                    raise HTTPException(413, 'The maximum supported GeoTIFF size is 16 MB.')
                out.write(part)
        if total < 128:
            raise HTTPException(422, 'The file does not contain a readable numeric GeoTIFF.')
        elev, xy, crs, spacing = _read_and_validate(temp)
        try:
            features = compute_features(temp)
        except (OSError, ValueError, RuntimeError) as exc:
            raise HTTPException(422, 'Could not calculate the seven numeric terrain features.') from exc
        # Use known geographic transform only for Earth. Planetary CRS is not WGS84.
        lat = lon = None
        if body == 'Tierra':
            try:
                longitudes, latitudes = transform_coordinates(crs, 'EPSG:4326', [xy[0]], [xy[1]])
                lon, lat = float(longitudes[0]), float(latitudes[0])
                if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                    lat = lon = None
            except Exception:
                pass
        # Only community items are allowed here; no collision with curated catalog.
        ident = 'Community_' + secrets.token_hex(7)
        with LOCK:
            catalog = _read_catalog()
            if sum(str(e.get('id', '')).startswith('Community_') for e in catalog['items']) >= 30:
                raise HTTPException(507, 'The community DEM collection is full.')
            folder = REGIONS / ident
            folder.mkdir(parents=True, exist_ok=False)
            try:
                shutil.copy2(temp, folder / 'DEM.tif')
                _preview(elev, folder / 'Mapa_2D.png')
                metadata = {
                    'title': title, 'body': body, 'source': 'Community submission',
                    'original_format': 'single-band GeoTIFF',
                    'vertical_unit_assumption': 'meters (uploader declaration; unverified)',
                    'extent_m': [5000, 5000],
                    'verification': 'format and extent checked; scientific validity not established',
                    'submitted_utc': datetime.now(timezone.utc).isoformat(),
                }
                (folder/'metadatos.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
                item = {
                    'id':ident,'title':title,'body':body,'source':'Community DEM',
                    'lat':lat,'lon':lon,'area_km2':25,'status':'disponible',
                    'user_uploaded':True,'assets':{name:f'data/regions/{ident}/{name}' for name in ('DEM.tif','Mapa_2D.png','metadatos.json')},
                    'metrics':features['metrics'],'profile':features['profile'],'histogram':features['histogram'],
                    'elevation_min_m':round(features['min'],3),'elevation_max_m':round(features['max'],3),
                    'native_resolution_m':round(spacing[0],3),
                    'coverage_pct':round(features['coverage'],2),'size_px':features['size'],
                    'pixel_m':features['pixel_m'],'crs':features['crs'],
                    'verdict':'COMMUNITY_UNREVIEWED',
                    'provenance':'Visitor-submitted data; geometric validation only',
                    'warning':'Unverified public submission. Reported pixel size is not proof of native sensor resolution. No geological equivalence or rover safety is established.'
                }
                catalog['items'].append(item)
                _save_catalog(catalog)
            except Exception:
                shutil.rmtree(folder, ignore_errors=True)
                raise
        return {'id': ident, 'status': 'published', 'notice':'Community data added to the public catalog. Scientific accuracy not independently verified.'}
