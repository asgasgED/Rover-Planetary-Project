# TerraRover 3.0 — Integration changes

- Restyled the existing TerraRover v2 UI in English, with the requested black/white/gray/royal-blue/red/orange palette and without aqua/cyan visuals.
- Added a local FastAPI application to serve the frontend, five sample DEM packages, scientific calculations and an optional AI interpretation endpoint.
- Integrated the seven feature formulas from the team's supplied `analisis_morfologico.py` through dynamic numerical `DEM.tif` inputs with NoData-safe handling. The original three scripts are stored under `backend/team_originals/` for reference.
- Added `backend/analysis_engine.py`: uncalibrated cosine index, feature-by-feature differences, normalized elevation Wasserstein/KS, scale/resolution gating and alternative physical explanations.
- Added `backend/plotting.py`: dynamic 2×2 scientific plots comparing actual rasters and their distributions; no cross-planet pixel-difference fiction.
- Added `backend/api.py`: `/api/health`, `/api/analyze`, `/api/chart`, `/api/interpret`, restricted static serving and private AMD configuration.
- Added `.env.example`, `requirements-backend.txt`, a Windows PowerShell setup and a scientific interpretation contract.
- Extended tests to verify numeric analyses on real DEMs, PNG generation, API paths, secret path blocking, invalid inputs, disabled AI, mocked TokenLab requests and frontend UI actions.
- Kept chemistry strictly as contextual samples within terrain details; preserved catalogue and the 33 import folders; rover simulation remains deferred.

## Known unverified areas

- Live AMD TokenLab completion requires a valid user credential, an available API endpoint and internet access; no live charged requests were made.
- No real outputs from the improved future comparison algorithm were supplied. Current indicators are exploratory and not scientifically calibrated.
- 33 full regional DEM source bundles were not supplied; five complete real demonstration bundles remain bundled, and the import tool supports more.
- Automated DOM and endpoint tests passed; a complete interactive visual browser regression run was not performed in this environment.
