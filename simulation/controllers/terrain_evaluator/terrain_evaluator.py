"""
TerraRover - Módulo: Terrain Evaluator (Fase 5)
Equipo: Killa Coders | NASA Space Apps Challenge 2026
Descripción:
    Controlador Supervisor en Webots encargado de medir en tiempo real el
    desempeño físico del rover Sojourner sobre cualquier terreno (artificial o DEM),
    detectar atascos reales y pérdida de estabilidad, y exportar métricas
    cuantitativas en formatos JSON, CSV y gráficos PNG.
"""

import csv
import json
import math
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from controller import Supervisor


def rotation_matrix_to_rpy(R: list) -> tuple:
    r11, r12, r13 = R[0], R[1], R[2]
    r21, r22, r23 = R[3], R[4], R[5]
    r31, r32, r33 = R[6], R[7], R[8]

    pitch = math.asin(max(-1.0, min(1.0, -r31)))
    if abs(math.cos(pitch)) > 1e-6:
        roll = math.atan2(r32, r33)
        yaw = math.atan2(r21, r11)
    else:
        roll = 0.0
        yaw = math.atan2(-r12, r22)

    return roll, pitch, yaw


class TerrainEvaluator:
    """Evalúa transitabilidad, estabilidad y eficiencia de recorrido del rover."""

    MAX_SAFE_ROLL_DEG = 32.0
    MAX_SAFE_PITCH_DEG = 35.0
    STALL_WINDOW_SEC = 5.0
    MIN_PROGRESS_IN_WINDOW_M = 0.008  # < 1.5 cm en 3.5 s (< 4.3 mm/s -> atasco real)
    RECOVERY_COOLDOWN_SEC = 13.0

    def __init__(
        self,
        supervisor: Supervisor,
        rover_def: str = "ROVER",
        terrain_name: str = "candidate_region_01",
        goal_xy: tuple = (17.0, 10.0),
        max_duration_sec: float = 480.0,
    ):
        self.sup = supervisor
        self.timestep = int(self.sup.getBasicTimeStep())
        self.dt = self.timestep / 1000.0
        self.terrain_name = terrain_name
        self.goal_x, self.goal_y = goal_xy
        self.max_duration_sec = max_duration_sec

        self.rover_node = self.sup.getFromDef(rover_def)
        if self.rover_node is None:
            raise RuntimeError(f"No se encontró el nodo DEF '{rover_def}' en el mundo Webots.")

        self.custom_data_field = self.rover_node.getField("customData")
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ros_bridge_addr = ("127.0.0.1", 9870)

        self.base_dir = Path(__file__).resolve().parents[2]
        self.csv_path = self.base_dir / "results" / "csv" / f"{terrain_name}_telemetry.csv"
        self.json_path = self.base_dir / "results" / "json" / f"{terrain_name}_results.json"
        self.plot_path = self.base_dir / "results" / "plots" / f"{terrain_name}_analysis.png"

        init_pos = self.rover_node.getPosition()
        self.start_x, self.start_y, self.start_z = init_pos[0], init_pos[1], init_pos[2]
        self.prev_x, self.prev_y, self.prev_z = self.start_x, self.start_y, self.start_z
        self.total_route_dist = max(0.01, math.hypot(self.goal_x - self.start_x, self.goal_y - self.start_y))

        self.elapsed_sec = 0.0
        self.distance_travelled = 0.0
        self.current_uninterrupted_dist = 0.0
        self.max_uninterrupted_dist = 0.0

        self.max_slope_climbed_deg = 0.0
        self.max_roll_deg = 0.0
        self.max_pitch_deg = 0.0

        self.stall_events = 0
        self.stability_loss_events = 0
        self.in_stall_state = False
        self.in_instability_state = False

        self.window_timer = 0.0
        self.window_start_pos = (self.start_x, self.start_y, self.start_z)
        self.cooldown_timer = 0.0

        self.telemetry_rows = []
        self.simulation_status = "running"

    def run(self):
        print("=========================================================")
        print(f"[TerrainEvaluator] Evaluando terreno: {self.terrain_name}")
        print(f"[TerrainEvaluator] Inicio: ({self.start_x:.2f}, {self.start_y:.2f}) -> Meta: ({self.goal_x:.2f}, {self.goal_y:.2f})")
        print("=========================================================")

        while self.sup.step(self.timestep) != -1:
            pos = self.rover_node.getPosition()
            vel = self.rover_node.getVelocity()
            rot = self.rover_node.getOrientation()

            x, y, z = pos[0], pos[1], pos[2]
            speed_3d = math.sqrt(vel[0] ** 2 + vel[1] ** 2 + vel[2] ** 2)
            roll_rad, pitch_rad, yaw_rad = rotation_matrix_to_rpy(rot)

            roll_deg = math.degrees(roll_rad)
            pitch_deg = math.degrees(pitch_rad)
            cos_tilt = max(-1.0, min(1.0, math.cos(roll_rad) * math.cos(pitch_rad)))
            slope_deg = math.degrees(math.acos(cos_tilt))

            step_dist = math.sqrt((x - self.prev_x) ** 2 + (y - self.prev_y) ** 2 + (z - self.prev_z) ** 2)
            self.distance_travelled += step_dist
            self.prev_x, self.prev_y, self.prev_z = x, y, z

            self.max_roll_deg = max(self.max_roll_deg, abs(roll_deg))
            self.max_pitch_deg = max(self.max_pitch_deg, abs(pitch_deg))
            if speed_3d > 0.012 and abs(roll_deg) < self.MAX_SAFE_ROLL_DEG and abs(pitch_deg) < self.MAX_SAFE_PITCH_DEG:
                self.max_slope_climbed_deg = max(self.max_slope_climbed_deg, slope_deg)

            # 1. Detección de pérdida de estabilidad
            is_unstable = (abs(roll_deg) > self.MAX_SAFE_ROLL_DEG) or (abs(pitch_deg) > self.MAX_SAFE_PITCH_DEG)
            if is_unstable and not self.in_instability_state:
                self.stability_loss_events += 1
                self.in_instability_state = True
                print(f"[t={self.elapsed_sec:5.1f}s] ALERTA ESTABILIDAD: roll={roll_deg:.1f}°, pitch={pitch_deg:.1f}°")
            elif not is_unstable:
                self.in_instability_state = False

            # 2. Detección de atasco real
            status_flag = "NAVIGATING"

            if self.cooldown_timer > 0.0:
                self.cooldown_timer -= self.dt
                self.window_timer = 0.0
                self.window_start_pos = (x, y, z)
                if self.cooldown_timer > (self.RECOVERY_COOLDOWN_SEC - 4.5):
                    status_flag = "RECOVER_STALL"
                else:
                    self.in_stall_state = False
            else:
                self.window_timer += self.dt
                if self.window_timer >= self.STALL_WINDOW_SEC:
                    net_disp = math.sqrt((x - self.window_start_pos[0])**2 + (y - self.window_start_pos[1])**2 + (z - self.window_start_pos[2])**2)
                    if net_disp < self.MIN_PROGRESS_IN_WINDOW_M and self.elapsed_sec > 4.0:
                        self.stall_events += 1
                        self.in_stall_state = True
                        self.current_uninterrupted_dist = 0.0
                        self.cooldown_timer = self.RECOVERY_COOLDOWN_SEC
                        status_flag = "RECOVER_STALL"
                        print(f"[t={self.elapsed_sec:5.1f}s] ATASCO REAL en ({x:.2f}, {y:.2f}) -> Maniobra de evasión")
                    else:
                        self.in_stall_state = False

                    self.window_timer = 0.0
                    self.window_start_pos = (x, y, z)

            if not self.in_stall_state:
                self.current_uninterrupted_dist += step_dist
                self.max_uninterrupted_dist = max(self.max_uninterrupted_dist, self.current_uninterrupted_dist)

            # 3. Progreso hacia la meta
            dist_to_goal = math.hypot(self.goal_x - x, self.goal_y - y)
            progress_pct = max(0.0, min(100.0, (1.0 - dist_to_goal / self.total_route_dist) * 100.0))

            if int(round(self.elapsed_sec / self.dt)) % 10 == 0:
                self.telemetry_rows.append({
                    "time_sec": round(self.elapsed_sec, 3),
                    "x": round(x, 4),
                    "y": round(y, 4),
                    "z": round(z, 4),
                    "speed_ms": round(speed_3d, 4),
                    "roll_deg": round(roll_deg, 2),
                    "pitch_deg": round(pitch_deg, 2),
                    "slope_deg": round(slope_deg, 2),
                    "uninterrupted_dist_m": round(self.current_uninterrupted_dist, 3),
                    "stall_flag": int(self.in_stall_state),
                    "instability_flag": int(self.in_instability_state),
                    "progress_pct": round(progress_pct, 2),
                })

            if dist_to_goal < 0.50:
                self.simulation_status = "completed"
                status_flag = "STOP"
                self.publish_state(x, y, yaw_rad, status_flag)
                print(f"[TerrainEvaluator] ¡Meta alcanzada en {self.elapsed_sec:.1f}s!")
                break

            if abs(roll_deg) > 65.0 or abs(pitch_deg) > 65.0:
                self.simulation_status = "aborted_rollover"
                status_flag = "STOP"
                self.publish_state(x, y, yaw_rad, status_flag)
                print(f"[TerrainEvaluator] Simulación abortada por vuelco en t={self.elapsed_sec:.1f}s")
                break

            if self.elapsed_sec >= self.max_duration_sec:
                self.simulation_status = "timeout_partial"
                status_flag = "STOP"
                self.publish_state(x, y, yaw_rad, status_flag)
                print(f"[TerrainEvaluator] Tiempo máximo ({self.max_duration_sec:.0f}s) alcanzado.")
                break

            self.publish_state(x, y, yaw_rad, status_flag)
            self.elapsed_sec += self.dt

        self.export_results(progress_pct)

    def publish_state(self, x: float, y: float, yaw: float, status: str):
        if self.custom_data_field is not None:
            self.custom_data_field.setSFString(f"{x:.4f},{y:.4f},{yaw:.4f},{status}")
        if self.telemetry_rows:
            payload = json.dumps({
                "terrain": self.terrain_name,
                "yaw_rad": round(yaw, 4),
                "status": status,
                **self.telemetry_rows[-1],
            }).encode("utf-8")
            try:
                self.udp_sock.sendto(payload, self.ros_bridge_addr)
            except OSError:
                pass

    def export_results(self, final_progress_pct: float):
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        self.json_path.parent.mkdir(parents=True, exist_ok=True)
        self.plot_path.parent.mkdir(parents=True, exist_ok=True)

        if self.telemetry_rows:
            with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(self.telemetry_rows[0].keys()))
                writer.writeheader()
                writer.writerows(self.telemetry_rows)

        avg_speed = self.distance_travelled / max(0.01, self.elapsed_sec)
        results = {
            "rover": "Sojourner",
            "terrain": self.terrain_name,
            "distance_travelled": round(self.distance_travelled, 3),
            "average_speed": round(avg_speed, 4),
            "elapsed_time_sec": round(self.elapsed_sec, 2),
            "maximum_slope": round(self.max_slope_climbed_deg, 2),
            "max_roll_deg": round(self.max_roll_deg, 2),
            "max_pitch_deg": round(self.max_pitch_deg, 2),
            "max_uninterrupted_distance": round(self.max_uninterrupted_dist, 3),
            "stall_events": self.stall_events,
            "stability_loss_events": self.stability_loss_events,
            "route_completion": round(100.0 if self.simulation_status == "completed" else final_progress_pct, 2),
            "simulation_status": self.simulation_status,
            "artifacts": {
                "csv": str(self.csv_path),
                "json": str(self.json_path),
                "plot": str(self.plot_path),
            },
        }

        self.json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"[TerrainEvaluator] JSON exportado: {self.json_path}")
        print(f"[TerrainEvaluator] CSV exportado : {self.csv_path}")

        print(f"[TerrainEvaluator] Para generar el gráfico PNG ejecuta:")
        print(f"  python3 {self.base_dir}/scripts/data_export/plot_results.py --json {self.json_path}")


def main():
    sup = Supervisor()
    terrain_name = sys.argv[1] if len(sys.argv) > 1 else "sample_analog_dem"
    goal_x = float(sys.argv[2]) if len(sys.argv) > 2 else 17.0
    goal_y = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
    max_dur = float(sys.argv[4]) if len(sys.argv) > 4 else 480.0

    evaluator = TerrainEvaluator(
        supervisor=sup,
        rover_def="ROVER",
        terrain_name=terrain_name,
        goal_xy=(goal_x, goal_y),
        max_duration_sec=max_dur,
    )
    evaluator.run()


if __name__ == "__main__":
    main()
