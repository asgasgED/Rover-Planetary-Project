# Current state and roadmap

**Documentation baseline:** public-facing v4.2 code snapshot and team-reported geospatial work as of 15 November 2026. These are development-status notes, not certification of a publicly deployed service.

## Component status matrix

| Component | Status | Evidence | Next step |
|---|---|---|---|
| Frontend route and public-facing UI | Implemented; code-tested | `src/app.js`, CSS and page tests | Real-browser accessibility/responsive regression |
| Earth/Mars/Moon catalog of 33 names | Implemented | `data/catalog.json` | Cross-check each site's metadata and source availability |
| Five example region bundles | Bundled in inspected archive | `data/regions/` | Replace with canonical team outputs when appropriate |
| Historical 19-region DEM audit | Team report available | Prior audit and catalogue status | Reconcile actual final files and metadata |
| Eight extra Mars MOLA regions | CLI success **reported** by team | Terminal output with 8/8, 5 km, 100% valid cells | Confirm all files imported and scientifically contextualized |
| Six additional lunar regions | Planned/catalogued; local final processing **not independently verified here** | Region IDs and source relationships | Inspect final files and validate 5 km bounds |
| Seven DEM-derived metrics | Implemented; unit-tested at code level | Catalog/preprocessing and live scientific engine | Common-scale analysis and independent checks |
| Cosine-based analog discovery | Implemented; exploratory | `src/analysis.js`, `src/app.js` | Calibrate and validate with independent labels |
| API numerical comparisons / charts | Implemented; tested on examples | `backend/api.py`, `analysis_engine.py`, tests | Performance/error budgets for public service |
| Community GeoTIFF publication | Implemented experimentally | `backend/community.py`, tests | Authentication, durable quotas, moderation, storage isolation |
| Chemistry panel | Implemented for selected entries; bibliography pending review | `data/chemistry.json` | Validate and cite each sample, do not extrapolate |
| External AMD AI integration | **Not part of public v4.2** | Public routes do not expose AI | Future work only if scientifically justified and safely deployed |
| Rover simulator | **Not connected** | Empty integration directories and placeholder page | Integrate actual converter/simulator outputs and test |
| Production deployment | **Not verified** | Local testing only in available record | Host, security audit, uptime and mobile QA |

## Immediate priorities

1. Finish file-level source reconciliation for the full local 33-region set; audit that each `DEM.tif` is numeric, complete and correctly referenced.
2. Improve permanent text contrast, keyboard focus, responsive layout, external link quality and accessibility in real browsers.
3. Disable or moderate unrestricted uploads for any public production deployment.
4. Establish ownership/licensing and third-party image/logo rights.
5. Preserve a reproducible research manifest per region and algorithm version.

## Medium-term scientific priorities

- Implement common-scale morphometric comparisons and normalized/controlled feature weighting.
- Add documented uncertainty and site inclusion/exclusion criteria.
- Verify sample chemistry bibliography and location specificity.
- Integrate higher-resolution planetary DTMs for sites where rover-scale morphology is central.
- Validate measured candidates against external geology and field evidence.

## Later platform priorities

- Replace local mutable JSON plus process-local rate limits with managed database and object storage.
- Add durable user/moderator workflows for submitted DEMs.
- Connect validated rover physics simulation with versioned run manifests and telemetric output.
- Add public deployment automation, reproducibility containers and a monitored CI pipeline.

## Version naming

The currently inspected `package.json` and public FastAPI report `4.2.0`. Previous documentation and team code refer to v3/v4 AMD prototypes; do not mistake those archived experiments for an active public AI feature.
