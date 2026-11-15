# Find Analog Sites — candidate discovery

## Visitor flow

1. Select a **published** Mars or Moon reference with available metric data.
2. The page obtains published Earth candidates with their seven precomputed descriptors.
3. TerraRover calculates a cosine score between each Earth candidate's vector and the reference vector.
4. It sorts available candidates in descending score order and currently displays up to **eight** records.
5. Select a candidate to inspect its source data or open the live Python pairwise comparison.

## What ranking means

The seven descriptors are compared **without a fitted feature weighting or scientific calibration**. Scores are not probabilities, not percentages, not independent evidence for the environmental/geochemical similarity of two sites. The ranking is a **triage list to prioritize further measurements**.

A Mars MOLA reference may be only 11 × 11 cells inside the 5 km window, while an Earth raster can contain ~162 × 162 cells. The same 3-cell and 15-cell filters operate over different real-world distances; the ranking **cannot reliably assess fine morphology or rover-sized obstacles**.

## Computation and sources

The browser function `src/analysis.js::cosine` uses precomputed numeric metrics in `data/catalog.json`. The chart and detailed live analysis use `backend/analysis_engine.py` through `/api/analyze` and `/api/chart`. These are related but not identical processing paths: the backend has additional masked-data logic and quality notes. Numerical differences between cached and live metrics should be investigated rather than silently ignored.

## What would make the ranking scientifically stronger

- A common spatial scale and justified resampling strategy.
- Explicit source error, uncertainty and NoData sensitivity.
- Feature normalization, weighting, ablation and rank stability.
- Grounded analogue labels and independent validation sites.
- Geochemical, sedimentological and mineralogical context acquired separately.
- A calibrated decision rule with documented out-of-distribution behavior.

## New public data

If community uploads are enabled, submissions are labelled `Community DEM` / `COMMUNITY_UNREVIEWED` and require their own provenance review. Such files should not be treated as verified ground truth or as equivalent to curated Killa Coders regions.
