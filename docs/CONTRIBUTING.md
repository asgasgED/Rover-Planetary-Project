# Contributing to TerraRover

Thank you for helping improve reproducible planetary terrain exploration. Contributions should be understandable to researchers and safe to merge into the application without changing published scientific outputs unexpectedly.

## Before opening a change

1. Read [Architecture](ARCHITECTURE.md), [Scientific methods](SCIENTIFIC_METHODS.md) and [Data formats](DATA_FORMATS.md).
2. Identify whether your work changes the UI, scientific analysis, data publication or future simulation contract.
3. Open an issue/discussion for scientific method changes that affect metrics, scale or result interpretation. This document describes a proposed collaboration workflow; maintainers may use a different repository process.
4. Never include private keys, `.env`, `.venv`, unapproved source archives, unrelated personal data, or copyrighted third-party assets without permission.

## Branch and pull request guidance

A practical naming convention is `feat/<scope>`, `fix/<scope>`, or `docs/<scope>`. Include a description of the problem, main implementation, manual test results, and any changes to data or science statements. Prefer small, focused pull requests and avoid large unrelated code refactors.

## Scientific changes require stronger review

If you add or revise a metric, document:

- The exact mathematical formula and definition of units.
- NoData handling and boundary conventions.
- Native vs final raster resolution and the physical size of any smoothing/analysis window.
- Whether the metric is an established published index or a project-specific proxy.
- Expected behavior on synthetic planar, sloped and rough surfaces.
- Stability against sources with different resolutions and geospatial reference systems.
- Consequences for comparison scores and public language.

Do not transform an uncalibrated score into a confidence percentage merely because it makes the UI look cleaner.

## UI changes

Check keyboard and touch behavior, responsive layout, contrast *before hover*, document links, data-provenance labels and missing-data states. Avoid adding buttons that point to internal debug actions or advertise an unimplemented feature to a public visitor.

## Data changes

Record the original institution, archive, filename, checksum if available, acquisition/product version, crop center and georeferencing; do not overwrite or silently smooth the upstream GeoTIFF. Keep community uploads clearly separate from curated region deliveries.

## Run available checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
node tests/test_frontend.mjs
node tests/test_pages.mjs
node tests/test_live_frontend.mjs
```

Add tests for new public API contracts and meaningful error cases. The repository currently contains some historical AMD-oriented tests; maintainers should reconcile these with the public v4.2 routes.

## Code of conduct and governance

This documentation does not assert an existing formal CODE_OF_CONDUCT, ownership policy, contributor license agreement or license. Establish these with the actual team before inviting outside code contributions and redistributing third-party assets.
