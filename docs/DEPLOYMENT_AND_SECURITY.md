# Deployment and security considerations

## Reality of public deployment

The application is **not a static-only website**. It uses Python/FastAPI for numeric analysis, PNG charts and community uploads; therefore **GitHub Pages alone cannot provide the full TerraRover experience**. GitHub Pages can host a frontend with a separate externally hosted API, if routes and CORS/proxy are configured appropriately. A hosting service supporting a long-running Python process or a container is more straightforward for the existing source layout.

No deployment pipeline or public site uptime was verified in the examined archive. These are implementation recommendations, not claims of production readiness.

## Minimum production hardening

1. Restrict public uploader or set `TERRAROVER_PUBLIC_UPLOADS=false` until authentication, moderation and persistent rate limits are available.
2. Enforce server-level request-body, CPU, RAM and processing-time limits for geospatial workloads.
3. Separate immutable curated data, public assets and quarantined community uploads.
4. Avoid exposing `.env`, `.venv`, source input archives, test fixtures or private team contact information.
5. Use HTTPS, trusted reverse-proxy settings, security logging without sensitive data, error reporting and backups.
6. Treat `data/regions/**` as **public**; confirm legal redistribution rights, hosting capacity and artifact sizes.
7. Add health monitoring beyond the basic `/api/health` handler and backup/rollback plans for `data/catalog.json`.
8. Adopt a documented policy for removing unlicensed or personally sensitive user-submitted materials.

## Sensitive values

The public v4.2 backend does not require AMD. An older `.env.example` may still mention historical AMD TokenLab variables; those are not needed for the public API. Never commit a real `.env`, hardcode a secret into JS, or place credentials in `catalog.json`.

## Supply chain and assets

- Python dependencies are version-ranged in `requirements-backend.txt`, not pinned with a lockfile. Test and lock actual builds before long-term reproducible deployment.
- The visual assets may include illustrative planet artwork and two logos. Verify usage rights separately; third-party emblems do not imply any NASA endorsement.
- The full team data directory can be larger than free-hosting limits. Consider an object store with explicit retention/versioning for large public DEMs.

## Storage and concurrency

The code uses a process-local IP rate limiter and a local JSON catalog protected by a threading lock. This is **not safe as a distributed, multi-instance production data store** without coordinated locks or an actual database. Two servers writing the same JSON file may race. Use a persistent database and governed object storage before horizontal scaling.

## Before announcing the site publicly

- Run tests on the exact production configuration.
- Perform a real mobile, desktop, light/dark contrast and keyboard-accessibility check.
- Confirm that every advertised dataset actually has its scientific `DEM.tif` and required viewer dependencies.
- Verify privacy, license, attribution, acknowledgments and scientific disclaimers.
- Disable or moderate public uploads and add operational monitoring.
- Validate API costs and resource exhaustion behavior under abusive or concurrent requests.
