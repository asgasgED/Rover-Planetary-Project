"""Análisis morfológico de dos modelos digitales de elevación (DEM).

Este módulo conserva las fórmulas matemáticas proporcionadas para TerraRover.
Puede ejecutarse directamente o importarse desde graficos_terrarover.py.

Estructura esperada:
    terrarover_visualizacion/
    ├── datos/
    │   ├── Mapa_2D.tiff
    │   └── Mapa_2D3.tiff
    ├── analisis_morfologico.py
    └── graficos_terrarover.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import uniform_filter
from scipy.stats import skew


# ---------------------------------------------------------------------------
# RUTAS
# Este archivo se encuentra en la misma carpeta que graficos_terrarover.py.
# Los archivos TIFF se encuentran dentro de la subcarpeta "datos".
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATOS_DIR = BASE_DIR / "datos"

DEM_A_PATH = DATOS_DIR / "Mapa_2D.tiff"
DEM_B_PATH = DATOS_DIR / "Mapa_2D3.tiff"


def extrac_perfil_morf(ruta_tiff: str | Path) -> dict[str, float]:
    """Extrae los siete indicadores morfológicos del DEM indicado."""
    ruta_tiff = Path(ruta_tiff)

    if not ruta_tiff.is_file():
        raise FileNotFoundError(
            f"No se encontró el DEM: {ruta_tiff}\n"
            "Comprueba que el archivo exista y que su nombre coincida con la ruta."
        )

    with rasterio.open(ruta_tiff) as src:
        dem = src.read(1).astype(np.float64)
        if src.nodata is not None:
            dem[dem == src.nodata] = np.nan
        res_x, res_y = src.res

    dem = np.nan_to_num(dem, nan=np.nanmean(dem))
    min_val_z = np.min(dem)
    max_val_z = np.max(dem)
    relieve_total = (max_val_z - min_val_z) + 1e-8  # Se conserva el cálculo original.

    # Parámetro de volumen normalizado.
    integral_hip = np.mean((dem - min_val_z) / relieve_total)

    # Parámetro de elevación y gradiente por pendiente.
    dz_dy, dz_dx = np.gradient(dem, res_y, res_x)
    pendiente_rad = np.arctan(np.hypot(dz_dx, dz_dy))
    pendiente_media = np.degrees(np.mean(pendiente_rad))
    pendiente_std = np.degrees(np.std(pendiente_rad))
    asimetria_z = skew(dem.flatten())

    # Razón de área superficial (rugosidad 3D / área 2D).
    area_3d = np.sum(np.sqrt(1.0 + dz_dx**2 + dz_dy**2)) * res_x * res_y
    area_2d = dem.size * res_x * res_y
    razon_rugosidad_area = area_3d / area_2d

    # Cálculo de TRI normalizado (rugosidad), sensible al tamaño de ventana.
    media_vecinos = uniform_filter(dem, size=3)
    tri = np.mean(np.abs(dem - media_vecinos)) / relieve_total

    # TPI multiescala.
    tpi_local = dem - uniform_filter(dem, size=15)
    tpi_std = np.std(tpi_local) / relieve_total

    return {
        "integral_hipsometrica": integral_hip,
        "pendiente_media_deg": pendiente_media,
        "pendiente_std_deg": pendiente_std,
        "asimetria_elevacion": asimetria_z,
        "razon_area_3d2d": razon_rugosidad_area,
        "tri_normalizado": tri,
        "tpi_std_normalizado": tpi_std,
    }


def calc_analog(
    tiff_1: str | Path,
    tiff_2: str | Path,
) -> tuple[float, dict[str, float], dict[str, float]]:
    """Calcula la similitud coseno usando los perfiles morfológicos originales."""
    p1 = extrac_perfil_morf(tiff_1)
    p2 = extrac_perfil_morf(tiff_2)

    v1 = np.array(list(p1.values()))
    v2 = np.array(list(p2.values()))

    # Similitud del coseno (se conserva la fórmula original).
    similitud_coseno = np.dot(v1, v2) / (
        np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8
    )

    return float(similitud_coseno), p1, p2


# ---------------------------------------------------------------------------
# EJECUCIÓN DIRECTA
# El bloque protegido permite importar calc_analog() desde el visualizador
# sin que se ejecute automáticamente un segundo análisis.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    similitud, parte_1, parte_2 = calc_analog(DEM_A_PATH, DEM_B_PATH)

    print("\n========== ANÁLISIS MORFOLÓGICO TERRAROVER ==========")
    print(f"DEM A: {DEM_A_PATH}")
    print(f"DEM B: {DEM_B_PATH}")
    print(f"Similitud coseno: {similitud}")
    print(f"Perfil DEM A: {parte_1}")
    print(f"Perfil DEM B: {parte_2}")
