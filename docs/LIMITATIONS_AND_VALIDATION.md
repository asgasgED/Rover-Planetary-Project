# Limitations, uncertainty and validation boundaries

## Verified technical constraints

| Constraint | Evidence | Consequence |
|---|---|---|
| Original DEMs have different native ground spacing | Earth ~30 m, SLDEM ~59 m, MOLA ~463 m | Local slope/roughness comparisons are scale-dependent |
| Team-derived windows share 5 km width and height | Raster audit and imported GeoTIFF dimensions | Equal area does **not** imply equal physical detail |
| The 7-feature cosine is uncalibrated | Source implementation | No geological similarity percentage/probability |
| TRI* is not standardized TRI | Implemented 3-cell mean-deviation proxy | Must be described as a local proxy |
| 15-cell TPI on 11-cell MOLA raster | Source implementation/window size | Nearly whole-tile context; no independent local-feature interpretation |
| Different planetary vertical reference frames | Earth/Mars/Moon DEM metadata | Absolute elevation values are not directly comparable |
| Composition is sample-specific | `data/chemistry.json` and external studies | No raster-wide material inference |
| No Webots/Gazebo runtime connected to UI | Public v4.2 codebase | No scientific rover traversability outcome exists in the web app |

## Known data-quality issue from earlier deliverables

The final Timanfaya ASTER GeoTIFF was inspected with 162 × 162 valid numeric samples covering 5,000 × 5,000 m. **1,396 zero-valued pixels (~5.32%)** formed a connected region touching the northern and western boundaries, consistent with a possible coastal/water mask. This was not independently verified against a dedicated water product. Its `metadatos.json` contained stale values from an earlier grid (e.g., reported 30 m rather than measured 30.8641975 m pixel spacing, older valid-pixel count and extrema). A new contributor should derive geometry/valid coverage from `DEM.tif` and reconcile stale metadata before presenting precise quantities as final.

Other raster warnings (e.g., candidate outliers near Askja, Haughton and Timanfaya) require separate geospatial inspection before any smoothing. Statistical outliers may represent real geomorphology; do not delete automatically.

## Validation levels

1. **Format/geometry check:** file is a numeric single-band GeoTIFF, with declared CRS, valid cells and 5 km bounds.
2. **Computational check:** metric calculations are finite and repeatable on known synthetic rasters; API/chart outputs are structurally correct.
3. **Cross-source check:** compare terrain shape with an alternative DEM source, acknowledging non-independence.
4. **Geographical/site check:** verify center, map coordinate conventions, datum, land/water masks and study-region identity.
5. **Scientific analogue validation:** compare against independent geological field labels and mission data, evaluate uncertainty, confirm feature scaling and report errors.
6. **Rover validation:** test a specified rover/simulator configuration on sufficiently resolved terrain and external reference experiments.

The public prototype supports mainly levels 1–2 and some preliminary cross-source checks; levels 4–6 must not be claimed complete solely because a webpage renders without errors.

## Explicit non-goals for the present release

- Hazard detection at rock/wheel scales from MOLA and ~30 m Earth DEMs.
- Automated inference of mineral abundance, subsurface ice or dust traction from height alone.
- Geological equivalence classification with measured ground-truth sensitivity/specificity.
- Autonomous remote rover execution or real simulation results.

## Improvement protocol

Document reference datasets, coordinate/datum reconciliation, resampling strategy, perturbation tests, feature normalization, uncertainty bands, withheld validation sites and external expert/field evidence before publishing a research claim or an official rank.
