# Scientific analysis and interpretation

This document describes the **implemented** numeric comparison in `backend/analysis_engine.py` and the initial catalog feature extraction in `scripts/preparar_catalogo.py`. It is a reproducible early-stage method, **not yet a calibrated analogue detection model**.

## Inputs and quality checks

- Read **one** numeric raster band from `DEM.tif` with Rasterio. Reject color TIFFs and unsupported raster geometries.
- Require a valid CRS and a 5,000 × 5,000 m physical window (allowing minor finite-precision tolerance in the backend).
- Identify valid cells by numeric finiteness and the GeoTIFF's declared NoData value.
- Record native resolution separately from final grid spacing. Missing cells are handled by a documented local weighted mean for metric computation; valid-area coverage is reported separately.
- Report limitations when terrain detail or native resolution differs across the comparison pair.

## Seven terrain descriptors

| Key in code | Meaning | Interpretation hazard |
|---|---|---|
| `integral_hipsometrica` | Mean normalized relative elevation `(z-min)/(max-min)` | Does not identify geology on its own |
| `pendiente_media_deg` | Mean local DEM-derived slope in degrees | A coarse DEM misses steep short-wavelength obstacles |
| `pendiente_std_deg` | Variation of local slope | Resolution affects measured variation |
| `asimetria_elevacion` | Skewness of valid elevation samples | Sensitive to extent and outliers |
| `razon_area_3d2d` | Mean `sqrt(1+(dz/dx)^2+(dz/dy)^2)` | Grid geometry vs physical surface approximation |
| `tri_normalizado` | Mean absolute deviation from a local **3-cell mean**, divided by total relief | **Not** the canonical TRI definition; window is measured in cells, not meters |
| `tpi_std_normalizado` | Standard deviation of elevation-minus-**15-cell** neighborhood mean, divided by relief | The window spans very different ground lengths by source |

The title **TRI\*** or **local roughness proxy** is more accurate than claiming a standardized TRI without qualification. The 15-cell TPI neighborhood may exceed most of an 11 × 11 MOLA crop; avoid fine-scale interpretations.

## Initial cosine score

For the vector `v` of seven raw descriptors, the implementation calculates:

\[
\operatorname{cosine}(A,B) = \frac{v_A \cdot v_B}{\lVert v_A \rVert\,\lVert v_B \rVert}
\]

No independently trained weights or statistical feature standardization are applied. The result is a **dimensionless alignment index**, commonly `-1` to `+1`, **not** a probability or percentage of geological equivalence. A high score can reflect scale dominance by one descriptor. Site rankings based on this number are **hypothesis-generating only**.

## Additional numeric comparisons

- **Wasserstein distance** of per-crop relative elevation distributions (0–1 normalized height).
- **Kolmogorov–Smirnov statistic** for the same normalized distributions.
- **Metric-by-metric delta**, including a relative signed change.
- **Raw and median-offset-adjusted RMSE** only if two rasters share the **same planetary body, CRS, shape and geospatial transform**. Otherwise this calculation is intentionally omitted.

The system does **not** subtract pixel elevations between arbitrary Earth and Mars crops. Absolute height reference surfaces are different; only *relative, exploratory* distribution/shape comparisons are appropriate here.

## Quality interpretation tiers

`fine_scale_comparison_permitted` is a **software quality gate**, not an independent scientific validation. In the inspected backend it requires the maximum native resolution to be ≤100 m and the ratio of the two native resolutions to be ≤1.5. Pairs not meeting the criteria can still have a regional/exploratory cosine, but the UI and backend warn that fine-scale equivalence is unsupported.

## Example of an appropriate conclusion

> “The two selected 5 km windows exhibit similar normalized elevation-distribution shapes. The planetary reference has substantially coarser ground sampling, so the apparent similarity does not establish comparable local roughness, regolith properties, or rover-scale hazard.”

**Do not write:** “These two sites are 93% geologically identical,” “Mars is safe for a rover,” or “this tile contains chemically verified evaporites” based only on a DEM score.

## Next scientific validation steps

1. Make window sizes **fixed in meters**, not cell counts; compare only at a defensible common physical scale.
2. Normalize or learn feature weights on a separately curated reference set; assess baselines.
3. Evaluate sensitivity to source resolution, NoData, vertical errors and source correlations.
4. Compare against independent field/geological evidence, remote-sensing products and higher-resolution DTMs where available.
5. Document study sites, date of acquisition, vertical reference and uncertainty before ranking scientifically.

## Related modules

- `scripts/preparar_catalogo.py::compute_features` precomputes the catalog descriptors.
- `backend/analysis_engine.py::read_dem`, `features`, `numerical_report` compute live pairwise results.
- `backend/plotting.py` produces visualization PNGs.
- `src/analysis.js` implements the initial browser cosine from catalog-precomputed metrics.
- `src/live_analysis.js` renders API results and warnings.
