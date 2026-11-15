# Glossary

| Term | Definition in TerraRover |
|---|---|
| **DEM** | Digital Elevation Model: raster grid of numeric heights with georeferencing |
| **DTM / DSM** | Digital Terrain Model / Digital Surface Model; not always interchangeable with each other or with generic DEM terminology |
| **GeoTIFF** | TIFF with raster georeferencing; scientific elevation may be one numeric band, unlike a multichannel color preview |
| **CRS** | Coordinate Reference System; defines how raster coordinates correspond to a body/surface |
| **UTM** | Universal Transverse Mercator, commonly used for metric Earth regional maps |
| **NoData** | Declared missing-cell value or mask; not necessarily zero |
| **GSD** | Ground Sampling Distance; native sample spacing versus a resampled final grid step |
| **ROI** | Region of Interest; here typically 5,000 × 5,000 m |
| **ASTER GDEM** | Global terrain DEM derived from ASTER observations, NASA/METI project |
| **NASADEM** | NASA reprocessed SRTM-related DEM product |
| **SRTM** | Shuttle Radar Topography Mission elevation data |
| **MOLA** | Mars Orbiter Laser Altimeter; source of regional Mars topography |
| **MEGDR** | MOLA Mission Experiment Gridded Data Record, including `megt` topography |
| **LOLA** | Lunar Orbiter Laser Altimeter, Lunar Reconnaissance Orbiter instrument |
| **SLDEM2015** | Merged LOLA and Kaguya lunar topography product covering broad nonpolar latitudes |
| **Hypsometric integral** | Summary of normalized elevation distribution within a terrain window |
| **Slope** | Estimated surface inclination computed from DEM gradients |
| **TRI** | Terrain Ruggedness Index; TerraRover's 3-cell mean-deviation is **a proxy**, not a strict standard TRI |
| **TPI** | Topographic Position Index; local elevation compared with neighborhood mean |
| **Skewness** | A measure of asymmetry of a height distribution |
| **Wasserstein distance** | Distance between two probability distributions; TerraRover applies it to normalized elevation samples |
| **K–S statistic** | Kolmogorov–Smirnov statistic measuring maximum separation between empirical distributions |
| **Cosine similarity** | Angular alignment of feature vectors, not a geological probability |
| **Vertical datum** | Reference surface for reported elevations; differs between bodies/products |
| **Native resolution** | Original product's effective/nominal sample spacing, which can differ from output raster spacing |
| **Analog site** | Terrestrial environment hypothesized to share a particular scientific property with a planetary reference; requires evidence and clear analogy type |
| **Rover traversability** | Whether a specified rover could traverse terrain under specified physical conditions; cannot be inferred reliably from a coarse DEM alone |
| **Plotly** | Library used by the supplied interactive 3D HTML exports |
| **FastAPI** | Python framework serving the numeric-analysis API and public assets |
| **Rasterio / GDAL** | Raster data access and geospatial metadata operations |
| **Community DEM** | Visitor-supplied, format-validated but geologically **unverified** public terrain model |
