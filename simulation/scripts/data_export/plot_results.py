#!/usr/bin/env python3
"""
TerraRover - Módulo: Data Export & Visualization (Fase 5)
Equipo: Killa Coders | NASA Space Apps Challenge 2026
"""

import argparse
import csv
import json
import site
import sys
from pathlib import Path

# Asegurar rutas de paquetes de usuario (~/.local/lib/pythonX.Y/site-packages)
user_site = site.getusersitepackages()
if user_site and user_site not in sys.path:
    site.addsitedir(user_site); sys.path.append("/usr/lib/python3/dist-packages")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def generate_report_plot(json_path: Path):
    data = json.loads(json_path.read_text(encoding="utf-8"))
    csv_path = Path(data["artifacts"]["csv"])
    plot_path = Path(data["artifacts"]["plot"])

    times, xs, ys, speeds, rolls, pitches, slopes, stalls = [], [], [], [], [], [], [], []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            times.append(float(row["time_sec"]))
            xs.append(float(row["x"]))
            ys.append(float(row["y"]))
            speeds.append(float(row["speed_ms"]))
            rolls.append(float(row["roll_deg"]))
            pitches.append(float(row["pitch_deg"]))
            slopes.append(float(row["slope_deg"]))
            stalls.append(int(row["stall_flag"]))

    if not times:
        print("[PlotResults] CSV vacío, no se generó gráfico.")
        return

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), dpi=150)
    fig.suptitle(
        f"TerraRover Traversability Report — Terrain: {data['terrain']} | "
        f"Status: {data['simulation_status'].upper()} ({data['route_completion']}%)",
        fontsize=12,
        fontweight="bold",
    )

    ax1 = axes[0]
    sc = ax1.scatter(xs, ys, c=speeds, cmap="viridis", s=16, label="Trayectoria")
    ax1.plot(xs[0], ys[0], "go", markersize=9, label="Inicio")
    ax1.plot(xs[-1], ys[-1], "r*", markersize=12, label="Fin")
    stall_x = [xs[i] for i, s in enumerate(stalls) if s == 1]
    stall_y = [ys[i] for i, s in enumerate(stalls) if s == 1]
    if stall_x:
        ax1.scatter(stall_x, stall_y, color="red", marker="x", s=45, label="Atasco")
    ax1.set_title("Trayectoria 2D y Velocidad")
    ax1.set_xlabel("X [m]")
    ax1.set_ylabel("Y [m]")
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.legend(loc="best", fontsize=8)
    cbar = fig.colorbar(sc, ax=ax1)
    cbar.set_label("Velocidad [m/s]")

    ax2 = axes[1]
    ax2.plot(times, slopes, color="#d95f02", linewidth=1.6, label="Inclinación total [°]")
    ax2.axhline(
        data["maximum_slope"],
        color="#1b9e77",
        linestyle="--",
        linewidth=1.2,
        label=f"Máx. superada ({data['maximum_slope']}°)",
    )
    ax2.set_title("Perfil de Pendiente Superada")
    ax2.set_xlabel("Tiempo [s]")
    ax2.set_ylabel("Ángulo [grados]")
    ax2.grid(True, linestyle="--", alpha=0.4)
    ax2.legend(loc="best", fontsize=8)

    ax3 = axes[2]
    ax3.plot(times, rolls, color="#7570b3", linewidth=1.4, label="Roll (Alabeo) [°]")
    ax3.plot(times, pitches, color="#e7298a", linewidth=1.4, label="Pitch (Cabeceo) [°]")
    ax3.axhline(32.0, color="red", linestyle=":", linewidth=1.1, label="Umbral crítico (±32°)")
    ax3.axhline(-32.0, color="red", linestyle=":", linewidth=1.1)
    ax3.set_title("Dinámica de Estabilidad (Roll / Pitch)")
    ax3.set_xlabel("Tiempo [s]")
    ax3.set_ylabel("Ángulo [grados]")
    ax3.grid(True, linestyle="--", alpha=0.4)
    ax3.legend(loc="best", fontsize=8)

    plt.tight_layout()
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(plot_path)
    plt.close(fig)
    print(f"[PlotResults] Gráfico PNG generado: {plot_path}")


def main():
    parser = argparse.ArgumentParser(description="Genera gráficos PNG de resultados TerraRover.")
    parser.add_argument("--json", type=Path, required=True, help="Ruta al archivo *_results.json")
    args = parser.parse_args()
    generate_report_plot(args.json.resolve())


if __name__ == "__main__":
    main()
