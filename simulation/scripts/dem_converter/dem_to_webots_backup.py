#!/usr/bin/env python3
"""
TerraRover - Módulo: DEM Converter (Fases 4 y 5)
Equipo: Killa Coders | NASA Space Apps Challenge 2026
Descripción:
    Convierte Modelos Digitales de Elevación (DEM en formato GeoTIFF .tif)
    a mundos de Webots (.wbt) mediante mallas ElevationGrid con colisión física,
    configurando el rover (DEF ROVER) y el evaluador Supervisor (terrain_evaluator).
"""

import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import zoom, gaussian_filter


def generate_sample_dem(output_tif: Path, size_m: float = 20.0, resolution_m: float = 0.25) -> dict:
    """Genera un archivo GeoTIFF (.tif) de 32-bit float simulando un terreno análogo."""
    output_tif.parent.mkdir(parents=True, exist_ok=True)
    dim = int(round(size_m / resolution_m))

    x = np.linspace(0, size_m, dim)
    y = np.linspace(0, size_m, dim)
    xx, yy = np.meshgrid(x, y)

    slope = 0.045 * xx
    undulations = (
        0.065 * np.sin(0.45 * xx) * np.cos(0.40 * yy)
        + 0.03 * np.sin(0.9 * xx + 0.7 * yy)
    )
    crater_dist = np.sqrt((xx - 11.0) ** 2 + (yy - 10.5) ** 2)
    crater = -0.22 * np.exp(-(crater_dist ** 2) / 3.5) + 0.09 * np.exp(-((crater_dist - 2.3) ** 2) / 0.8)

    mound1 = 0.16 * np.exp(-(((xx - 6.5) ** 2 + (yy - 8.5) ** 2) / 1.4))
    mound2 = 0.19 * np.exp(-(((xx - 14.5) ** 2 + (yy - 11.5) ** 2) / 1.8))

    dem = slope + undulations + crater + mound1 + mound2
    dem = gaussian_filter(dem, sigma=1.8)
    dem -= np.min(dem)

    img = Image.fromarray(dem.astype(np.float32), mode="F")
    img.save(output_tif, format="TIFF")

    meta = {
        "source": "synthetic_analog_generator",
        "resolution_m": resolution_m,
        "width_m": size_m,
        "height_m": size_m,
    }
    print(f"[DEM Generator] DEM de prueba generado: {output_tif} ({dim}x{dim} px, {resolution_m} m/px)")
    return meta


def load_dem_tiff(tif_path: Path) -> np.ndarray:
    if not tif_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo DEM: {tif_path}")

    with Image.open(tif_path) as img:
        elev = np.array(img, dtype=np.float64)

    if elev.ndim == 3:
        elev = elev[:, :, 0]

    valid_mask = np.isfinite(elev) & (elev > -1e5) & (elev < 1e5)
    if not np.all(valid_mask):
        median_val = float(np.median(elev[valid_mask])) if np.any(valid_mask) else 0.0
        elev = np.where(valid_mask, elev, median_val)

    return elev


def convert_dem_to_webots(
    tif_path: Path,
    output_wbt: Path,
    meta_out: Path,
    pixel_size_m: float = 0.25,
    vertical_scale: float = 1.0,
    max_nodes: int = 120,
    start_xy: tuple = (2.0, 10.0),
    goal_xy: tuple = None,
    mode: str = "auto_eval",
) -> dict:
    elev = load_dem_tiff(tif_path) * vertical_scale
    elev -= np.min(elev)

    orig_rows, orig_cols = elev.shape
    phys_width_m = (orig_cols - 1) * pixel_size_m
    phys_height_m = (orig_rows - 1) * pixel_size_m

    scale = min(1.0, max_nodes / orig_rows, max_nodes / orig_cols)
    if scale < 1.0:
        elev = zoom(elev, scale, order=1)

    rows, cols = elev.shape
    x_spacing = phys_width_m / max(1, cols - 1)
    y_spacing = phys_height_m / max(1, rows - 1)

    dz_dy, dz_dx = np.gradient(elev, y_spacing, x_spacing)
    slope_deg = np.degrees(np.arctan(np.sqrt(dz_dx ** 2 + dz_dy ** 2)))
    max_slope_deg = float(np.max(slope_deg))
    mean_slope_deg = float(np.mean(slope_deg))

    sx = float(np.clip(start_xy[0], x_spacing, phys_width_m - x_spacing))
    sy = float(np.clip(start_xy[1], y_spacing, phys_height_m - y_spacing))
    ix = int(round(sx / x_spacing))
    iy = int(round(sy / y_spacing))
    local_patch = elev[max(0, iy - 1):min(rows, iy + 2), max(0, ix - 1):min(cols, ix + 2)]
    sz = float(np.max(local_patch)) + 0.16

    if goal_xy is None:
        gx = float(np.clip(phys_width_m - 2.5, x_spacing, phys_width_m - x_spacing))
        gy = sy
    else:
        gx = float(np.clip(goal_xy[0], x_spacing, phys_width_m - x_spacing))
        gy = float(np.clip(goal_xy[1], y_spacing, phys_height_m - y_spacing))

    heights_flat = elev.flatten(order="C")
    height_lines = []
    for i in range(0, len(heights_flat), 12):
        chunk = ", ".join(f"{val:.4f}" for val in heights_flat[i:i + 12])
        height_lines.append("          " + chunk)
    height_block = ",\n".join(height_lines)

    terrain_name = tif_path.stem
    rover_args = f'"{mode}", "{gx:.2f}", "{gy:.2f}"' if mode == "auto_eval" else f'"{mode}"'

    wbt_content = f"""#VRML_SIM R2025a utf8

EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2025a/projects/objects/backgrounds/protos/TexturedBackground.proto"
EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2025a/projects/objects/backgrounds/protos/TexturedBackgroundLight.proto"
EXTERNPROTO "../protos/Sojourner.proto"

WorldInfo {{
  title "TerraRover - DEM: {terrain_name}"
  basicTimeStep 16
  contactProperties [
    ContactProperties {{
      material1 "default"
      material2 "default"
      coulombFriction [
        0.8
      ]
    }}
  ]
}}

Viewpoint {{
  orientation -0.22 0.35 0.91 2.15
  position {sx - 1.8:.2f} {sy - 1.9:.2f} {sz + 0.95:.2f}
  follow "ROVER"
}}

TexturedBackground {{
}}

TexturedBackgroundLight {{
}}

DEF DEM_TERRAIN Solid {{
  translation 0 0 0
  children [
    Shape {{
      appearance PBRAppearance {{
        baseColor 0.68 0.43 0.28
        roughness 0.93
        metalness 0.0
      }}
      geometry DEF DEM_GRID ElevationGrid {{
        xDimension {cols}
        xSpacing {x_spacing:.5f}
        yDimension {rows}
        ySpacing {y_spacing:.5f}
        height [
{height_block}
        ]
      }}
    }}
  ]
  name "{terrain_name}"
  boundingObject USE DEM_GRID
}}

DEF ROVER Sojourner {{
  translation {sx:.3f} {sy:.3f} {sz:.3f}
  rotation 0 0 1 0
  controller "rover_controller"
  controllerArgs [
    {rover_args}
  ]
}}

Robot {{
  name "terrain_evaluator_supervisor"
  supervisor TRUE
  controller "terrain_evaluator"
  controllerArgs [
    "{terrain_name}"
    "{gx:.2f}"
    "{gy:.2f}"
    "450"
  ]
}}
"""

    output_wbt.parent.mkdir(parents=True, exist_ok=True)
    output_wbt.write_text(wbt_content, encoding="utf-8")

    summary = {
        "terrain_id": terrain_name,
        "source_dem": str(tif_path),
        "webots_world": str(output_wbt),
        "grid_dimensions": {"xDimension": int(cols), "yDimension": int(rows)},
        "spacing_m": {"xSpacing": round(x_spacing, 5), "ySpacing": round(y_spacing, 5)},
        "physical_extent_m": {"width_x": round(phys_width_m, 2), "height_y": round(phys_height_m, 2)},
        "elevation_range_m": {"min": 0.0, "max": round(float(np.max(elev)), 3)},
        "topography_stats": {
            "max_slope_deg": round(max_slope_deg, 2),
            "mean_slope_deg": round(mean_slope_deg, 2),
        },
        "rover_spawn": {"x": round(sx, 3), "y": round(sy, 3), "z": round(sz, 3)},
        "mission_goal": {"x": round(gx, 3), "y": round(gy, 3)},
    }

    meta_out.parent.mkdir(parents=True, exist_ok=True)
    meta_out.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"[DEM Converter] Mundo Webots generado: {output_wbt}")
    print(f"[DEM Converter] Metadatos guardados : {meta_out}")
    return summary


def main():
    base_dir = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description="Convierte un DEM GeoTIFF (.tif) a un mundo Webots (.wbt)")
    parser.add_argument("--input", type=Path, help="Ruta al archivo DEM (.tif)")
    parser.add_argument("--pixel-size", type=float, default=0.25, help="Resolución espacial del DEM en m/px")
    parser.add_argument("--vertical-scale", type=float, default=1.0, help="Escala vertical de elevación")
    parser.add_argument("--max-nodes", type=int, default=120, help="Máximo de nodos por eje")
    parser.add_argument("--start-x", type=float, default=2.0, help="Coordenada X inicial")
    parser.add_argument("--start-y", type=float, default=10.0, help="Coordenada Y inicial")
    parser.add_argument("--goal-x", type=float, default=17.0, help="Coordenada X meta")
    parser.add_argument("--goal-y", type=float, default=10.0, help="Coordenada Y meta")
    parser.add_argument("--mode", choices=["auto_eval", "manual"], default="auto_eval", help="Modo del controlador")
    parser.add_argument("--generate-sample", action="store_true", help="Genera y convierte DEM de prueba")

    args = parser.parse_args()

    if args.generate_sample or args.input is None:
        sample_tif = base_dir / "terrains" / "imported_terrains" / "sample_analog_dem.tif"
        generate_sample_dem(sample_tif, size_m=20.0, resolution_m=args.pixel_size)
        tif_path = sample_tif
    else:
        tif_path = args.input.resolve()

    wbt_out = base_dir / "worlds" / f"dem_{tif_path.stem}.wbt"
    meta_out = base_dir / "terrains" / "imported_terrains" / f"{tif_path.stem}_meta.json"

    convert_dem_to_webots(
        tif_path=tif_path,
        output_wbt=wbt_out,
        meta_out=meta_out,
        pixel_size_m=args.pixel_size,
        vertical_scale=args.vertical_scale,
        max_nodes=args.max_nodes,
        start_xy=(args.start_x, args.start_y),
        goal_xy=(args.goal_x, args.goal_y),
        mode=args.mode,
    )


if __name__ == "__main__":
    main()
