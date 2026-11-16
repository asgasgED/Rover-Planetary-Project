"""TerraRover public API: scientific DEM comparisons and controlled community uploads.

No third-party AI credentials or simulation execution are required.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from io import BytesIO
import json
from pathlib import Path
import re

import matplotlib
matplotlib.use('Agg')

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .analysis_engine import read_dem, numerical_report
from .community import import_new_team_deliverables, submit_community_dem

# NUEVO: router de simulación
from .simulation.routes import router as simulation_router

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data' / 'regions'
CATALOG = ROOT / 'data' / 'catalog.json'
SAFE_ID = re.compile(r'^[A-Za-z0-9_-]{2,100}$')

@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        import_new_team_deliverables()
    except Exception as exc:
        print(f'[TerraRover] Auto-import warning: {type(exc).__name__}: {exc}')
    yield

app = FastAPI(
    title='TerraRover Terrain Research API',
    version='4.2.0',
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan
)

app.include_router(simulation_router)

class PairRequest(BaseModel):
    a: str = Field(min_length=2, max_length=100)
    b: str = Field(min_length=2, max_length=100)


def get_pair(req):
    if not SAFE_ID.fullmatch(req.a) or not SAFE_ID.fullmatch(req.b) or req.a == req.b:
        raise HTTPException(400, 'Select two different valid terrain identifiers.')
    try:
        catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    except Exception:
        raise HTTPException(503, 'The terrain catalog is temporarily unavailable.')
    ids = {x['id']: x for x in catalog.get('items', [])}
    if req.a not in ids or req.b not in ids:
        raise HTTPException(404, 'Unknown terrain identifier.')
    if ids[req.a].get('status') != 'disponible' or ids[req.b].get('status') != 'disponible':
        raise HTTPException(409, 'Both regions need published numeric elevation models.')
    paths = [DATA / v / 'DEM.tif' for v in (req.a, req.b)]
    if not all(path.is_file() for path in paths):
        raise HTTPException(409, 'Numeric terrain data for this comparison is not available.')
    return ids[req.a], ids[req.b], paths


def compute(req):
    a, b, paths = get_pair(req)
    try:
        da, db = read_dem(paths[0]), read_dem(paths[1])
        result = numerical_report(da, db, a['title'], b['title'], a['body'], b['body'],
                                 a.get('native_resolution_m'), b.get('native_resolution_m'))
    except (OSError, ValueError) as exc:
        raise HTTPException(422, str(exc))
    result['regions']['a_id'] = a['id']
    result['regions']['b_id'] = b['id']
    return result, da, db

@app.get('/api/health')
def health():
    return {'service': 'terrarover-terrain-science', 'status': 'ok'}

@app.post('/api/analyze')
def analyze(req: PairRequest):
    result, _, _ = compute(req)
    return result

@app.get('/api/chart')
def chart(a: str = Query(min_length=2, max_length=100),
          b: str = Query(min_length=2, max_length=100)):
    from .plotting import comparison_png
    report, da, db = compute(PairRequest(a=a, b=b))
    return Response(content=comparison_png(da, db, report), media_type='image/png',
                    headers={'Cache-Control': 'no-store'})

@app.post('/api/community-upload', status_code=201)
def community_upload(request: Request, file: UploadFile = File(...),
                     title: str = Form(...), body: str = Form(...),
                     public_consent: str = Form(...)):
    result = submit_community_dem(request, file, title, body, public_consent)
    return result

@app.exception_handler(HTTPException)
async def http_error_handler(_request, exc):
    return JSONResponse(status_code=exc.status_code, content={'detail': exc.detail})

@app.get('/')
@app.get('/index.html')
def home():
    return FileResponse(ROOT / 'index.html')

# Explicit static mounts only. Never expose .env, .venv, source imports or backend.
app.mount('/assets', StaticFiles(directory=ROOT / 'assets'), name='assets')
app.mount('/src', StaticFiles(directory=ROOT / 'src'), name='frontend')
app.mount('/data', StaticFiles(directory=ROOT / 'data'), name='datasets')
