#!/usr/bin/env bash
# ==============================================================================
# TerraRover - Orquestador de Evaluación de Transitabilidad (Fase 6)
# Equipo: Killa Coders | NASA Space Apps Challenge 2026
# Uso:
#   ./scripts/run_terrarover_eval.sh [ruta_al_dem.tif] [pixel_size_m] [goal_x] [goal_y]
# Ejemplo sin argumentos (usa DEM análogo de prueba):
#   ./scripts/run_terrarover_eval.sh
# ==============================================================================
set -e

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEM_INPUT="${1:-}"
PIXEL_SIZE="${2:-0.25}"
GOAL_X="${3:-17.0}"
GOAL_Y="${4:-10.0}"

echo "=========================================================="
echo " TERRAROVER - Pipeline de Evaluación Robótica"
echo "=========================================================="

if [ -z "$DEM_INPUT" ]; then
    echo "[1/3] Generando y convirtiendo DEM análogo de prueba..."
    python3 "$BASE_DIR/scripts/dem_converter/dem_to_webots.py" \
        --generate-sample --pixel-size "$PIXEL_SIZE" --goal-x "$GOAL_X" --goal-y "$GOAL_Y"
    TERRAIN_NAME="sample_analog_dem"
else
    echo "[1/3] Convirtiendo DEM externo: $DEM_INPUT..."
    python3 "$BASE_DIR/scripts/dem_converter/dem_to_webots.py" \
        --input "$DEM_INPUT" --pixel-size "$PIXEL_SIZE" --goal-x "$GOAL_X" --goal-y "$GOAL_Y"
    TERRAIN_NAME="$(basename "${DEM_INPUT%.*}")"
fi

WORLD_FILE="$BASE_DIR/worlds/dem_${TERRAIN_NAME}.wbt"
JSON_FILE="$BASE_DIR/results/json/${TERRAIN_NAME}_results.json"

echo "[2/3] Ejecutando simulación física en Webots (modo rápido)..."
echo "      (Cierra Webots cuando la consola muestre '¡Meta alcanzada!')"
webots --mode=fast "$WORLD_FILE"

echo "[3/3] Generando reporte gráfico PNG y verificando resultados..."
if [ -f "$JSON_FILE" ]; then
    python3 "$BASE_DIR/scripts/data_export/plot_results.py" --json "$JSON_FILE"
    echo "=========================================================="
    echo " RESULTADOS EXPORTADOS PARA PLATAFORMA TERRAROVER:"
    cat "$JSON_FILE"
    echo "=========================================================="
else
    echo "[ERROR] No se generó $JSON_FILE. Verifica que la simulación haya completado."
    exit 1
fi
