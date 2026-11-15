# Development history and documentation baseline

The dates below are based on the Killa Coders project work and releases available in this conversation. They are **not** derived from a formal Git tag history and should not replace your repository's authoritative release commits.

## Upstream geospatial module (November 2026)

- Prepared initial Earth, Mars and Moon 5 × 5 km DEM deliveries; reported an audit of 19 regions (17 Earth + Jezero + Mare Tranquillitatis).
- Expanded lunar study list to seven regions sharing six unique original lunar raster products, including a dedicated polar LOLA source for Shackleton.
- Added eight Mars MOLA study windows; the team reported 8/8 successful 11 × 11-cell, 5 km processing in terminal output.
- Documented scientific scope, source-tile sharing and the limitations of coarser planetary data.

## TerraRover v1–v2 (development prototypes)

- Established the research web application, catalog, map, 2D/3D product display and initial cosine comparator.
- Developed cinematic and later light-theme visual design, responsive navigation and chemistry-context panels.

## TerraRover v3–v4.1 (prototype iterations)

- Added Python numeric comparison, dynamic graphs and AMD TokenLab experiments.
- Improved NoData and spatial-alignment handling, scientific interpretation warnings, light-theme contrast and catalog appearance.
- These iterations included internal AMD diagnostics that do **not** belong in the public v4.2 API.

## TerraRover v4.2 — public research interface

- Simplified visitor-facing navigation and removed publicly exposed AMD routes/testing controls.
- Kept real numeric DEM comparison and chart generation on the Python backend.
- Added **Find Analog Sites** (uncalibrated seven-feature candidate ranking).
- Added optional visitor **single-band GeoTIFF** publishing, labelled community/unreviewed and subject to validation/consent.
- Added automatic import of new complete team deliverable folders on server startup.
- Added **Rover Simulation** placeholder directories and a public “integration coming” page, with no fictional execution results.

## Next release should address

- Audited public deployment hardening and rights-cleared imagery.
- Full canonical 33-region import verification in the deployed environment.
- Scientifically robust comparable-scale feature scoring and uncertainty evaluation.
- Real rover integration only after simulated-world and telemetry validation.
