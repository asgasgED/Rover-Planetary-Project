# Repository and module reference

The paths below were inspected in the public-facing v4.2 source snapshot. Only the `README.md` and `docs/` directory are delivered in the documentation ZIP; the files described here belong to the main application repository.

```text
TerraRover_Plataforma/
├── index.html
├── package.json
├── requirements-backend.txt
├── .env.example                       # Historical optional AMD template; not required by public v4.2
├── .gitignore
├── assets/
│   ├── brand/                          # Logo assets, rights to verify
│   └── space/                          # Illustrative planet imagery
├── src/
│   ├── app.js                          # UI routes, events, catalog and discovery
│   ├── ui.js                           # Labels/icons/formatting/HTML utilities
│   ├── analysis.js                     # Browser cosine + scale messaging
│   ├── live_analysis.js                # /api/analyze client + result rendering
│   ├── public.css                      # Public-facing UI refinements
│   ├── v4_light.css                    # Light interface overrides
│   ├── v3_palette.css                  # Shared palette
│   ├── cinematic.css                   # Hero/interaction styling
│   └── styles.css                      # Base styles
├── backend/
│   ├── api.py                          # FastAPI routes, static mounts, startup
│   ├── analysis_engine.py              # Numeric DEM analysis
│   ├── plotting.py                     # Generated PNG charts
│   ├── community.py                    # User-upload and team auto-import
│   ├── team_originals/                 # Historical team analyzer scripts
│   └── simulation/                     # Future backend simulation integration
├── scripts/preparar_catalogo.py       # Admin catalog build/import
├── data/
│   ├── catalog.json                    # Public region catalog
│   ├── chemistry.json                  # Contextual sample-specific chemistry
│   └── regions/
│       ├── <REGION_ID>/                # Published team deliverables
│       ├── Community_<random>/         # Public unreviewed user uploads (if enabled)
│       └── plotly.min.js               # Shared 3D viewer dependency
├── datos_para_importar/entrega_5km/   # Local, original six-file deliveries
├── simulation/                         # Future rover integration code/assets
├── tests/                              # Python + Node verification
├── docs/                               # Technical and user documentation
└── README.md
```

## Startup sequence

1. Uvicorn starts `backend.api:app`.
2. The FastAPI lifespan handler invokes `backend.community.import_new_team_deliverables()`.
3. The importer scans `datos_para_importar/entrega_5km/` and copies eligible new regions into `data/regions/`, updating `data/catalog.json`.
4. The browser loads `index.html` and `src/app.js`, fetches `./data/catalog.json` and renders its navigation and selected page.
5. On comparison, the browser requests `POST /api/analyze` and, where appropriate, `/api/chart`. The server resolves region IDs against the catalog rather than accepting arbitrary file paths.

## Code ownership boundaries

| Modify if working on… | Primary files | Preserve |
|---|---|---|
| UI layout/design | `src/app.js`, `src/ui.js`, CSS | Public scientific warnings, accessible contrast, functioning links |
| New analysis metric | `backend/analysis_engine.py`, `scripts/preparar_catalogo.py`, `src/analysis.js` if ranking changes | Metric naming, scaling, scientific interpretations, tests |
| Catalog ingest | `scripts/preparar_catalogo.py`, `backend/community.py` | Original inputs, status semantics, public asset paths, existing entries |
| Public submissions | `backend/community.py` | Validation, consent, rate controls and provenance; prevent team overwrites |
| Simulator integration | `simulation/`, `backend/simulation/`, UI simulation route | Do not present mock telemetry as completed experiments |

## Included reference samples versus user working data

The inspected code archive includes five complete example DEM bundles and has 33 named catalog entries. The user's local installation may have all 33 imported. Developers must avoid replacing a populated `data/` directory with the documentation/archive examples. A **code-only patch** should not delete `data/catalog.json`, `data/regions/` or user `.env` and `.venv`.
