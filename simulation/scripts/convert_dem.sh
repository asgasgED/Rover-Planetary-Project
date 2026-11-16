#!/usr/bin/env bash

set -euo pipefail

# ==========================================
# TerraRover - DEM to Webots
# Conversor de GeoTIFF a mundo Webots
# ==========================================

# Directorio raíz del proyecto
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Parámetros
DEM_INPUT="${1:-}"
ROI_WIDTH="${2:-5000}"
ROI_HEIGHT="${3:-5000}"
TARGET_CRS="${4:-auto}"

# Comprobar archivo de entrada
if [[ -z "$DEM_INPUT" ]]; then
    echo "Uso:"
    echo "./scripts/convert_dem.sh archivo.tif [ancho_m] [alto_m] [CRS]"
    echo ""
    echo "Ejemplo:"
    echo "./scripts/convert_dem.sh terreno.tif 1000 1000"
    exit 1
fi

# Resolver ruta del DEM
if [[ "$DEM_INPUT" != /* ]]; then
    DEM_INPUT="$BASE_DIR/$DEM_INPUT"
fi

if [[ ! -f "$DEM_INPUT" ]]; then
    echo "[ERROR] No se encontró el archivo: $DEM_INPUT"
    exit 1
fi

# Seleccionar Python del entorno virtual
PYTHON="$BASE_DIR/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
    echo "[ERROR] No se encontró el entorno virtual .venv"
    exit 1
fi

CONVERTER="$BASE_DIR/scripts/dem_converter/dem_to_webots.py"

echo "=========================================="
echo "         TERRAROVER DEM CONVERTER"
echo "=========================================="
echo "DEM:       $DEM_INPUT"
echo "ROI:       ${ROI_WIDTH} x ${ROI_HEIGHT} m"
echo "CRS:       $TARGET_CRS"
echo "=========================================="

ARGS=(
    --input "$DEM_INPUT"
    --roi-width-m "$ROI_WIDTH"
    --roi-height-m "$ROI_HEIGHT"
)

# Si no se especifica CRS, el conversor lo selecciona automáticamente
if [[ "$TARGET_CRS" != "auto" ]]; then
    ARGS+=(--target-crs "$TARGET_CRS")
fi

# Ejecutar conversión
"$PYTHON" "$CONVERTER" "${ARGS[@]}"

echo ""
echo "[OK] Conversión finalizada."
echo "Busca el mundo generado en:"
echo "$BASE_DIR/worlds/"
