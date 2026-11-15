# Catalog, geospatial handoff and datasets

## Exact scope

The examined catalog has **33 named entries**: 17 Earth, 9 Mars and 7 lunar. Its **initial** availability reflects the reference archive: five `disponible`, fourteen `auditoria_historica`, eight `cli_reportada`, and six `pendiente`. These statuses are **not immutable**: importing a valid six-file bundle changes a region to `disponible`.

A user's locally populated installation may contain all 33 imported sets. Do not confuse `33 catalogued` with `33 importable full GeoTIFF datasets` until inspecting the local files.

## Earth — 17 source-labelled entries

```text
Askja_ASTER
Badwater_Basin_ASTER
Black_Point_Lava_Flow_ASTER
Black_Point_Lava_Flow_NASADEM
Craters_of_the_Moon_NASADEM
Haughton_Crater_ASTER
Kilauea_ASTER
La_Joya_NASADEM
La_Joya_SRTM
MDRS_Utah_NASADEM
MDRS_Utah_SRTM
Salar_Atacama_NASADEM
Sunset_Crater_ASTER
Sunset_Crater_NASADEM
Timanfaya_ASTER
Wadi_Rum_ASTER
Yungay_NASADEM
```

Several physical sites are represented by more than one source; they are intentionally separate products, not duplicates of the same measurement. For example, La Joya, Black Point Lava Flow, MDRS Utah and Sunset Crater are used for relative cross-source checks. Agreement across derived elevation products is **not independent ground truth**.

## Mars — 9 entries

```text
Jezero_MOLA
Gale_Crater_MOLA
Gale_Dunes_MOLA
Gale_Evaporites_MOLA
Meridiani_Planum_MOLA
Meridiani_Evaporites_MOLA
Arcadia_Planitia_MOLA
Elysium_Volcanic_MOLA
Elysium_Basaltic_MOLA
```

**Shared source-tile relationship:**

| Original MOLA MEG128 topography image | Derived region(s) |
|---|---|
| `megt44n000hb.img` | Jezero |
| `megt00n090hb.img` | Gale Crater, Gale Dunes, Gale Evaporites |
| `megt44n270hb.img` | Meridiani Planum |
| `megt00n270hb.img` | Meridiani Evaporites |
| `megt88n180hb.img` | Arcadia Planitia |
| `megt44n090hb.img` | Elysium Volcanic, Elysium Basaltic |

**Caution:** names like “evaporites” or “dunes” refer to study objectives / nominated locations; the coarse topographic raster alone does not establish sedimentary chemistry or resolve individual small dunes.

## Moon — 7 entries

```text
Mare_Tranquillitatis_SLDEM
Mare_Imbrium_SLDEM
Marius_Hills_SLDEM
Tycho_Crater_SLDEM
Copernicus_Crater_SLDEM
Rima_Hadley_SLDEM
Shackleton_Crater_LOLA_POLAR
```

| Original elevation tile | Derived region(s) |
|---|---|
| `sldem2015_512_00n_30n_000_045.jp2` | Mare Tranquillitatis **and Rima Hadley** |
| `sldem2015_512_30n_60n_315_360.jp2` | Mare Imbrium |
| `sldem2015_512_00n_30n_270_315.jp2` | Marius Hills |
| `sldem2015_512_60s_30s_315_360.jp2` | Tycho Crater |
| `sldem2015_512_00n_30n_315_360.jp2` | Copernicus Crater |
| `ldem_875s_5m.jp2` | Shackleton (polar LOLA model; not SLDEM2015) |

This yields seven region crops from six unique original lunar rasters. **Sharing a source tile does not mean sharing a processed crop**: each site must have independent final 5 × 5 km bounds and its own `DEM.tif` and metadata.

## Region status meanings

| Value in `status` | Interpretation |
|---|---|
| `disponible` | Numerical DEM/region bundle copied or published, with technical checks (not scientific ground-truth validation) |
| `auditoria_historica` | Region listed in the prior 19-item audit; full web bundle may not have been bundled |
| `cli_reportada` | Team-reported successful Martian CLI processing, pending direct file publication in reference checkout |
| `pendiente` | Catalog placeholder with no complete bundle in current reference snapshot |

User-submitted community entries can also have `status=disponible` **and** `user_uploaded=true`, `verdict=COMMUNITY_UNREVIEWED`; availability is not a quality endorsement.

## Ingest process

For every named region: copy all six canonical files, place shared Plotly JS once in the parent directory, then import or restart the server. The importer rejects incomplete folders, invalid numeric/CRS rasters or area dimensions different from the 5 km target. A manual rebuild uses `scripts/preparar_catalogo.py`; the startup importer adds complete new items without replacing existing published complete rows.

```powershell
.\.venv\Scripts\python.exe scripts/preparar_catalogo.py --source "datos_para_importar/entrega_5km"
```

**Do not commit all raw global source DEM tiles automatically.** The original 5 km deliverables and published copies may be large, and publishing them may carry data redistribution, hosting-size or security implications. `data/catalog.json` points to browser-public assets, not private storage.
