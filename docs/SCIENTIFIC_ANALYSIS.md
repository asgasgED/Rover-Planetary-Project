# TerraRover v3 — Scientific analysis and interpretation contract

This document describes the integrated **numerical DEM** analyzer (`backend/analysis_engine.py`) and the difference from the original team scripts preserved in `backend/team_originals/`.

## Original modules and changes

| Original script | Actual team function | How integrated and why |
|---|---|---|
| `analisis_morfologico.py` | Extracts 7 features and computes cosine from two hard-coded TIFF files | Seven features and the uncalibrated cosine are retained, but use dynamic numeric `DEM.tif` inputs and valid-cell masking instead of hardcoded `Mapa_2D.tiff` image bands. |
| `analisis_diferencias.py` | Matrix-based difference after `scipy.ndimage.zoom`, with warning about lack of CRS alignment | Its raw difference is **not valid across separate regions or planets**. The backend only provides pixelwise RMSE if CRSs and full affine grids agree and both rasters are of the same planetary body. |
| `graficos_terrarover.py` | Generates static spatial/morphology plots and optionally sends figures to AMD TokenLab | Its visualization responsibility is implemented as a per-pair dynamic `/api/chart` endpoint and numeric-first AI interpretation through `/api/interpret`. The original is archived unchanged. |

## The seven original features

Let \(z_{ij}\) denote a real numeric elevation in metres and \(\Delta x,\Delta y\) the pixel spacing in metres. Only finite non-NoData pixels are used in summary calculations.

1. **Hypsometric integral**: mean of \((z-z_{min})/(z_{max}-z_{min})\).
2. **Mean slope**: mean of \(\arctan\sqrt{(\partial z/\partial x)^2+(\partial z/\partial y)^2}\) in degrees.
3. **Slope spread**: standard deviation of those slope angles in degrees.
4. **Elevation skewness**: skew of the distribution of valid elevations.
5. **3D/2D area ratio**: mean of \(\sqrt{1+z_x^2+z_y^2}\) over valid pixels.
6. **TRI*** proxy: mean absolute difference from a 3×3 neighborhood average, divided by total relief.
7. **TPI window variation**: std. dev. of elevation minus the 15×15 neighborhood average, divided by total relief.

The supplied 3×3 and 15×15 formulas are **proxies**. TRI* is not automatically the standardized terrain ruggedness index found in every literature definition; the 15-cell TPI is not a fixed-metre multiscale comparison. The backend handles missing cells by masking and neighbor-aware means, not by assigning an arbitrary `0 m` elevation. Some feature values therefore differ from the original team's fixed-file version in cases with missing data.

## Comparison outputs

- `legacy_cosine`: cosine of the seven unstandardized metrics. **Not a validated probability or percentage of geological analog quality.**
- `feature_comparison`: seven A/B feature values, numerical deltas and a bounded contrast indicator.
- `normalized_elevation_wasserstein`: Wasserstein distance between each DEM's min–max-normalized elevation distribution. This measures distributional resemblance in [0,1] coordinates, **not** geospatial alignment.
- `normalized_elevation_KS_statistic`: a distance between normalized empirical elevation distributions.
- `pixelwise_difference`: populated only for the same planetary body with identical 2D affine grids and CRS, using valid overlapping cells. It reports raw RMSE and shape RMSE after removing the median height offset. Null for all cross-planet cases and for non-co-located terrestrial sites.
- `interpretive_notes` and `warnings`: physical implications, possible confounders, resolution mismatch and the limits of the source.
- `fine_scale_comparison_permitted`: an **exploratory data-quality gate**, true only if both native resolutions are ≤100 m and differ by ≤1.5×. This is not a scientific certification of fine-scale equivalence or rover safety.

## AMD AI interpretation

Only a private backend process sends the two DEM visualization panels and the **real calculated numerical report** to TokenLab. Prompt requirements:

1. Scientific judgment and limits of the available evidence.
2. Evidence-based similarities citing particular numeric features.
3. Significant dissimilarities and their geophysical meaning.
4. Clearly labelled hypotheses about terrain processes and suggested falsification tests.
5. Resolution effects, alternative explanations and what cannot be inferred from a DEM.
6. Concrete next actions for data processing, algorithm development and verification.

The model cannot validate geology or prove composition or rover traversability from the figures. An AI reply is a hypothesis-generating text output, **not** a deterministic metric or scientific ground truth. The numerical analysis works even when TokenLab is disabled.

## Security and evidence

The backend serves the web frontend only from `src/`, `assets/`, `data/` plus `index.html`. The `backend/`, `.env`, and `datos_para_importar/` paths are blocked by design. API ID inputs are selected by a strict whitelist of catalog names and a filename pattern. Do not expose the development server on a public IP without authentication, rate limiting, request limits and secret management.

The offline test suite verifies input/output with actual imported sample DEMs and mocks the AI provider. Calls to the actual AMD endpoint are not verified by these tests.
