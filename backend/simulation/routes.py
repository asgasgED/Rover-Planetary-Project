"""TerraRover simulation Preview API.

Read-only terrain discovery until a real isolated Webots execution service is
connected. Historic prototype runs are intentionally NOT served to the public.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/simulation", tags=["simulation"])
ROOT = Path(__file__).resolve().parents[2]
SAFE_TERRAIN = re.compile(r"^[A-Za-z0-9_-]{1,160}$")


@router.get("/health")
def simulation_health():
    return {
        "service": "terrarover-simulation",
        "status": "available",
        "mode": "preview_readonly",
        "webots_live": False,
        "mission_result": None,
    }


@router.get("/status")
def webots_status():
    return {
        "service": "terrarover-simulation",
        "status": "available",
        "webots_installed": False,
        "webots_live": False,
        "execution_scope": "preview-readonly",
        "stream_mode": None,
        "message": "The Webots execution service is not connected yet.",
    }


@router.get("/terrains")
def simulation_terrains():
    catalog_path = ROOT / "data" / "catalog.json"
    regions_dir = ROOT / "data" / "regions"

    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        raise HTTPException(503, "Terrain catalog unavailable.")

    terrains = []
    for region in catalog.get("items", []):
        terrain_id = region.get("id", "")
        if not isinstance(terrain_id, str) or not SAFE_TERRAIN.fullmatch(terrain_id):
            continue

        folder = regions_dir / terrain_id
        preview = folder / "Mapa_2D.png"
        dem = folder / "DEM.tif"

        terrains.append({
            "id": terrain_id,
            "name": region.get("title") or terrain_id,
            "body": region.get("body", "Unknown"),
            "source": region.get("source", "Catalog"),
            "has_dem": dem.is_file(),
            "has_world": False,
            "has_rgb_map": preview.is_file(),
            "has_embedded_heights": False,
            "can_simulate": False,
            "can_create_parcel": False,
            "synthetic": False,
            "lfs_missing": False,
            "extent_x": 5000.0,
            "extent_y": 5000.0,
            "native_resolution_m": region.get("native_resolution_m"),
            "preview_url": (
                f"/data/regions/{terrain_id}/Mapa_2D.png"
                if preview.is_file() else None
            ),
            "warning": (
                "Terrain catalog preview only. Webots execution is not yet "
                "connected; no simulation result has been generated."
            ),
        })

    return terrains


@router.get("/runs/current")
def current_simulation():
    # No synthetic or historic metrics in place of an actual current run.
    return {
        "status": "idle",
        "webots_live": False,
        "stream_ready": False,
        "latest": {},
        "result": None,
        "message": "No simulation has been launched in the current service.",
    }
