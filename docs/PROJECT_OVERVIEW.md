# Project overview

## Purpose

TerraRover is a public-facing geospatial research application built by Killa Coders to explore a defensible early question: **which terrestrial terrain regions exhibit measured topographic characteristics resembling selected lunar or Martian landscapes, given the limits of the available DEMs?**

The problem is that raw planetary and Earth elevation archives differ in coordinate systems, vertical references, sampling density and file formats. A comparison application must not hide these differences or mislead a visitor with a visually compelling but physically unsupported score.

## Research objectives

1. Present consistent, traceable 5 × 5 km digital elevation windows from Earth, Mars and the Moon.
2. Characterize elevation geometry with a reproducible, initially limited set of terrain metrics.
3. Enable exploratory pairwise comparisons and candidate discovery with clear units, provenance and warnings.
4. Provide two- and three-dimensional views for datasets with genuine source products.
5. Prepare a future link between identified regions and rover simulation outputs—**not implemented in this release**.

## What the application is not

- Not a geologically calibrated analogue-classification model, a remote-sensing mineral mapper, or a substitute for field sampling.
- Not an automatic claim that candidate sites are physically identical across planets.
- Not a Webots, Gazebo or ROS 2 execution service at present.
- Not an official NASA publication or NASA-branded service.
- Not a complete original-source repository for all 33 regions by default. Original global satellite rasters and large PDS tiles belong in their own governed storage.

## Intended users

University students and teams learning geospatial analysis, planetary-science collaborators, researchers triaging potential analog sites, and developers preparing reproducible interactive DEM viewers. For scientific use, the user must review source provenance and data scale independently.

## Interfaces

- **Mission Control** — scientific mission context and navigation.
- **Planet Explorer** — selection of Earth, Moon or Mars regions and a coordinate-based exploration view.
- **Terrain Catalog / Detail** — search, filters, terrain facts, actual deliverables and material-composition context where documented.
- **Morphological Analysis** — measured terrain descriptors and visual summaries.
- **Planetary Comparator** — real numeric pairwise analysis from published DEMs.
- **Find Analog Sites** — preliminary Earth candidate ranking relative to a selected planetary region.
- **Rover Simulation** — reserved integration screen; no simulated outcomes asserted.

## Evidence boundary

All images used in hero banners are illustrative unless explicitly linked to a particular instrument/scene. Color elevation previews are visualization assets; only `DEM.tif` contains numeric height values. Mineral chemistry observations from a spacecraft sample or research paper are not spatial chemical measurements of every raster pixel.
