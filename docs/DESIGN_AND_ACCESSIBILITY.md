# Interface design and accessibility

## Product direction

TerraRover is intended to resemble an accessible, professional research console rather than a marketing landing page. The current public variant favors a light background, readable scientific content and high-contrast floating panels. Original source DEM pseudocolor ramps are preserved as **data visualizations**, even when they contain colors not used in the brand palette.

## Project palette and role of color

| Color | HEX | Recommended use |
|---|---|---|
| Black | `#000000` | Dark text, technical readouts, high-contrast panels |
| White | `#FFFFFF` | Main content canvas, text on dark surfaces |
| Gray | `#626262` | Secondary descriptions (check actual contrast) |
| Royal blue | `#2F28FB` | Restrained active interactions; avoid low contrast on black |
| Red-orange | `#fc3c23` | Section accents and primary calls to action |
| Orange | `#fc3e00` | Data/mission highlights where semantically suitable |
| Deep red | `#b80c09` | Important state accents (not the only warning signal) |

The current source has multiple layered CSS files including `styles.css`, `cinematic.css`, `v3_palette.css`, `v4_light.css` and `public.css`. Changes to a selector in one layer may be overridden in a later file. A design-system cleanup should consolidate duplicate and conflicting rules while preserving the site's proven navigation.

## Accessibility acceptance checklist

- **Default state matters:** links, tabs, text on image cards and “Details” should be readable **without hover, text selection or keyboard focus**.
- Preserve a visible focus ring, keyboard-driven tabs, appropriate labels and functional forms.
- Avoid showing meaning solely through red/blue/green. Use text status and icons as well.
- Make touch targets large enough for phone use, and ensure cards, tables and code panels wrap or scroll without hiding core actions.
- Respect `prefers-reduced-motion`: cinematic effects should not block interaction or reading.
- Chart annotations should have axes, quantities, units and an accessible explanation. Pseudocolor elevation should include a legend.
- The Moon and Mars maps may use body-specific coordinates; do not silently display them as Earth WGS84 markers.

## Quality state

Tests of CSS classes and navigation do not constitute a complete automated visual QA. Before production, perform real Chromium/Firefox/mobile checks, contrast review, keyboard-only exploration and responsive screenshots at representative viewport sizes.

## Branding

Use the team-owned approved Killa Coders brand assets, subject to ownership confirmation. NASA Space Apps Challenge visuals and third-party planet imagery should be used only in accordance with their applicable policies. Do not imply an official NASA endorsement.
