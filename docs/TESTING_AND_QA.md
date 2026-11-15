# Testing, quality assurance and reproducibility

## Automated tests available in source snapshot

| Test file | Purpose |
|---|---|
| `tests/test_backend.py` | Numeric analysis, API inputs, MOLA limits, chart and static privacy checks |
| `tests/test_catalogo.py` | Synthetic DEM profile checks, CRS rejection, catalog contract and Plotly reference |
| `tests/test_public.py` | Public route behavior, community uploads, auto-import and invalid input rejection |
| `tests/test_frontend.mjs` | Core browser-side JS data/route checks |
| `tests/test_pages.mjs` | Multi-page route markup |
| `tests/test_live_frontend.mjs` | Numerical API integration behavior on the frontend |
| `tests/test_v41_ui.mjs` | Legacy v4.1 UI regression tests |
| `tests/test_v4_ai.py` | **Historical** AI fallback/test coverage; inspect for relevance before running against public v4.2 |

**Commands from project root:**

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
node tests/test_frontend.mjs
node tests/test_pages.mjs
node tests/test_live_frontend.mjs
node tests/test_v41_ui.mjs
```

`npm test` is defined by `package.json` and invokes both Node and Python tests. Some older files test pre-public AMD behavior and may require maintenance when refactoring; do not claim the current production build has a live AI integration.

## Manual release checklist

### Catalog and 3D

- [ ] Check all 33 region identifiers, each source label and each status.
- [ ] Confirm only physically present region products say available.
- [ ] Validate `DEM.tif` CRS, mask and 5,000 m × 5,000 m bounds.
- [ ] Open 2D previews and check their labels do not imply imagery if they show pseudocolor height.
- [ ] Open 3D viewers and confirm shared `data/regions/plotly.min.js` is accessible.
- [ ] Verify source/geographic metadata and map marker coordinate conventions.

### Computation

- [ ] Test a relatively comparable Earth–Moon pair and a coarse MOLA reference.
- [ ] Check that MOLA comparisons explicitly warn about resolution and are labelled regional only.
- [ ] Verify no pixelwise height subtraction occurs between non-colocated sites or different bodies.
- [ ] Test missing/constant/noisy/NoData rasters and error messages.
- [ ] Compare catalog-precomputed features against live backend features for expected differences.

### Public UI

- [ ] All navigation works on desktop and narrow mobile viewport.
- [ ] Focus, hover and default states remain legible in both keyboard and touch use.
- [ ] All buttons have working actions and accessible labels.
- [ ] Image alt text, chart labels/units and contrast meet accessibility goals.
- [ ] The simulation page does not imply data or physics runs that were never executed.
- [ ] Nothing advertises AMD service setup or internal debugging to visitors.

### Security

- [ ] `/.env` and `/.venv` cannot be fetched.
- [ ] Community uploads are disabled or appropriately protected on public deployment.
- [ ] An uploaded DEM cannot overwrite a team region or arbitrary server path.
- [ ] API latency/memory and maximum request sizes behave under load.
- [ ] Third-party data redistribution and attribution have been reviewed.

## Reproducibility notes

Capture dependency versions (`pip freeze`), SHA-256 of all canonical DEM files, generation script versions, dataset timestamps, validation output and any non-default algorithm parameters for a formal research submission. The examined repository does not include a fully pinned environment lock or a scientific benchmark dataset of labeled analogue sites.
