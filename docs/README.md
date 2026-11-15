# TerraRover documentation

This documentation describes the **public-facing v4.2 codebase** examined in November 2026, plus the related geospatial 5 × 5 km deliverable workflow. Paths and API contracts refer to the project root `TerraRover_Plataforma/`. Features still in development are not presented as available.

## Start with

| If you want to… | Read |
|---|---|
| Understand the project's purpose and evidence boundaries | [Project overview](PROJECT_OVERVIEW.md) |
| Understand components and data flow | [Architecture](ARCHITECTURE.md) |
| Install, launch or import datasets | [Setup and local use](SETUP_AND_RUN.md), [Catalog and data](CATALOG_AND_DATA.md) |
| Understand upstream DEM processing | [Geospatial pipeline](GEOSPATIAL_PIPELINE.md) |
| Understand the files in the repository | [Repository reference](REPOSITORY_REFERENCE.md), [File formats](DATA_FORMATS.md) |
| Understand metrics and results | [Scientific methods](SCIENTIFIC_METHODS.md), [Limitations and validation](LIMITATIONS_AND_VALIDATION.md) |
| Use API endpoints | [API reference](API_REFERENCE.md) |
| Find Earth candidate analogs | [Analog discovery](ANALOG_DISCOVERY.md) |
| Submit a DEM | [Community data](COMMUNITY_SUBMISSIONS.md) |
| Work on future rover integration | [Rover simulation contract](ROVER_SIMULATION.md) |
| Deploy safely | [Deployment and security](DEPLOYMENT_AND_SECURITY.md) |
| Read chemical/mineral context responsibly | [Chemistry and evidence](CHEMISTRY_AND_CONTEXT.md) |
| Understand visual design and accessibility | [Design and accessibility](DESIGN_AND_ACCESSIBILITY.md) |
| Check official data provenance | [Official data sources](DATA_SOURCES.md) |
| Understand the project timeline/status | [Status and roadmap](STATUS_AND_ROADMAP.md), [Changelog](CHANGELOG.md) |
| Test or debug the project | [Testing and QA](TESTING_AND_QA.md), [Troubleshooting](TROUBLESHOOTING.md) |
| Contribute | [Contributing](CONTRIBUTING.md), [Licensing and attribution](LICENSING_AND_ATTRIBUTION.md) |
| Clarify terminology | [Glossary](GLOSSARY.md) |
| Read a quick Spanish overview | [Guía rápida (ES)](GUIA_RAPIDA_ES.md) |

## Documentation rules

1. **Observed in the examined code** means a function or route is implemented; it does not prove scientific validation or successful production deployment.
2. **Reported by team CLI** means execution output was provided, but the resulting raster was not necessarily inspected in the application archive.
3. **Catalogued** means an entry exists; **available** means its actual numerical DEM has been imported and inspected.
4. **Future** means an explicit integration placeholder or planned work, not an available service.
5. Every number must retain its unit, source and scale; a mathematical score is not geological proof.

The documentation-only ZIP does **not** contain the application source, scientific rasters, `.env`, API secrets or `.venv`. Copy the root `README.md` and this entire `docs/` folder into the existing application repository.
