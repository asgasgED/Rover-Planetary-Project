# Geochemical context and responsible presentation

TerraRover includes a small `data/chemistry.json` dataset for displaying **sample-specific or study-specific** composition context inside selected terrain detail views. The values are **not extracted from `DEM.tif`**, and their availability does not mean the full 5 km region has a uniform composition.

## Examples in the inspected source

| Catalog ID | Study/site context in application | Data type | Qualification |
|---|---|---|---|
| `Mare_Tranquillitatis_SLDEM` | Apollo 11 sample 10084 | Oxide/element fractions supplied by team | Bibliographic source-to-value verification pending |
| `Gale_Crater_MOLA` | Curiosity Rocknest windblown soil | Mineral phases identified by XRD and reported amorphous content | Specific sample and instrument, not an entire Gale tile |
| `Meridiani_Planum_MOLA` | Opportunity soils/dust/rocks | Phases such as hematite, jarosite, sulfates | Evidence spans different materials; not one uniform sample |
| `Askja_ASTER` | Studied volcanic rock groups | Ranges for major oxides | Basalt sample ranges are not DEM-derived maps |
| `Yungay_NASADEM` | Hyperarid Atacama soil samples | Sample-reported mineral content | Depends on local site and study methodology |

No chemical values should be invented for other catalog sites. The historic team notes contain values accidentally converted into calendar dates in some tables; these are not credible concentration measurements and should **not** be imported as numbers without checking the original paper or source spreadsheet.

## Presentation requirements

- Always show sample/study identifier, instrument, measurement units and source citation when verified.
- Distinguish minerals detected qualitatively from quantities measured as wt. %, vol. % or ppm.
- Describe uncertainty or a reported interval; do not silently average incompatible samples.
- When a link or original publication has not been checked, label the values as **bibliographic review pending** rather than calling them authoritative measurements for the map.
- Never calculate traversability from geochemical labels alone.

## Future controlled data schema (proposal, not implemented)

A sound record would carry `site_id`, `sample_id`, `coordinate_reference`, `sampling_date`, `measurement_type`, `instrument`, `analyte_or_phase`, `value`, `unit`, `uncertainty`, `source_doi`, `quality_status` and geographic representativeness. A future ETL/validation step should verify citations and distinguish sample-point data from raster-wide covariates before merging with terrain analyses.
