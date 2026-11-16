#!/usr/bin/env python3
"""TerraRover DEM converter: synthetic DEMs and georeferenced GeoTIFFs."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import calculate_default_transform, reproject, Resampling, transform as transform_coords
from scipy.ndimage import zoom, distance_transform_edt


def generate_sample_dem(path: Path, size_m=20.0, resolution_m=0.25):
    path.parent.mkdir(parents=True, exist_ok=True)
    n = int(round(size_m / resolution_m)) + 1
    x = np.linspace(0, size_m, n)
    y = np.linspace(0, size_m, n)
    xx, yy = np.meshgrid(x, y)
    slope = 0.045 * xx
    undulations = 0.065*np.sin(0.45*xx)*np.cos(0.40*yy) + 0.03*np.sin(0.9*xx + 0.7*yy)
    crater_dist = np.sqrt((xx-11.0)**2 + (yy-10.5)**2)
    crater = -0.22*np.exp(-(crater_dist**2)/3.5) + 0.09*np.exp(-((crater_dist-2.3)**2)/0.8)
    mound1 = 0.16*np.exp(-(((xx-6.5)**2 + (yy-8.5)**2)/1.4))
    mound2 = 0.19*np.exp(-(((xx-14.5)**2 + (yy-11.5)**2)/1.8))
    dem = slope + undulations + crater + mound1 + mound2
    dem -= dem.min()
    # Local metric CRS only for this synthetic test; it is not a real location.
    with rasterio.open(path, "w", driver="GTiff", height=n, width=n, count=1,
                       dtype="float32", crs="EPSG:32718",
                       transform=from_origin(500000, 8500000, resolution_m, resolution_m),
                       nodata=np.nan) as dst:
        dst.write(dem.astype("float32"), 1)
        dst.update_tags(source="synthetic_analog_generator", resolution_m=str(resolution_m))
    print(f"[DEM] Sintético generado: {path} ({n}x{n}, {resolution_m} m/px)")


def utm_crs_for_lonlat(lon, lat):
    zone = max(1, min(60, int(math.floor((lon + 180) / 6)) + 1))
    return f"EPSG:{(32600 if lat >= 0 else 32700) + zone}"


def fill_invalid_nearest(array):
    valid = np.isfinite(array)
    if not valid.any():
        raise ValueError("La región seleccionada no contiene elevaciones válidas.")
    missing = int(array.size - valid.sum())
    if missing:
        nearest = distance_transform_edt(~valid, return_distances=False, return_indices=True)
        array[~valid] = array[tuple(nearest[:, ~valid])]
    return array, missing


def load_local_dem(path: Path):
    """Read an already metric local/synthetic DEM without changing its grid."""
    with rasterio.open(path) as src:
        if src.crs is None:
            raise ValueError("El TIFF no declara CRS. No se puede asumir su escala ni ubicación.")
        data = src.read(1, masked=True).filled(np.nan).astype(np.float64)
        data, missing = fill_invalid_nearest(data)
        meta = {
            "source_file": str(path), "source_crs": src.crs.to_string(),
            "source_dimensions_px": {"width": src.width, "height": src.height},
            "source_resolution": [float(v) for v in src.res],
            "source_units": list(src.units) if src.units else None,
            "filled_pixels": missing, "processing": "local_metric_raster"
        }
        return data, meta


def load_geotiff_roi(path: Path, roi_width_m: float, roi_height_m: float,
                     pixel_size_m=None, target_crs=None,
                     center_lon=None, center_lat=None):
    """
    Load a GeoTIFF and extract a metric ROI.

    - Projected CRS in metres: preserve the original CRS.
      This supports Earth, Mars, Moon and other planetary DEMs.
    - Geographic CRS: use the existing Earth-oriented UTM workflow.
    """

    with rasterio.open(path) as src:

        if src.crs is None:
            raise ValueError(
                "El GeoTIFF no declara CRS; no se puede procesar con seguridad."
            )

        if roi_width_m <= 0 or roi_height_m <= 0:
            raise ValueError("Las dimensiones de la ROI deben ser positivas.")

        if (center_lon is None) != (center_lat is None):
            raise ValueError(
                "Indica ambos parámetros --center-lon y --center-lat."
            )

        # Read source elevation data.
        source = src.read(1, masked=True).filled(np.nan).astype(np.float32)

        # ---------------------------------------------------------
        # CASE 1: PROJECTED CRS IN METRES (Earth, Mars, Moon, etc.)
        # ---------------------------------------------------------

        if src.crs.is_projected:

            if src.crs.linear_units != "metre":
                raise ValueError(
                    f"El CRS proyectado utiliza '{src.crs.linear_units}', "
                    "no metros. Se requiere conversión explícita de unidades."
                )

            if center_lon is not None:
                raise ValueError(
                    "Para un DEM proyectado, el centro se determina "
                    "automáticamente desde sus coordenadas X/Y. "
                    "No utilices --center-lon ni --center-lat."
                )

            if target_crs is not None:
                requested_crs = rasterio.crs.CRS.from_user_input(target_crs)

                if requested_crs != src.crs:
                    raise ValueError(
                        "No se permite reproyectar automáticamente un DEM "
                        "planetario a otro CRS. Conserva el CRS original."
                    )

            # Preserve native projected coordinates.
            dst_crs = src.crs

            # Center of the source raster in its native coordinates.
            center_x = (src.bounds.left + src.bounds.right) / 2
            center_y = (src.bounds.bottom + src.bounds.top) / 2

            # Native pixel resolution.
            native_res = (
                abs(src.res[0]) + abs(src.res[1])
            ) / 2

            center_metadata = {
                "x": float(center_x),
                "y": float(center_y),
                "coordinate_units": "metres"
            }

            processing_mode = "native_projected_metric_crs"

        # ---------------------------------------------------------
        # CASE 2: GEOGRAPHIC CRS (traditional Earth workflow)
        # ---------------------------------------------------------

        else:

            if center_lon is None:
                cx = (src.bounds.left + src.bounds.right) / 2
                cy = (src.bounds.bottom + src.bounds.top) / 2

                lons, lats = transform_coords(
                    src.crs, "EPSG:4326", [cx], [cy]
                )

                center_lon = float(lons[0])
                center_lat = float(lats[0])

            dst_crs = target_crs or utm_crs_for_lonlat(
                center_lon, center_lat
            )

            xs, ys = transform_coords(
                "EPSG:4326", dst_crs,
                [center_lon], [center_lat]
            )

            center_x = float(xs[0])
            center_y = float(ys[0])

            default_transform, _, _ = calculate_default_transform(
                src.crs, dst_crs,
                src.width, src.height,
                *src.bounds
            )

            native_res = (
                abs(default_transform.a) +
                abs(default_transform.e)
            ) / 2

            center_metadata = {
                "longitude": center_lon,
                "latitude": center_lat
            }

            processing_mode = "geographic_to_metric_reprojection"

        # ---------------------------------------------------------
        # COMMON ROI GENERATION
        # ---------------------------------------------------------

        out_res = (
            float(pixel_size_m)
            if pixel_size_m is not None
            else float(native_res)
        )

        if out_res <= 0:
            raise ValueError("La resolución de salida debe ser positiva.")

        cols = max(
            2,
            int(math.ceil(roi_width_m / out_res)) + 1
        )

        rows = max(
            2,
            int(math.ceil(roi_height_m / out_res)) + 1
        )

        actual_w = (cols - 1) * out_res
        actual_h = (rows - 1) * out_res

        dst_transform = from_origin(
            center_x - actual_w / 2,
            center_y + actual_h / 2,
            out_res,
            out_res
        )

        destination = np.full(
            (rows, cols),
            np.nan,
            dtype=np.float32
        )

        # Reproject/resample onto the ROI grid.
        # For planetary DEMs, source and destination CRS are identical.
        reproject(
            source=source,
            destination=destination,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=np.nan,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear
        )

        valid_before_fill = int(np.isfinite(destination).sum())

        destination, missing = fill_invalid_nearest(destination)

        metadata = {
            "source_file": str(path),
            "source_crs": src.crs.to_string(),
            "target_crs": dst_crs.to_string(),
            "processing_mode": processing_mode,

            "source_dimensions_px": {
                "width": src.width,
                "height": src.height
            },

            "source_bounds": [
                src.bounds.left,
                src.bounds.bottom,
                src.bounds.right,
                src.bounds.top
            ],

            "source_native_resolution_approx_m": round(
                float(native_res), 3
            ),

            "output_resolution_m": round(out_res, 3),

            "roi_center": center_metadata,

            "roi_dimensions_m": {
                "width": round(actual_w, 3),
                "height": round(actual_h, 3)
            },

            "valid_pixels_before_fill": valid_before_fill,
            "filled_pixels": missing,
            "resampling": "bilinear"
        }

        return destination.astype(np.float64), out_res, metadata


def convert_to_webots(elev, output_wbt: Path, meta_out: Path, pixel_size_m: float,
                      terrain_name: str, source_meta: dict, vertical_scale=1.0,
                      max_nodes=120, start_xy=None, goal_xy=None, mode="auto_eval"):
    if elev.ndim != 2 or min(elev.shape) < 2:
        raise ValueError("El DEM debe ser una matriz 2D de al menos 2x2 píxeles.")
    if pixel_size_m <= 0 or max_nodes < 2:
        raise ValueError("pixel_size_m debe ser positivo y max_nodes >= 2.")

    elev = np.asarray(elev, dtype=np.float64) * vertical_scale
    if not np.isfinite(elev).all():
        raise ValueError("El DEM aún contiene NaN o infinitos.")
    source_min, source_max = float(elev.min()), float(elev.max())
    elev -= source_min

    original_rows, original_cols = elev.shape
    extent_x = (original_cols - 1) * pixel_size_m
    extent_y = (original_rows - 1) * pixel_size_m
    scale = min(1.0, (max_nodes - 1)/(original_rows - 1), (max_nodes - 1)/(original_cols - 1))
    if scale < 1.0:
        elev = zoom(elev, (scale, scale), order=1)
    rows, cols = elev.shape
    x_spacing, y_spacing = extent_x/(cols-1), extent_y/(rows-1)

    dz_dy, dz_dx = np.gradient(elev, y_spacing, x_spacing)
    slopes = np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))

    sx, sy = start_xy if start_xy is not None else (0.10*extent_x, 0.50*extent_y)
    gx, gy = goal_xy if goal_xy is not None else (0.90*extent_x, 0.50*extent_y)
    mx, my = min(x_spacing, extent_x/4), min(y_spacing, extent_y/4)
    sx, gx = float(np.clip(sx, mx, extent_x-mx)), float(np.clip(gx, mx, extent_x-mx))
    sy, gy = float(np.clip(sy, my, extent_y-my)), float(np.clip(gy, my, extent_y-my))
    ix, iy = int(round(sx/x_spacing)), int(round(sy/y_spacing))
    patch = elev[max(0,iy-1):min(rows,iy+2), max(0,ix-1):min(cols,ix+2)]
    sz = float(patch.max()) + 0.16

    flat = elev.flatten(order="C")
    height_lines = ["          " + ", ".join(f"{v:.4f}" for v in flat[i:i+12])
                    for i in range(0, len(flat), 12)]
    height_block = ",\n".join(height_lines)
    rover_args = f'"{mode}", "{gx:.2f}", "{gy:.2f}"' if mode == "auto_eval" else f'"{mode}"'

    world = f'''#VRML_SIM R2025a utf8
EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2025a/projects/objects/backgrounds/protos/TexturedBackground.proto"
EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2025a/projects/objects/backgrounds/protos/TexturedBackgroundLight.proto"
EXTERNPROTO "../protos/Sojourner.proto"

WorldInfo {{ title "TerraRover - DEM: {terrain_name}" basicTimeStep 16 }}
ViViewpoint {{
  orientation 1 0 0 0.733
  position 2500 7000 5000
}}
TexturedBackground {{}}
TexturedBackgroundLight {{}}
DEF DEM_TERRAIN Solid {{
  children [ Shape {{ appearance PBRAppearance {{ baseColor 0.68 0.43 0.28 roughness 0.93 }}
    geometry DEF DEM_GRID ElevationGrid {{ xDimension {cols} xSpacing {x_spacing:.6f}
      yDimension {rows} ySpacing {y_spacing:.6f} height [\n{height_block}\n      ] }} }} ]
  name "{terrain_name}" boundingObject USE DEM_GRID
}}
DEF ROVER Sojourner {{ translation {sx:.3f} {sy:.3f} {sz:.3f} rotation 0 0 1 0
  controller "rover_controller" controllerArgs [ {rover_args} ] }}
Robot {{ name "terrain_evaluator_supervisor" supervisor TRUE controller "terrain_evaluator"
  controllerArgs [ "{terrain_name}" "{gx:.2f}" "{gy:.2f}" "450" ] }}
'''
    output_wbt.parent.mkdir(parents=True, exist_ok=True)
    output_wbt.write_text(world, encoding="utf-8")
    summary = {
        "terrain_id": terrain_name, "source_dem": source_meta.get("source_file"),
        "webots_world": str(output_wbt),
        "grid_dimensions": {"xDimension": cols, "yDimension": rows},
        "spacing_m": {"xSpacing": round(x_spacing,5), "ySpacing": round(y_spacing,5)},
        "physical_extent_m": {"width_x": round(extent_x,2), "height_y": round(extent_y,2)},
        "source_elevation_range_m": {"min": round(source_min,3), "max": round(source_max,3)},
        "elevation_range_after_normalization_m": {"min": 0.0, "max": round(float(elev.max()),3)},
        "topography_stats": {"max_slope_deg": round(float(slopes.max()),2),
                              "mean_slope_deg": round(float(slopes.mean()),2)},
        "rover_spawn": {"x": round(sx,3), "y": round(sy,3), "z": round(sz,3)},
        "mission_goal": {"x": round(gx,3), "y": round(gy,3)},
        "source_metadata": source_meta
    }
    meta_out.parent.mkdir(parents=True, exist_ok=True)
    meta_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[DEM Converter] Mundo: {output_wbt}")
    print(f"[DEM Converter] Malla: {cols}x{rows}; extensión: {extent_x:.1f}x{extent_y:.1f} m")
    print(f"[DEM Converter] Espaciado: {x_spacing:.2f}x{y_spacing:.2f} m")
    print(f"[DEM Converter] Elevación fuente: {source_min:.2f} a {source_max:.2f} m")
    print(f"[DEM Converter] Metadatos: {meta_out}")


def main():
    base = Path(__file__).resolve().parents[2]
    p = argparse.ArgumentParser(description="Convierte DEM sintético o GeoTIFF a Webots ElevationGrid.")
    p.add_argument("--input", type=Path, help="GeoTIFF de entrada.")
    p.add_argument("--generate-sample", action="store_true")
    p.add_argument("--pixel-size", type=float, default=None,
                   help="Resolución de salida en m/px; en GeoTIFF se usa resolución nativa si se omite.")
    p.add_argument("--roi-width-m", type=float, default=5000.0)
    p.add_argument("--roi-height-m", type=float, default=5000.0)
    p.add_argument("--center-lon", type=float)
    p.add_argument("--center-lat", type=float)
    p.add_argument("--target-crs", default=None, help="CRS proyectado; por defecto UTM automático.")
    p.add_argument("--vertical-scale", type=float, default=1.0)
    p.add_argument("--max-nodes", type=int, default=120)
    p.add_argument("--start-x", type=float)
    p.add_argument("--start-y", type=float)
    p.add_argument("--goal-x", type=float)
    p.add_argument("--goal-y", type=float)
    p.add_argument("--mode", choices=["auto_eval", "manual"], default="auto_eval")
    args = p.parse_args()

    if (args.start_x is None) != (args.start_y is None):
        p.error("--start-x y --start-y deben indicarse juntos.")
    if (args.goal_x is None) != (args.goal_y is None):
        p.error("--goal-x y --goal-y deben indicarse juntos.")

    if args.generate_sample or args.input is None:
        sample = base / "terrains/imported_terrains/sample_analog_dem.tif"
        resolution = args.pixel_size or 0.25
        generate_sample_dem(sample, 20.0, resolution)
        elev, source_meta = load_local_dem(sample)
        pixel_size = resolution
        start = (args.start_x, args.start_y) if args.start_x is not None else (2.0,10.0)
        goal = (args.goal_x, args.goal_y) if args.goal_x is not None else (17.0,10.0)
        name = "sample_analog_dem"
    else:
        tif = args.input.expanduser().resolve()
        if not tif.is_file():
            p.error(f"No existe el archivo: {tif}")
        elev, pixel_size, source_meta = load_geotiff_roi(
            tif, args.roi_width_m, args.roi_height_m, args.pixel_size,
            args.target_crs, args.center_lon, args.center_lat)
        start = (args.start_x, args.start_y) if args.start_x is not None else None
        goal = (args.goal_x, args.goal_y) if args.goal_x is not None else None
        name = tif.stem

    convert_to_webots(
        elev, base / "worlds" / f"dem_{name}.wbt",
        base / "terrains/imported_terrains" / f"{name}_meta.json",
        pixel_size, name, source_meta, args.vertical_scale, args.max_nodes,
        start, goal, args.mode)


if __name__ == "__main__":
    main()
