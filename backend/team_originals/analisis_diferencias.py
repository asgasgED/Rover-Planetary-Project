"""Análisis de diferencias entre dos modelos digitales de elevación (DEM) para TerraRover.

Este script adapta a Python convencional el primer bloque de análisis compartido.
Conserva el procedimiento original:
  1. Lee la primera banda de dos GeoTIFF.
  2. Si sus dimensiones son distintas, redimensiona la matriz del DEM B a la
     dimensión del DEM A mediante scipy.ndimage.zoom (interpolación bilineal).
  3. Calcula la diferencia absoluta, RMSE, diferencia máxima y promedio.
  4. Guarda mapa_diferencias.tiff y una visualización PNG en /resultados.

IMPORTANTE:
El remuestreo con zoom actúa sobre las matrices y no realiza reproyección ni
alineación geoespacial. Si CRS, transformaciones o extensiones no coinciden,
la comparación píxel a píxel debe interpretarse con cautela. No se modifican
las fórmulas estadísticas originales.
"""

from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.errors import RasterioIOError
from scipy.ndimage import zoom


# -----------------------------------------------------------------------------
# 1. RUTAS DEL PROYECTO
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATOS_DIR = BASE_DIR / "datos"
RESULTADOS_DIR = BASE_DIR / "resultados"

# Deben coincidir con los nombres de los GeoTIFF que tienes en /datos.
DEM_A_PATH = DATOS_DIR / "Mapa_2D.tiff"
DEM_B_PATH = DATOS_DIR / "Mapa_2D3.tiff"

# Archivos que generará este script.
DEM_B_REMUESTREADO_PATH = RESULTADOS_DIR / "origen_remuestreo.tiff"
DIFERENCIAS_TIFF_PATH = RESULTADOS_DIR / "mapa_diferencias.tiff"
DIFERENCIAS_PNG_PATH = RESULTADOS_DIR / "mapa_diferencias.png"

# Muestra la figura al terminar. El PNG se guarda siempre.
MOSTRAR_GRAFICO = True


# -----------------------------------------------------------------------------
# 2. VALIDACIONES Y UTILIDADES
# -----------------------------------------------------------------------------
def validar_archivos_entrada() -> None:
    """Comprueba que los dos DEM de entrada existan y puedan abrirse."""
    faltantes = [ruta for ruta in (DEM_A_PATH, DEM_B_PATH) if not ruta.is_file()]
    if faltantes:
        detalle = "\n".join(f"  - {ruta}" for ruta in faltantes)
        raise FileNotFoundError(
            "No se encontraron todos los DEM de entrada:\n"
            f"{detalle}\n\n"
            "Comprueba que ambos archivos estén dentro de la carpeta 'datos'."
        )

    for ruta in (DEM_A_PATH, DEM_B_PATH):
        try:
            with rasterio.open(ruta) as src:
                if src.count < 1:
                    raise ValueError(f"El raster no contiene bandas: {ruta}")
                if src.width < 2 or src.height < 2:
                    raise ValueError(
                        f"El raster debe tener al menos 2 filas y 2 columnas: {ruta}"
                    )
        except RasterioIOError as exc:
            raise RuntimeError(f"No se pudo abrir el archivo GeoTIFF: {ruta}\n{exc}") from exc


def adaptar_raster_a_base(
    ruta_origen: Path,
    ruta_base: Path,
    ruta_salida: Path,
) -> np.ndarray:
    """Redimensiona la primera banda del raster origen al tamaño del raster base.

    Se conserva el método del código original: interpolación bilineal sobre la
    matriz mediante scipy.ndimage.zoom. No se realiza reproyección geográfica.
    El raster de salida adopta la georreferenciación y dimensiones de la base.
    """
    with rasterio.open(ruta_base) as base, rasterio.open(ruta_origen) as origen:
        origen_data = origen.read(1).astype(np.float32)

        factores_zoom = (
            base.height / origen_data.shape[0],
            base.width / origen_data.shape[1],
        )

        destino_data = zoom(origen_data, factores_zoom, order=1).astype(np.float32)

        # Comprobación por seguridad frente a posibles diferencias de redondeo.
        if destino_data.shape != (base.height, base.width):
            raise RuntimeError(
                "El remuestreo no produjo las dimensiones esperadas. "
                f"Esperado: {(base.height, base.width)}; obtenido: {destino_data.shape}."
            )

        perfil_salida = base.profile.copy()
        perfil_salida.update(
            driver="GTiff",
            height=base.height,
            width=base.width,
            count=1,
            dtype="float32",
            nodata=origen.nodata,
            compress="lzw",
        )

        ruta_salida.parent.mkdir(parents=True, exist_ok=True)
        with rasterio.open(ruta_salida, "w", **perfil_salida) as destino:
            destino.write(destino_data, 1)

    print(f"[OK] DEM B remuestreado guardado en: {ruta_salida}")
    return destino_data


# -----------------------------------------------------------------------------
# 3. COMPARACIÓN DE LOS DOS DEM
# -----------------------------------------------------------------------------
def calcular_diferencias() -> tuple[np.ndarray, dict[str, float]]:
    """Calcula diferencias y métricas manteniendo las fórmulas originales."""
    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)

    with rasterio.open(DEM_A_PATH) as src_a, rasterio.open(DEM_B_PATH) as src_b:
        # Avisos sobre la referencia espacial. El código original no reproyecta.
        if src_a.crs != src_b.crs:
            print(
                "[ADVERTENCIA] Los sistemas de coordenadas (CRS) son diferentes. "
                "El script conservará la comparación matricial original; no reproyectará."
            )

        if src_a.transform != src_b.transform and src_a.shape == src_b.shape:
            print(
                "[ADVERTENCIA] Las dimensiones coinciden, pero las transformaciones "
                "geográficas son distintas. La comparación píxel a píxel puede no "
                "representar las mismas ubicaciones."
            )

        banda_a = src_a.read(1).astype(np.float32)
        banda_b = src_b.read(1).astype(np.float32)
        forma_a = banda_a.shape
        forma_b = banda_b.shape

        if forma_a != forma_b:
            print(
                "[INFO] Las dimensiones no coinciden. Se adaptará DEM B al tamaño de DEM A "
                "mediante interpolación bilineal de matriz."
            )
            banda_b = adaptar_raster_a_base(
                ruta_origen=DEM_B_PATH,
                ruta_base=DEM_A_PATH,
                ruta_salida=DEM_B_REMUESTREADO_PATH,
            )
        else:
            print("[OK] Los dos DEM tienen las mismas dimensiones.")

        # Aviso de NoData: se preserva el cálculo del bloque original, que no
        # excluía automáticamente esos valores de las métricas.
        if src_a.nodata is not None or src_b.nodata is not None:
            print(
                "[ADVERTENCIA] Al menos un DEM declara un valor NoData. "
                "Se conserva el cálculo original sobre las matrices completas; "
                "los valores NoData podrían influir en las métricas."
            )

        # Fórmulas originales, sin modificar.
        diferencia = np.abs(banda_a - banda_b)
        rmse = float(np.sqrt(np.mean((banda_a - banda_b) ** 2)))
        diferencia_maxima = float(np.max(diferencia))
        diferencia_promedio = float(np.mean(diferencia))

        # Se utiliza la georreferenciación del DEM A, que define la cuadrícula
        # final después del posible remuestreo matricial.
        perfil_salida = src_a.profile.copy()
        perfil_salida.update(
            driver="GTiff",
            count=1,
            dtype="float32",
            compress="lzw",
        )

    with rasterio.open(DIFERENCIAS_TIFF_PATH, "w", **perfil_salida) as destino:
        destino.write(diferencia.astype(np.float32), 1)

    metricas = {
        "rmse": rmse,
        "diferencia_maxima": diferencia_maxima,
        "diferencia_promedio": diferencia_promedio,
    }

    print("\n========== RESULTADOS DE LA COMPARACIÓN ==========")
    print(f"RMSE: {rmse:.4f}")
    print(f"Diferencia máxima entre píxeles: {diferencia_maxima:.4f}")
    print(f"Diferencia promedio: {diferencia_promedio:.4f}")
    print(f"[OK] GeoTIFF de diferencias guardado en: {DIFERENCIAS_TIFF_PATH}")

    return diferencia, metricas


# -----------------------------------------------------------------------------
# 4. VISUALIZACIÓN DEL MAPA DE DIFERENCIAS
# -----------------------------------------------------------------------------
def crear_visualizacion(diferencia: np.ndarray) -> Path:
    """Guarda el mapa de diferencias como PNG y opcionalmente lo muestra."""
    with rasterio.open(DEM_A_PATH) as src_a:
        bounds = src_a.bounds

    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

    fig, ax = plt.subplots(figsize=(11, 8))
    imagen = ax.imshow(
        diferencia,
        cmap="inferno",
        extent=extent,
        origin="upper",
        aspect="auto",
    )
    barra = fig.colorbar(imagen, ax=ax)
    barra.set_label("Magnitud de la diferencia")
    ax.set_title("TerraRover | Mapa de diferencia espacial", fontsize=15, weight="bold")
    ax.set_xlabel("Coordenada X")
    ax.set_ylabel("Coordenada Y")
    ax.grid(False)

    fig.tight_layout()
    fig.savefig(DIFERENCIAS_PNG_PATH, dpi=180, bbox_inches="tight")
    print(f"[OK] Imagen del mapa de diferencias guardada en: {DIFERENCIAS_PNG_PATH}")

    if MOSTRAR_GRAFICO:
        plt.show()

    plt.close(fig)
    return DIFERENCIAS_PNG_PATH


# -----------------------------------------------------------------------------
# 5. EJECUCIÓN PRINCIPAL
# -----------------------------------------------------------------------------
def main() -> int:
    print("=" * 62)
    print("TERRAROVER | ANÁLISIS DE DIFERENCIAS ENTRE DEM")
    print("=" * 62)
    print(f"DEM A: {DEM_A_PATH}")
    print(f"DEM B: {DEM_B_PATH}")
    print(f"Salida: {RESULTADOS_DIR}")

    try:
        validar_archivos_entrada()
        diferencia, _metricas = calcular_diferencias()
        crear_visualizacion(diferencia)
    except (FileNotFoundError, ValueError, RuntimeError, RasterioIOError) as exc:
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"\n[ERROR INESPERADO] {type(exc).__name__}: {exc}", file=sys.stderr)
        raise

    print("\n[FINALIZADO] Análisis de diferencias completado correctamente.")
    print("Ahora puedes ejecutar: python graficos_terrarover.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
