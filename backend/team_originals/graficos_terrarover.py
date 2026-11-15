from __future__ import annotations

import base64
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

# Este script guarda imÃ¡genes y no necesita abrir ventanas grÃ¡ficas.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.enums import Resampling


# ---------------------------------------------------------------------------
# 1. RUTAS Y CONFIGURACIÃ“N
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATOS_DIR = BASE_DIR / "datos"
RESULTADOS_DIR = BASE_DIR / "resultados"
DOTENV_PATH = BASE_DIR / ".env"

DEM_A_PATH = DATOS_DIR / "Mapa_2D.tiff"
DEM_B_PATH = DATOS_DIR / "Mapa_2D3.tiff"
DIFERENCIAS_PATH = RESULTADOS_DIR / "mapa_diferencias.tiff"

# OpenAI-compatible base URL. Debe terminar en /v1, no en /chat/completions.
AMD_BASE_URL = os.getenv("AMD_BASE_URL", "https://api.tokenlab.amd.com/v1")
# Identificador exacto utilizado en el ejemplo Python de TokenLab proporcionado.
AMD_MODEL = os.getenv("AMD_MODEL", "Qwen3.8-27B")
AMD_API_KEY = os.getenv("AMD_API_KEY", "")
ENVIAR_A_IA = os.getenv("ENVIAR_A_IA", "true").strip().lower() in {
    "1", "true", "yes", "si", "sÃ­"
}

# Ajustes exclusivamente visuales; no intervienen en las fÃ³rmulas matemÃ¡ticas.
DPI_FIGURAS = 180
MAX_DIMENSION_VISUALIZACION = 1800
MAX_MUESTRAS_HISTOGRAMA = 250_000
NUM_BINS_HISTOGRAMA = 45

COLOR_A = "#2585D8"
COLOR_B = "#E39A35"
COLOR_TEXTO = "#253247"
COLOR_SECUNDARIO = "#68778D"
COLOR_FONDO = "#FFFFFF"

NOMBRES_METRICAS = {
    "integral_hipsometrica": "Integral hipsomÃ©trica",
    "pendiente_media_deg": "Pendiente media (Â°)",
    "pendiente_std_deg": "Desv. estándar de pendiente (Â°)",
    "asimetria_elevacion": "Asimetria de elevación",
    "razon_area_3d2d": "Razón de Área 3D/2D",
    "tri_normalizado": "TRI normalizado",
    "tpi_std_normalizado": "TPI normalizado",
}


# Cargar el .env ubicado junto al script, no depender del directorio desde
# el que se ejecuta Python.
try:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=DOTENV_PATH, override=False)
except ImportError:
    # TambiÃ©n se pueden definir las variables directamente en el entorno.
    pass

# Leer despuÃ©s de load_dotenv para que las variables del archivo .env estÃ©n disponibles.
AMD_BASE_URL = os.getenv("AMD_BASE_URL", AMD_BASE_URL)
AMD_MODEL = os.getenv("AMD_MODEL", AMD_MODEL)
AMD_API_KEY = os.getenv("AMD_API_KEY", AMD_API_KEY)
ENVIAR_A_IA = os.getenv("ENVIAR_A_IA", str(ENVIAR_A_IA)).strip().lower() in {
    "1", "true", "yes", "si", "sÃ­"
}


# ---------------------------------------------------------------------------
# 2. UTILIDADES
# ---------------------------------------------------------------------------
def comprobar_entradas_principales() -> None:
    """Comprueba que los DEM y el módulo matemático están en las rutas esperadas."""
    faltantes = [ruta for ruta in (DEM_A_PATH, DEM_B_PATH) if not ruta.is_file()]
    if faltantes:
        detalle = "\n".join(f"  - {ruta}" for ruta in faltantes)
        raise FileNotFoundError(
            "No se encontraron los DEM de entrada. Verifica esta estructura:\n"
            f"{DATOS_DIR}\n"
            f"Archivos faltantes:\n{detalle}"
        )

    modulo = BASE_DIR / "analisis_morfologico.py"
    if not modulo.is_file():
        raise FileNotFoundError(
            "No se encontró analisis_morfologico.py. Coloca ese archivo junto a "
            "graficos_terrarover.py y conserva allá tus funciones originales."
        )


def localizar_mapa_diferencias() -> Path | None:
    """Busca el TIFF de diferencias en las ubicaciones habituales."""
    candidatos = (
        DIFERENCIAS_PATH,
        BASE_DIR / "mapa_diferencias.tiff",
        DATOS_DIR / "mapa_diferencias.tiff",
        RESULTADOS_DIR / "mapa_diferencias.tif",
        BASE_DIR / "mapa_diferencias.tif",
        DATOS_DIR / "mapa_diferencias.tif",
    )
    for candidato in candidatos:
        if candidato.is_file():
            return candidato
    return None


def leer_raster_para_grafico(ruta: Path):
    """Lee un raster para dibujarlo; no altera los datos usados por el análisis."""
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encontró el archivo: {ruta}")

    with rasterio.open(ruta) as src:
        alto_original, ancho_original = src.height, src.width
        factor = min(
            1.0,
            MAX_DIMENSION_VISUALIZACION / max(alto_original, ancho_original),
        )
        alto_visual = max(1, int(round(alto_original * factor)))
        ancho_visual = max(1, int(round(ancho_original * factor)))

        # El remuestreo se usa solo para acelerar la representaciÃ³n grÃ¡fica.
        # Los archivos fuente y los cÃ¡lculos matemÃ¡ticos no se modifican.
        raster = src.read(
            1,
            masked=True,
            out_shape=(alto_visual, ancho_visual),
            resampling=Resampling.average,
        )
        raster = np.ma.masked_invalid(raster)

        limites = (
            src.bounds.left,
            src.bounds.right,
            src.bounds.bottom,
            src.bounds.top,
        )
        crs = str(src.crs) if src.crs else "CRS no definido"
        resolucion = src.res
        unidades = src.units or ()
        unidad = unidades[0] if unidades and unidades[0] else "unidades del raster"
        forma_original = (alto_original, ancho_original)

    return raster, limites, crs, resolucion, unidad, forma_original


def valores_validos(raster: np.ma.MaskedArray) -> np.ndarray:
    """Devuelve valores finitos y no enmascarados para histogramas."""
    if np.ma.isMaskedArray(raster):
        valores = np.asarray(raster.compressed(), dtype=np.float64)
    else:
        valores = np.asarray(raster, dtype=np.float64).ravel()
    return valores[np.isfinite(valores)]


def limitar_muestra(valores: np.ndarray, maximo: int) -> np.ndarray:
    """Reduce de forma determinista el número de puntos usados en histogramas."""
    if valores.size <= maximo:
        return valores
    indices = np.linspace(0, valores.size - 1, num=maximo, dtype=np.int64)
    return valores[indices]


def guardar_figura(figura: plt.Figure, destino: Path) -> Path:
    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)
    figura.savefig(destino, dpi=DPI_FIGURAS, bbox_inches="tight", facecolor=COLOR_FONDO)
    plt.close(figura)
    print(f"[OK] Figura guardada: {destino}")
    return destino


def json_compatible(objeto: Any) -> Any:
    """Convierte escalares NumPy y estructuras simples a tipos serializables."""
    if isinstance(objeto, dict):
        return {str(k): json_compatible(v) for k, v in objeto.items()}
    if isinstance(objeto, (list, tuple)):
        return [json_compatible(v) for v in objeto]
    if isinstance(objeto, np.generic):
        return objeto.item()
    if isinstance(objeto, (np.ndarray,)):
        return objeto.tolist()
    if isinstance(objeto, (Path,)):
        return str(objeto)
    return objeto


# ---------------------------------------------------------------------------
# 3. GRÃFICOS ESPACIALES
# ---------------------------------------------------------------------------
def crear_graficos_espaciales() -> tuple[Path, Path | None]:
    """Genera mapas DEM, mapa de diferencias si existe e histogramas."""
    dem_a, extent_a, crs_a, res_a, unidad_a, forma_a = leer_raster_para_grafico(DEM_A_PATH)
    dem_b, extent_b, crs_b, res_b, unidad_b, forma_b = leer_raster_para_grafico(DEM_B_PATH)

    ruta_diferencias = localizar_mapa_diferencias()
    if ruta_diferencias is not None:
        diferencias, extent_d, crs_d, res_d, unidad_d, forma_d = leer_raster_para_grafico(
            ruta_diferencias
        )
    else:
        diferencias = None
        extent_d = crs_d = res_d = unidad_d = forma_d = None
        print(
            "[AVISO] No se encontró mapa_diferencias.tiff. Se generarÃ¡ la figura "
            "espacial sin ese mapa. Ejecuta primero analisis_diferencias.py para incluirlo."
        )

    valores_a = limitar_muestra(valores_validos(dem_a), MAX_MUESTRAS_HISTOGRAMA)
    valores_b = limitar_muestra(valores_validos(dem_b), MAX_MUESTRAS_HISTOGRAMA)

    fig, axes = plt.subplots(2, 2, figsize=(15, 10), constrained_layout=True)
    fig.patch.set_facecolor(COLOR_FONDO)
    fig.suptitle(
        "COMPARACIóN ESPACIAL DE TERRENOS",
        fontsize=16,
        fontweight="bold",
        color=COLOR_TEXTO,
    )

    # Usar una escala comÃºn cuando ambas bandas declaran las mismas unidades.
    misma_unidad = unidad_a == unidad_b
    if misma_unidad and valores_a.size and valores_b.size:
        vmin = float(min(np.min(valores_a), np.min(valores_b)))
        vmax = float(max(np.max(valores_a), np.max(valores_b)))
        if np.isclose(vmin, vmax):
            vmax = vmin + 1.0
    else:
        vmin = vmax = None

    im_a = axes[0, 0].imshow(
        dem_a,
        cmap="terrain",
        extent=extent_a,
        origin="upper",
        vmin=vmin,
        vmax=vmax,
        interpolation="nearest",
    )
    axes[0, 0].set_title("DEM A | Terreno terrestre", fontweight="bold")
    axes[0, 0].set_xlabel("Coordenada X")
    axes[0, 0].set_ylabel("Coordenada Y")
    fig.colorbar(im_a, ax=axes[0, 0], label=f"ElevaciÃ³n ({unidad_a})", shrink=0.86)

    im_b = axes[0, 1].imshow(
        dem_b,
        cmap="terrain",
        extent=extent_b,
        origin="upper",
        vmin=vmin,
        vmax=vmax,
        interpolation="nearest",
    )
    axes[0, 1].set_title("DEM B | Terreno de referencia", fontweight="bold")
    axes[0, 1].set_xlabel("Coordenada X")
    axes[0, 1].set_ylabel("Coordenada Y")
    fig.colorbar(im_b, ax=axes[0, 1], label=f"Elevación ({unidad_b})", shrink=0.86)

    if diferencias is not None:
        im_d = axes[1, 0].imshow(
            diferencias,
            cmap="inferno",
            extent=extent_d,
            origin="upper",
            interpolation="nearest",
        )
        axes[1, 0].set_title("Mapa de diferencias", fontweight="bold")
        axes[1, 0].set_xlabel("Coordenada X")
        axes[1, 0].set_ylabel("Coordenada Y")
        fig.colorbar(
            im_d,
            ax=axes[1, 0],
            label=f"Magnitud de diferencia ({unidad_d})",
            shrink=0.86,
        )
    else:
        axes[1, 0].set_facecolor("#F2F5F9")
        axes[1, 0].text(
            0.5,
            0.55,
            "MAPA DE DIFERENCIAS NO DISPONIBLE",
            ha="center",
            va="center",
            transform=axes[1, 0].transAxes,
            fontsize=10,
            fontweight="bold",
            color=COLOR_TEXTO,
        )
        axes[1, 0].text(
            0.5,
            0.42,
            "Ejecuta analisis_diferencias.py\npara generar mapa_diferencias.tiff",
            ha="center",
            va="center",
            transform=axes[1, 0].transAxes,
            fontsize=9,
            color=COLOR_SECUNDARIO,
        )
        axes[1, 0].set_xticks([])
        axes[1, 0].set_yticks([])
        for borde in axes[1, 0].spines.values():
            borde.set_visible(False)

    ax_hist = axes[1, 1]
    if valores_a.size and valores_b.size and misma_unidad:
        minimo = float(min(np.min(valores_a), np.min(valores_b)))
        maximo = float(max(np.max(valores_a), np.max(valores_b)))
        if np.isclose(minimo, maximo):
            maximo = minimo + 1.0
        bins = np.linspace(minimo, maximo, NUM_BINS_HISTOGRAMA + 1)
        ax_hist.hist(
            valores_a,
            bins=bins,
            density=True,
            alpha=0.48,
            color=COLOR_A,
            label="DEM A",
        )
        ax_hist.hist(
            valores_b,
            bins=bins,
            density=True,
            alpha=0.48,
            color=COLOR_B,
            label="DEM B",
        )
        ax_hist.set_title("Distribución de elevaciones", fontweight="bold")
        ax_hist.set_xlabel(f"Elevación ({unidad_a})")
        ax_hist.set_ylabel("Densidad")
        ax_hist.legend(frameon=False)
        ax_hist.grid(axis="y", alpha=0.2)
        ax_hist.set_axisbelow(True)
    elif valores_a.size and valores_b.size:
        ax_hist.text(
            0.5,
            0.5,
            "No se superponen los histogramas:\nlas unidades declaradas son distintas.",
            ha="center",
            va="center",
            transform=ax_hist.transAxes,
            color=COLOR_SECUNDARIO,
        )
        ax_hist.set_axis_off()
    else:
        ax_hist.text(
            0.5,
            0.5,
            "No hay suficientes valores válidos\npara construir los histogramas.",
            ha="center",
            va="center",
            transform=ax_hist.transAxes,
            color=COLOR_SECUNDARIO,
        )
        ax_hist.set_axis_off()

    metadatos = (
        f"CRS A: {crs_a} | CRS B: {crs_b} | "
        f"Resolución A: {res_a} | ResoluciÃ³n B: {res_b} | "
        f"Dimensiones originales A/B: {forma_a}/{forma_b}"
    )
    if diferencias is not None:
        metadatos += f" | CRS diferencias: {crs_d} | Resolución diferencias: {res_d}"
    fig.text(0.01, -0.015, metadatos, fontsize=7.5, color=COLOR_SECUNDARIO)

    salida = RESULTADOS_DIR / "comparacion_espacial.png"
    guardar_figura(fig, salida)
    return salida, ruta_diferencias


# ---------------------------------------------------------------------------
# 4. GRÃFICOS MORFOLÃ“GICOS: REUTILIZA LAS FUNCIONES MATEMÃTICAS EXISTENTES
# ---------------------------------------------------------------------------
def crear_grafico_morfologico() -> tuple[Path, float, dict[str, Any], dict[str, Any]]:
    try:
        from analisis_morfologico import calc_analog
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar calc_analog desde analisis_morfologico.py. "
            "Coloca ese archivo junto a graficos_terrarover.py y conserva allÃ­ "
            "las funciones originales extrac_perfil_morf() y calc_analog()."
        ) from exc

    # Se llama a la implementaciÃ³n matemÃ¡tica ya existente. No se redefinen fÃ³rmulas.
    similitud, perfil_a, perfil_b = calc_analog(str(DEM_A_PATH), str(DEM_B_PATH))
    similitud = float(similitud)

    claves = list(NOMBRES_METRICAS.keys())
    faltantes_a = [clave for clave in claves if clave not in perfil_a]
    faltantes_b = [clave for clave in claves if clave not in perfil_b]
    if faltantes_a or faltantes_b:
        raise KeyError(
            "Faltan indicadores en los perfiles devueltos por calc_analog(). "
            f"DEM A: {faltantes_a or 'ninguno'}; DEM B: {faltantes_b or 'ninguno'}. "
            "Comprueba que las claves coincidan con analisis_morfologico.py."
        )

    fig, axes = plt.subplots(4, 2, figsize=(14, 13), constrained_layout=True)
    fig.patch.set_facecolor(COLOR_FONDO)
    axes_flat = axes.ravel()
    fig.suptitle(
        "COMPARACIÓN MORFOLÓGICA",
        fontsize=16,
        fontweight="bold",
        color=COLOR_TEXTO,
    )

    for indice, clave in enumerate(claves):
        ax = axes_flat[indice]
        valor_a = float(perfil_a[clave])
        valor_b = float(perfil_b[clave])
        if not np.isfinite(valor_a) or not np.isfinite(valor_b):
            ax.text(
                0.5,
                0.5,
                "Indicador no finito\n(revisar resultado de origen)",
                ha="center",
                va="center",
                transform=ax.transAxes,
                color=COLOR_SECUNDARIO,
            )
            ax.set_title(NOMBRES_METRICAS[clave], fontsize=9, fontweight="bold")
            ax.set_axis_off()
            continue

        barras = ax.barh(
            ["DEM A", "DEM B"],
            [valor_a, valor_b],
            color=[COLOR_A, COLOR_B],
            height=0.55,
        )
        ax.axvline(0, color="#6B7788", linewidth=0.8)
        ax.set_title(NOMBRES_METRICAS[clave], fontsize=9.5, fontweight="bold")
        ax.grid(axis="x", alpha=0.20)
        ax.set_axisbelow(True)
        ax.tick_params(axis="both", labelsize=8)

        limite_min = min(0.0, valor_a, valor_b)
        limite_max = max(0.0, valor_a, valor_b)
        amplitud = limite_max - limite_min
        margen = amplitud * 0.18 if amplitud > 0 else max(abs(limite_max) * 0.18, 0.1)
        ax.set_xlim(limite_min - margen, limite_max + margen)

        for barra, valor in zip(barras, (valor_a, valor_b)):
            desplazamiento = 4 if valor >= 0 else -4
            alineacion = "left" if valor >= 0 else "right"
            ax.annotate(
                f"{valor:.5g}",
                (valor, barra.get_y() + barra.get_height() / 2),
                xytext=(desplazamiento, 0),
                textcoords="offset points",
                ha=alineacion,
                va="center",
                fontsize=8,
            )

    # El octavo panel se usa como indicador visual, no recalcula la similitud.
    ax_kpi = axes_flat[-1]
    ax_kpi.set_facecolor("#F2F6FA")
    ax_kpi.text(
        0.5,
        0.72,
        "SIMILITUD COSENO",
        ha="center",
        va="center",
        transform=ax_kpi.transAxes,
        fontsize=11,
        fontweight="bold",
        color=COLOR_SECUNDARIO,
    )
    ax_kpi.text(
        0.5,
        0.48,
        f"{similitud:.6f}",
        ha="center",
        va="center",
        transform=ax_kpi.transAxes,
        fontsize=24,
        fontweight="bold",
        color=COLOR_TEXTO,
    )
    ax_kpi.text(
        0.5,
        0.22,
        "Valor devuelto por calc_analog()\nNo constituye por sí solo una validación física.",
        ha="center",
        va="center",
        transform=ax_kpi.transAxes,
        fontsize=8,
        color=COLOR_SECUNDARIO,
    )
    ax_kpi.set_xticks([])
    ax_kpi.set_yticks([])
    for borde in ax_kpi.spines.values():
        borde.set_visible(False)

    salida = RESULTADOS_DIR / "comparacion_morfologica.png"
    guardar_figura(fig, salida)
    return salida, similitud, perfil_a, perfil_b


# ---------------------------------------------------------------------------
# 5. GUARDAR RESUMEN DE RESULTADOS PARA TRAZABILIDAD
# ---------------------------------------------------------------------------
def guardar_resumen_resultados(
    similitud: float,
    perfil_a: dict[str, Any],
    perfil_b: dict[str, Any],
    ruta_diferencias: Path | None,
) -> Path:
    resumen = {
        "proyecto": "TerraRover",
        "fecha_generacion_utc": datetime.now(timezone.utc).isoformat(),
        "dem_a": str(DEM_A_PATH),
        "dem_b": str(DEM_B_PATH),
        "mapa_diferencias": str(ruta_diferencias) if ruta_diferencias else None,
        "mapa_diferencias_disponible": ruta_diferencias is not None,
        "similitud_coseno_devuelta_por_calc_analog": similitud,
        "perfil_dem_a": perfil_a,
        "perfil_dem_b": perfil_b,
        "nota": (
            "Los indicadores y la similitud proceden de analisis_morfologico.py. "
            "Este archivo solo organiza resultados para visualización y reporte."
        ),
    }
    salida = RESULTADOS_DIR / "resumen_analisis.json"
    salida.write_text(
        json.dumps(json_compatible(resumen), ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    print(f"[OK] Resumen JSON guardado: {salida}")
    return salida


# ---------------------------------------------------------------------------
# 6. INTERPRETACIÃ“N OPCIONAL CON AMD TOKENLAB (MODELO VISION)
# ---------------------------------------------------------------------------
def imagen_como_data_url(ruta: Path) -> str:
    """Codifica una imagen PNG/JPEG en una data URL para la API."""
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe la imagen que se enviarÃ¡ a la IA: {ruta}")

    extension = ruta.suffix.lower()
    tipos_mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}
    mime = tipos_mime.get(extension)
    if mime is None:
        raise ValueError(f"Formato de imagen no admitido para TokenLab: {extension}")

    encoded = base64.b64encode(ruta.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def interpretar_con_amd(
    grafico_espacial: Path,
    grafico_morfologico: Path,
    similitud: float,
    perfil_a: dict[str, Any],
    perfil_b: dict[str, Any],
    mapa_diferencias_disponible: bool,
) -> Path:
    """EnvÃ­a dos grÃ¡ficos y el resumen al VLM mediante el SDK OpenAI-compatible."""
    if not AMD_API_KEY:
        raise RuntimeError(
            "Falta AMD_API_KEY. Añádela al archivo .env ubicado junto a "
            "graficos_terrarover.py."
        )

    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI
    except ImportError as exc:
        raise ImportError(
            "Falta el paquete openai. Instálalo con: pip install openai"
        ) from exc

    resumen = {
        "similitud_coseno_devuelta_por_calc_analog": similitud,
        "perfil_dem_a": perfil_a,
        "perfil_dem_b": perfil_b,
        "mapa_de_diferencias_disponible": mapa_diferencias_disponible,
    }

    instruccion = (
        "Actúa como asistente de interpretación visual para el proyecto TerraRover. "
        "Analiza las dos imágenes adjuntas y los indicadores numéricos proporcionados. "
        "Describe únicamente los patrones que puedan observarse, las diferencias "
        "destacadas y los aspectos que merecen revisión. No recalcules, corrijas ni "
        "sustituyas las métricas. No inventes datos, unidades, ubicaciones ni condiciones "
        "geológicas. Distingue observaciones visuales de interpretaciones. No afirmes "
        "equivalencia física entre terrenos ni transitabilidad de una ruta basándote "
        "solo en similitud morfológica. Recuerda que un DEM no describe por sí mismo "
        "granulometría, cohesión, fricción ni resistencia mecánica del suelo. "
        "Si el gráfico indica que el mapa de diferencias no está disponible, no describas "
        "ni infieras sus patrones. Responde en español, con títulos breves y lenguaje "
        "científico comprensible.\n\n"

        "Realiza un análisis comparativo entre las dos imágenes, priorizando las "
        "semejanzas, diferencias y relaciones observables entre ambas. No te limites "
        "a describir cada imagen de manera independiente. La comparación debe ser "
        "el eje central del análisis.\n\n"

        "Compara directamente los patrones morfológicos, la distribución de elevaciones, "
        "las pendientes, las irregularidades y demás características topográficas "
        "visibles en ambas imágenes, siempre que estén representadas.\n\n"

        "Identifica qué características son similares, cuáles presentan diferencias "
        "destacadas y dónde se concentran los cambios más relevantes. Explica qué "
        "significan estas diferencias desde el punto de vista de la interpretación "
        "del terreno, distinguiendo claramente entre observaciones visuales "
        "e interpretaciones.\n\n"

        "Organiza el análisis de la siguiente manera:\n"
        "1. Comparación general: semejanzas y diferencias principales entre ambos terrenos.\n"
        "2. Análisis de patrones: comparación de las características morfológicas y topográficas.\n"
        "3. Diferencias destacadas: identificación y explicación de los contrastes más relevantes.\n"
        "4. Interpretación conjunta: conclusiones que permiten obtener las similitudes "
        "y diferencias observadas.\n"
        "5. Aspectos que requieren revisión: anomalías, limitaciones o elementos "
        "que no pueden determinarse únicamente mediante las imágenes y métricas disponibles.\n\n"

        "Evita repetir descripciones individuales que no aporten información comparativa. "
        "No establezcas conclusiones que excedan la información disponible.\n\n"

        "Indicadores calculados por las funciones originales del proyecto:\n"

        f"{json.dumps(json_compatible(resumen), ensure_ascii=False, indent=2)}"
    )

    # Se utiliza el mismo patrÃ³n que el ejemplo oficial de Python compartido:
    # OpenAI(base_url='https://api.tokenlab.amd.com/v1', api_key=...)
    # y client.chat.completions.create(model=..., messages=...).
    client = OpenAI(
        base_url=AMD_BASE_URL.rstrip("/"),
        api_key=AMD_API_KEY,
        timeout=180.0,
        max_retries=2,
    )

    mensajes = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": instruccion},
                {
                    "type": "image_url",
                    "image_url": {"url": imagen_como_data_url(grafico_espacial)},
                },
                {
                    "type": "image_url",
                    "image_url": {"url": imagen_como_data_url(grafico_morfologico)},
                },
            ],
        }
    ]

    print(
        f"[INFO] Enviando gráficos a AMD TokenLab | Modelo: {AMD_MODEL} | "
        f"Base URL: {AMD_BASE_URL}"
    )

    try:
        parametros_solicitud = {
            "model": AMD_MODEL,
            "messages": mensajes,
            "max_tokens": 1200,
        }
        # Qwen3.8-27B documenta reasoning_effort="low". No se envÃ­a este
        # parÃ¡metro a otros VLM (por ejemplo Gemma), cuya configuraciÃ³n difiere.
        if AMD_MODEL.strip().lower() == "qwen3.8-27b":
            parametros_solicitud["reasoning_effort"] = "low"

        respuesta = client.chat.completions.create(**parametros_solicitud)
    except APIStatusError as exc:
        estado = getattr(exc, "status_code", "desconocido")
        detalle = str(exc)
        if estado == 429:
            raise RuntimeError(
                f"TokenLab respondió HTTP 429 para el modelo {AMD_MODEL}. "
                "El endpoint está limitando temporalmente la solicitud o la "
                "concurrencia. Espera un momento o prueba otro VLM habilitado "
                "(por ejemplo, Gemma-4-31B-IT). Detalle: " + detalle
            ) from exc
        if estado == 404:
            raise RuntimeError(
                f"TokenLab respondió HTTP 404: el modelo '{AMD_MODEL}' no está "
                "disponible con ese identificador en este endpoint. Comprueba el "
                "identificador de API en TokenLab. Detalle: " + detalle
            ) from exc
        raise RuntimeError(f"TokenLab respondiÃ³ HTTP {estado}: {detalle}") from exc
    except APITimeoutError as exc:
        raise RuntimeError(
            "La solicitud a TokenLab agotá el tiempo de espera. Los gráficos ya "
            "fueron generados; vuelve a intentar la interpretación más tarde."
        ) from exc
    except APIConnectionError as exc:
        raise RuntimeError(
            f"No se pudo establecer conexión con AMD TokenLab: {exc}"
        ) from exc
    except Exception as exc:
        raise RuntimeError(
            f"Error al solicitar la interpretación visual a TokenLab: {exc}"
        ) from exc

    contenido = respuesta.choices[0].message.content
    if isinstance(contenido, str):
        texto = contenido.strip()
    elif isinstance(contenido, list):
        fragmentos = []
        for parte in contenido:
            if isinstance(parte, dict):
                texto_parte = parte.get("text")
            else:
                texto_parte = getattr(parte, "text", None)
            if texto_parte:
                fragmentos.append(str(texto_parte))
        texto = "\n".join(fragmentos).strip()
    else:
        texto = str(contenido or "").strip()

    if not texto:
        raise RuntimeError(
            "TokenLab respondió correctamente, pero el contenido del modelo llegá vacío."
        )

    salida = RESULTADOS_DIR / "interpretacion_ia.md"
    salida.write_text(texto + "\n", encoding="utf-8")
    print(f"[OK] Interpretación de IA guardada: {salida}")
    return salida


# ---------------------------------------------------------------------------
# 7. EJECUCIÃ“N PRINCIPAL
# ---------------------------------------------------------------------------
def main() -> int:
    RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        comprobar_entradas_principales()

        print("\n========== GENERACIÓN DE VISUALIZACIONES ==========")
        print(f"[INFO] DEM A: {DEM_A_PATH}")
        print(f"[INFO] DEM B: {DEM_B_PATH}")

        grafico_espacial, ruta_diferencias = crear_graficos_espaciales()
        grafico_morfologico, similitud, perfil_a, perfil_b = crear_grafico_morfologico()
        resumen_path = guardar_resumen_resultados(
            similitud,
            perfil_a,
            perfil_b,
            ruta_diferencias,
        )

        print("\n[OK] Visualizaciones generadas correctamente.")
        print(f"[RESULTADO] Similitud coseno devuelta por calc_analog(): {similitud:.6f}")
        print(f"[ARCHIVO] {grafico_espacial}")
        print(f"[ARCHIVO] {grafico_morfologico}")
        print(f"[ARCHIVO] {resumen_path}")

        if ENVIAR_A_IA:
            try:
                interpretar_con_amd(
                    grafico_espacial,
                    grafico_morfologico,
                    similitud,
                    perfil_a,
                    perfil_b,
                    mapa_diferencias_disponible=(ruta_diferencias is not None),
                )
            except Exception as exc:
                print(
                    "\n[ERROR IA] Los gráficos sí se generaron, pero no se pudo "
                    f"completar la interpretación con TokenLab: {exc}",
                    file=sys.stderr,
                )
                return 2
        else:
            print(
                "\n[INFO] Interpretación IA desactivada. Para activarla, configura "
                "ENVIAR_A_IA=true en el archivo .env."
            )

        if ruta_diferencias is None:
            print(
                "\n[AVISO] La figura espacial se generó sin el mapa de diferencias. "
                "Cuando ejecutes analisis_diferencias.py, vuelve a ejecutar este script."
            )

        return 0

    except Exception as exc:
        print(f"\n[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())