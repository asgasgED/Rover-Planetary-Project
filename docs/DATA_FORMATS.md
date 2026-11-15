# Data formats, meaning and consumers

## Six canonical regional deliverables

| File | Content | Created upstream by | Used in TerraRover | Typical viewer |
|---|---|---|---|---|
| `DEM.tif` | Single-band numerical elevations in meters, CRS and transform, NoData marker | Geospatial crop/reprojection and validation | Catalog feature extraction, backend comparison, downloads | QGIS, GDAL, Rasterio |
| `Mapa_2D.tiff` | Georeferenced **color image** of the terrain (not scientific elevation values) | Geospatial visualization stage | Download/map context | QGIS, GDAL, TIFF viewer |
| `Mapa_2D.png` | Browser-friendly colored preview | Map rendering | Cards, region detail, thumbnail | Browser, image viewer |
| `Terreno_3D.html` | Interactive 3D relief generated with Plotly | 3D visualization stage | Embedded terrain viewer | Browser with JS |
| `Terreno_3D.obj` | Terrain geometry in Wavefront OBJ format | 3D export stage | Download, potential future simulation conversion | Blender, MeshLab, 3D tools |
| `metadatos.json` | Information on location, input source, resolution and geometry | Geospatial pipeline | Catalog context and provenance | Text editor / JSON tooling |

For each upstream **complete six-file** folder the importer validates its `DEM.tif`, obtains metrics, and places the six files under `data/regions/<REGION_ID>/`. `Terreno_3D.html` uses a relative reference to **`../plotly.min.js`**; place that JavaScript asset in the parent `regions` directory before attempting offline 3D viewing.

**Key invariant:** the scientific analysis must consume **`DEM.tif`**, not `Mapa_2D.tiff`, even if a colored TIFF opens successfully in Rasterio. Color pixels encode a rendering palette, not physical elevation in meters.

## Additional project files

| Extension | Meaning in this project | Required? |
|---|---|---|
| `.json` | Catalog entries, chemistry context and regional metadata | Yes for catalog; region-specific metadata with team source |
| `.py` | Python scientific functions, HTTP endpoints, importer and tests | Yes for backend |
| `.js` / `.mjs` | Frontend scripts and Node.js tests; Plotly bundle | Yes for UI / optional tests |
| `.html` / `.css` | Frontend markup and style | Yes for UI |
| `.png` / `.webp` / `.svg` | Scientific plots/previews or illustrative visual assets | If referenced by page |
| `.csv` | Potential rover telemetry, future study export | **Not yet a runtime requirement** |
| `.md` | Documentation | Developer/reference artifact |
| `.img`, `.hdr`, `.xml`, `.lbl` | Original NASA PDS MOLA topography and labels/headers | **Upstream**, not required by web UI |
| `.jp2`, `_aux.xml`, `_jp2.lbl` | Original SLDEM / LOLA elevation and auxiliary labels | **Upstream**, not required by web UI |
| `.hgt`, `.nc` | Original NASADEM/SRTM or ASTER elevation archives | **Upstream**, not required by web UI |
| `.wbt`, `.proto` | Webots world / robot PROTO formats | **Not bundled into v4.2 public runtime** |

## Units and projections

- **Extent:** 5,000 meters per side in a suitable projected CRS. This is a map-grid footprint, not proof of meter-level sensor accuracy.
- **Horizontal resolution:** recorded separately as native GSD and final raster pixel spacing; those should not be conflated.
- **Vertical units:** team-delivered elevation values are intended in meters; the reference surface depends on the planet/source.
- **Earth coordinates:** geographic WGS84 can be meaningful for centers; UTM is common for 5 km metric windows.
- **Mars and Moon:** use the documented planetary longitude convention and body-specific reference. Do **not** assume their x/y and geographic coordinates use EPSG:4326.
- **NoData and water:** NoData is not zero; legitimate sea-level zeros may occur (e.g. the Timanfaya coastal region). A zero-valued pixel must not automatically be interpreted as passable rock or soil.

## 3D rendering caveat

`Terreno_3D.html` expresses relief without artificial vertical exaggeration (1:1 source vertical scale). Geometrical *relative* z coordinates in an OBJ export may be offset from raw elevation by a minimum or reference height: inspect its export metadata before treating OBJ z as the absolute elevation datum.

## Chemistry data is separate

`data/chemistry.json` contains **sample- or study-specific** mineral/oxide context for a small subset of catalog entries. It is not a pixel-level geochemical map, cannot be inferred from a DEM, and may require source-by-source bibliographic verification before publication.
