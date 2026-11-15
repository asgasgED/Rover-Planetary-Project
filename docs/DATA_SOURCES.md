# Official geospatial data sources and provenance

This document distinguishes **original mission/DEM products** from the **derived, cropped 5 × 5 km outputs** used in TerraRover. Links below point to authoritative dataset descriptions, institutional archives or official distribution directories, rather than to arbitrary third-party copies. Product permissions and attribution should be reviewed for each redistribution.

## Earth elevation products

| Product | Provider | Official dataset/access | Use in TerraRover |
|---|---|---|---|
| ASTER GDEM V3 / ASTGTM.003 | NASA/METI; NASA LP DAAC | [NASA dataset](https://data.nasa.gov/dataset/aster-global-digital-elevation-model-v003-7ede1) · [NASA NetCDF V003](https://data.nasa.gov/dataset/aster-global-digital-elevation-model-netcdf-v003-90e58) | Earth regions whose ID ends `_ASTER` |
| NASADEM HGT V001 | NASA LP DAAC / JPL | [NASA dataset](https://data.nasa.gov/dataset/nasadem-merged-dem-global-1-arc-second-v001) | Earth regions whose ID ends `_NASADEM` |
| SRTMGL1 V003 | NASA/JPL SRTM; LP DAAC | [NASA dataset](https://data.nasa.gov/dataset/nasa-shuttle-radar-topography-mission-global-1-arc-second-v003-e47e1) · [Product DOI](https://doi.org/10.5067/MEaSUREs/SRTM/SRTMGL1.003) | Earth regions whose ID ends `_SRTM` |

**Nominal sampling:** approximately 1 arc second (~30 m near the equator), but effective native detail and errors vary with latitude, processing and source. Do not infer a pixel-size claim directly from the 5 km output grid. NASADEM and SRTM have related underlying data; differences between them are not independent ground truth.

**Local source naming** may include `ASTGTMV003_..._dem.nc`, `NASADEM_HGT_...zip` and `...SRTMGL1.hgt.zip`. These are upstream source files—not the small `DEM.tif` supplied to the web. Exact granule download URLs for every Earth region were not all available from the project source snapshot and are not fabricated here. Record individual source filenames/checksums in `metadatos.json` or a future manifest.

## Mars: MGS / MOLA topography (MEGDR)

Official product overview: [PDS Geosciences MGS MOLA MEGDRs](https://pds-geosciences.wustl.edu/missions/mgs/megdr.html). Maintained PDS4 directory: [MEG128](https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/). The 128-pixels-per-degree topography product uses prefix `megt`; radius `megr` and counts `megc` are *different* products.

| Topography IMG | Region crop(s) derived |
|---|---|
| `megt44n000hb.img` | Jezero Crater |
| `megt00n090hb.img` | Gale Crater, Gale Dunes, Gale Evaporites |
| `megt44n270hb.img` | Meridiani Planum |
| `megt00n270hb.img` | Meridiani Evaporites |
| `megt88n180hb.img` | Arcadia Planitia |
| `megt44n090hb.img` | Elysium Volcanic and Elysium Basaltic |

For every source IMG, preserve its accompanying `.xml` and `.hdr` (and `.lbl` when distributed). A single IMG source may be used for **multiple non-identical regional 5 × 5 km crops**. Do not duplicate full original raster files merely because two sites reference the same tile.

**Precision:** the project's 5 km MOLA examples have ~11 × 11 cells (~463 m each), useful only for regional relief. Descriptive names such as dunes and evaporites require independent material/sediment confirmation.

## Moon: SLDEM2015 and polar LOLA

Official product documentation: [LRO LOLA SLDEM](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/LOLA/SLDEM.htm). Source tile archive: [PDS Geosciences SLDEM2015 JP2](https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/sldem2015/tiles/jp2/). Alternative product browser: [MIT SLDEM2015 tiles](https://imbrium.mit.edu/BROWSE/SLDEM2015/TILES/).

| Original raster | 5 km region crop(s) |
|---|---|
| `sldem2015_512_00n_30n_000_045.jp2` | Mare Tranquillitatis **and** Rima Hadley |
| `sldem2015_512_30n_60n_315_360.jp2` | Mare Imbrium |
| `sldem2015_512_00n_30n_270_315.jp2` | Marius Hills |
| `sldem2015_512_60s_30s_315_360.jp2` | Tycho Crater |
| `sldem2015_512_00n_30n_315_360.jp2` | Copernicus Crater |
| `ldem_875s_5m.jp2` | Shackleton (LOLA **polar**, not SLDEM2015) |

SLDEM2015 512-pixel/degree tiles cover low and middle latitudes (~59 m spacing in the processed outputs). Shackleton is near 90° S and requires a polar product/projection. Source JP2 products may require an auxiliary scale/offset XML and label; using raw pixels without checking scale factors can produce wrong heights. A product's 5 m nominal map resolution does not imply every cell is independently measured at 5 m resolution.

## Shared sources are not shared final terrain files

- **Mare Tranquillitatis / Rima Hadley:** one SLDEM JP2, but two geographic centers and **two** separate cropped `DEM.tif` outputs.
- **Gale Crater / Gale Dunes / Gale Evaporites:** one MOLA IMG source, three study windows and separate derived outputs.
- **Elysium Volcanic / Elysium Basaltic:** one MOLA source, distinct centers; labels are hypotheses for research rather than mineralogical findings.
- **Multiple Earth products:** Black Point Lava Flow, La Joya, MDRS Utah and Sunset Crater have more than one DEM provider. Compare source measurements cautiously due to related inputs and different errors.

## Local traceability checklist

For each public `data/regions/<ID>/` object, preserve the upstream archive source, filename, center/bounds, coordinate convention, vertical reference/datum, original native resolution, scale/offset, NoData policy, processing script version/date, output geometry, any quality warnings, and dataset citation. Hashes/checksums are desirable but were not present for every known file in the snapshot; do not invent them.

## Data licensing and image rights

Government/public data access does not automatically license every derived graphic, external illustration, team software file or collaborator asset. Verify each source product's citation/data-use instructions. Neither NASA logos nor Space Apps branding implies sponsorship or endorsement of TerraRover. See [Licensing and attribution](LICENSING_AND_ATTRIBUTION.md).
