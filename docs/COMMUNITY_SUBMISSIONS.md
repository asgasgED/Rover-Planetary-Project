# Community DEM submissions

**Status: implemented experimentally; do not expose unrestricted internet uploads without additional safeguards.** Code: `backend/community.py` and the public upload form in `src/app.js`.

## User experience

The public interface provides **Submit a DEM**. A visitor selects a title, planet, single-band GeoTIFF and gives explicit consent that the submitted scientific file and preview will become publicly accessible. If technically acceptable, the app adds a new `Community_...` entry to the catalog.

## Implemented acceptance checks

- `.tif` or `.tiff` extension and GeoTIFF driver.
- Exactly one **numeric elevation** band; color TIFF is not accepted as a DEM.
- A declared **projected** coordinate system in meters and grid extent close to **5,000 × 5,000 m** (±1 m tolerance in this endpoint).
- Grid with at least three cells per axis and no more than 2,000,000 total cells.
- At least 50% finite, non-NoData elevation samples.
- File size up to **16 MiB**; 3 submissions per IP per hour in a process-local rate limiter; at most **30** community rows.
- A title between 3 and 80 characters, valid body selection, and explicit public publication consent.

A successful upload writes only `DEM.tif`, `Mapa_2D.png` and `metadatos.json` to a new **randomized** `data/regions/Community_<...>/` folder; it adds `user_uploaded: true` and `verdict: COMMUNITY_UNREVIEWED` in the public catalog. It does not generate scientific 3D meshes or claim to verify source geology.

## What the checks do NOT validate

- Whether the uploaded file is authentic satellite, rover or survey data.
- Whether its height values truly are meters relative to the declared datum (the system assumes submitter declaration).
- Whether planetary CRS values correspond to Earth, Mars or Moon correctly.
- Whether the 5 km window actually contains the named geological feature.
- Whether the uploader has valid redistribution rights beyond their own consent.
- Whether the content is free of malicious or resource-exhausting inputs beyond the current limits.

## Operator checklist for public hosting

- **Disable uploads by default in production** while abuse controls are being designed: set `TERRAROVER_PUBLIC_UPLOADS=false` before launch.
- Add user accounts or a moderated review queue, persistent per-user/region quotas, content scanning and durable rate limits across replicas.
- Set memory/CPU/time limits for Rasterio and PNG generation, and isolate untrusted files in restricted storage.
- Keep immutable raw originals and a deletion/takedown workflow for unauthorized content.
- Establish a data retention policy, privacy notice, legal basis for storing request metadata, and escalation for removal requests.
- Avoid exposing an untrusted uploader directly against your main curated dataset store.

## Catalog consistency

Team deliverables are six-file curated bundles; community submissions are three-file unreviewed bundles. An admin catalog **rebuild** may replace `catalog.json`; back up current user-submission entries first and reconcile them in a controlled migration. Incremental backend startup import is safer for adding new **team** items without disturbing existing records.
