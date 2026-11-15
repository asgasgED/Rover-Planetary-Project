# Licensing, attribution and publication responsibilities

## No license assumed

The user requested a GitHub-ready documentation package and allowed omission of a license if not needed or not established. **A `LICENSE` file has intentionally not been generated**, because no agreement among the collaborators regarding software ownership and rights was supplied.

Without a software license, people can usually view a public GitHub repository, but **public visibility alone does not grant all reuse, modification or redistribution rights**. Ask the team to choose an appropriate license only after checking:

1. Who owns and has authority to license the code created by the Killa Coders team.
2. Whether the project includes code from employers, classes, external frameworks, third-party repositories or AI-generated contributions with additional restrictions.
3. Whether the desired rights extend to data, images, logos or only code.
4. Whether NASA competition branding has separate conditions.

## Distinct rights categories

| Asset group | Guidance |
|---|---|
| Team source code | Choose and add a project software license with all authorized collaborators |
| NASA Earthdata / PDS products | Use each dataset's formal citation and product use notices; retain original metadata |
| Project-generated 5 km rasters | Determine whether derived data redistribution is permitted and what attribution is required |
| External imagery | Check the specific photographer/agency/image license; do not infer from being online |
| NASA / Space Apps branding | Follow official trademark and brand use rules; no implication of NASA endorsement |
| Killa Coders logo | Confirm the team owns the asset and decide whether it is freely reusable |
| Community user uploads | Require uploader permission/consent, enforce takedown process and clear publication terms |
| Third-party software packages | Comply with dependencies' existing package licenses; they are not replaced by the repository's license |

## Citation recommendations

Cite the **specific dataset and product DOI** rather than only the agency's home page. Official source references are collected in [Data sources](DATA_SOURCES.md). Where a source's original exact granule URL was not available, document that gap instead of constructing a plausible but unverified link.

## Practical checklist before making the repository public

- [ ] Confirm authorship/ownership with the team.
- [ ] Choose a software license and add the official text if approved.
- [ ] Check included planet images, icons and both brand logos.
- [ ] Confirm which GeoTIFFs, derived rasters and Plotly bundles may be published.
- [ ] Add the required data citations and any disclaimers.
- [ ] Remove `.env`, `.venv`, secret keys and private notes.
- [ ] Review the community upload terms and takedown process.

## Disclaimer

TerraRover is an independently developed research prototype by Killa Coders. Its appearance and use of publicly available agency data do not make it a NASA, USGS, MIT or AMD official service.
