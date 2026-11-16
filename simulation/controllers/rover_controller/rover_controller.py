"""
TerraRover - Módulo: Rover Controller (Fases 2 y 5)
Equipo: Killa Coders | NASA Space Apps Challenge 2026
Descripción:
    Controlador cinemático y de tracción para el modelo NASA Sojourner en Webots.
    Gestiona los 6 motores de tracción independiente y los 4 actuadores de dirección
    (Ackermann doble y giro en el sitio), manteniendo libre la suspensión rocker-bogie.
"""

import math
import socket
import sys
from controller import Robot, Keyboard


class SojournerController:
    """Encapsula la cinemática y actuación del rover Sojourner de 6 ruedas."""

    DRIVE_MOTORS = [
        "FrontLeftWheel",
        "MiddleLeftWheel",
        "BackLeftWheel",
        "FrontRightWheel",
        "MiddleRightWheel",
        "BackRightWheel",
    ]

    STEER_MOTORS = [
        "FrontLeftArm",
        "FrontRightArm",
        "BackLeftArm",
        "BackRightArm",
    ]

    WHEEL_RADIUS = 0.065       # m (aprox. 13 cm de diámetro)
    MAX_WHEEL_SPEED = 0.6      # rad/s (~0.039 m/s lineal)
    MAX_STEER_ANGLE = 0.55     # rad (~31.5 grados)
    POINT_TURN_ANGLE = 0.72    # rad (~41.2 grados para rotación sobre su propio eje)

    def __init__(self, robot: Robot):
        self.robot = robot
        self.timestep = int(self.robot.getBasicTimeStep())

        self.wheels = {}
        for name in self.DRIVE_MOTORS:
            motor = self.robot.getDevice(name)
            if motor is None:
                raise RuntimeError(f"Motor de tracción no encontrado: {name}")
            motor.setPosition(float("inf"))
            motor.setVelocity(0.0)
            self.wheels[name] = motor

        self.arms = {}
        for name in self.STEER_MOTORS:
            motor = self.robot.getDevice(name)
            if motor is None:
                raise RuntimeError(f"Motor de dirección no encontrado: {name}")
            motor.setPosition(0.0)
            motor.setVelocity(1.5)
            self.arms[name] = motor

        self.speed_factor = 0.6
        self.is_commanding_drive = False

    def set_speed_factor(self, factor: float):
        self.speed_factor = max(0.1, min(1.0, factor))

    def stop(self):
        self.is_commanding_drive = False
        for motor in self.wheels.values():
            motor.setVelocity(0.0)
        for arm in self.arms.values():
            arm.setPosition(0.0)

    def set_motion(self, linear_norm: float, angular_norm: float, spin_in_place: bool = False):
        linear_norm = max(-1.0, min(1.0, linear_norm))
        angular_norm = max(-1.0, min(1.0, angular_norm))
        base_omega = linear_norm * self.MAX_WHEEL_SPEED * self.speed_factor
        self.is_commanding_drive = (abs(linear_norm) > 0.05) or (spin_in_place and abs(angular_norm) > 0.05)

        if spin_in_place and abs(angular_norm) > 0.05:
            angle = self.POINT_TURN_ANGLE
            self.arms["FrontLeftArm"].setPosition(-angle)
            self.arms["FrontRightArm"].setPosition(angle)
            self.arms["BackLeftArm"].setPosition(angle)
            self.arms["BackRightArm"].setPosition(-angle)

            spin_omega = angular_norm * (self.MAX_WHEEL_SPEED * 0.65) * self.speed_factor
            self.wheels["FrontLeftWheel"].setVelocity(-spin_omega)
            self.wheels["MiddleLeftWheel"].setVelocity(-spin_omega)
            self.wheels["BackLeftWheel"].setVelocity(-spin_omega)

            self.wheels["FrontRightWheel"].setVelocity(spin_omega)
            self.wheels["MiddleRightWheel"].setVelocity(spin_omega)
            self.wheels["BackRightWheel"].setVelocity(spin_omega)
            return

        steer_angle = angular_norm * self.MAX_STEER_ANGLE
        self.arms["FrontLeftArm"].setPosition(steer_angle)
        self.arms["FrontRightArm"].setPosition(steer_angle)
        self.arms["BackLeftArm"].setPosition(-steer_angle)
        self.arms["BackRightArm"].setPosition(-steer_angle)

        diff_ratio = 0.25 * angular_norm
        left_omega = base_omega * (1.0 - diff_ratio)
        right_omega = base_omega * (1.0 + diff_ratio)

        peak_omega = max(abs(left_omega), abs(right_omega))
        if peak_omega > self.MAX_WHEEL_SPEED:
            scale = self.MAX_WHEEL_SPEED / peak_omega
            left_omega *= scale
            right_omega *= scale

        self.wheels["FrontLeftWheel"].setVelocity(left_omega)
        self.wheels["MiddleLeftWheel"].setVelocity(left_omega)
        self.wheels["BackLeftWheel"].setVelocity(left_omega)

        self.wheels["FrontRightWheel"].setVelocity(right_omega)
        self.wheels["MiddleRightWheel"].setVelocity(right_omega)
        self.wheels["BackRightWheel"].setVelocity(right_omega)

    def move_forward(self, speed: float = 1.0):
        self.set_motion(abs(speed), 0.0)

    def move_backward(self, speed: float = 1.0):
        self.set_motion(-abs(speed), 0.0)

    def turn_left(self, speed: float = 0.8, turn_rate: float = 0.8):
        self.set_motion(speed, abs(turn_rate))

    def turn_right(self, speed: float = 0.8, turn_rate: float = 0.8):
        self.set_motion(speed, -abs(turn_rate))

    def spin_left(self, speed: float = 0.8):
        self.set_motion(0.0, abs(speed), spin_in_place=True)

    def spin_right(self, speed: float = 0.8):
        self.set_motion(0.0, -abs(speed), spin_in_place=True)


def run_manual_mode(robot: Robot, rover: SojournerController):
    keyboard = Keyboard()
    keyboard.enable(rover.timestep)

    print("=========================================================")
    print("[TerraRover] Controlador Sojourner iniciado (MODO MANUAL)")
    print("Haz clic en la vista 3D de Webots y usa:")
    print("  W / Flecha Arriba    : Avanzar")
    print("  S / Flecha Abajo     : Retroceder")
    print("  A / Flecha Izquierda : Girar a la izquierda")
    print("  D / Flecha Derecha   : Girar a la derecha")
    print("  Q / E                : Rotar sobre su eje (Izq / Der)")
    print("  1 / 2 / 3            : Velocidad Baja (30%) / Media (60%) / Alta (100%)")
    print("  ESPACIO              : Detener")
    print("=========================================================")

    while robot.step(rover.timestep) != -1:
        linear = 0.0
        angular = 0.0
        spin = False

        key = keyboard.getKey()
        while key != -1:
            if key in (ord("W"), Keyboard.UP):
                linear += 1.0
            elif key in (ord("S"), Keyboard.DOWN):
                linear -= 1.0
            elif key in (ord("A"), Keyboard.LEFT):
                angular += 1.0
            elif key in (ord("D"), Keyboard.RIGHT):
                angular -= 1.0
            elif key == ord("Q"):
                angular += 1.0
                spin = True
            elif key == ord("E"):
                angular -= 1.0
                spin = True
            elif key == ord(" "):
                linear = 0.0
                angular = 0.0
                spin = False
            elif key == ord("1"):
                rover.set_speed_factor(0.3)
                print("[TerraRover] Velocidad ajustada: 30% (Baja)")
            elif key == ord("2"):
                rover.set_speed_factor(0.6)
                print("[TerraRover] Velocidad ajustada: 60% (Media)")
            elif key == ord("3"):
                rover.set_speed_factor(1.0)
                print("[TerraRover] Velocidad ajustada: 100% (Alta)")

            key = keyboard.getKey()

        if linear == 0.0 and angular == 0.0:
            rover.stop()
        else:
            if linear == 0.0 and not spin:
                linear = 0.65
            rover.set_motion(linear, angular, spin_in_place=spin)


def run_demo_mode(robot: Robot, rover: SojournerController):
    print("[TerraRover] Ejecutando secuencia de prueba de locomoción...")
    elapsed = 0.0
    dt = rover.timestep / 1000.0
    last_phase = ""

    while robot.step(rover.timestep) != -1:
        if elapsed < 3.0:
            phase = "1. Avance recto"
            rover.move_forward(0.8)
        elif elapsed < 6.5:
            phase = "2. Giro a la izquierda (Ackermann doble)"
            rover.turn_left(0.7, 0.9)
        elif elapsed < 10.0:
            phase = "3. Giro a la derecha (Ackermann doble)"
            rover.turn_right(0.7, 0.9)
        elif elapsed < 12.5:
            phase = "4. Rotación sobre su propio eje"
            rover.spin_left(0.8)
        elif elapsed < 15.0:
            phase = "5. Retroceso"
            rover.move_backward(0.7)
        else:
            phase = "6. Detención completa"
            rover.stop()

        if phase != last_phase:
            print(f"[t={elapsed:4.1f}s] {phase}")
            last_phase = phase

        elapsed += dt


def run_auto_eval_mode(robot: Robot, rover: SojournerController, goal_x: float, goal_y: float):
    """
    Navegación autónoma hacia waypoint con evasión mediante sub-objetivo lateral:
      1) Retroceso breve (1.5 s) para liberar la rueda.
      2) Establece un waypoint lateral temporal (+2.5 m adelante, ±3.0 m de desvío)
         para bordear la zona conflictiva avanzando siempre hacia la meta.
    """
    rover.set_speed_factor(1.0)
    print(f"[TerraRover] Modo AUTO_EVAL iniciado -> Objetivo: ({goal_x:.2f}, {goal_y:.2f})")

    backtrack_timer = 0.0
    subgoal_timer = 0.0
    subgoal_x, subgoal_y = goal_x, goal_y
    side_sign = -1.0
    dt = rover.timestep / 1000.0

    while robot.step(rover.timestep) != -1:
        raw = robot.getCustomData().strip()
        if not raw:
            rover.stop()
            continue

        parts = raw.split(",")
        if len(parts) < 4:
            continue

        rx, ry, ryaw, status = float(parts[0]), float(parts[1]), float(parts[2]), parts[3]

        if status == "STOP":
            rover.stop()
            continue

        # Disparar recuperación una sola vez por evento de atasco
        if status == "RECOVER_STALL" and backtrack_timer <= 0.0 and subgoal_timer <= 0.0:
            backtrack_timer = 1.5
            subgoal_timer = 14.0
            side_sign = -1.0 if ry >= 9.0 else 1.0
            subgoal_x = min(goal_x, rx + 2.5)
            subgoal_y = max(2.0, min(17.5, ry + 3.0 * side_sign))
            print(f"[TerraRover] Evasión -> Sub-objetivo lateral ({subgoal_x:.2f}, {subgoal_y:.2f})")

        if backtrack_timer > 0.0:
            backtrack_timer -= dt
            rover.move_backward(0.85)
            continue

        if subgoal_timer > 0.0:
            subgoal_timer -= dt
            tx, ty = subgoal_x, subgoal_y
            if math.hypot(tx - rx, ty - ry) < 0.55:
                subgoal_timer = 0.0
        else:
            tx, ty = goal_x, goal_y

        dx = tx - rx
        dy = ty - ry
        dist = math.hypot(dx, dy)

        if dist < 0.45 and subgoal_timer <= 0.0:
            rover.stop()
            continue

        target_yaw = math.atan2(dy, dx)
        heading_error = math.atan2(math.sin(target_yaw - ryaw), math.cos(target_yaw - ryaw))

        # Navegación Ackermann continua: siempre mantiene avance lineal mientras corrige el rumbo
        angular_cmd = max(-1.0, min(1.0, -heading_error * 1.5))
        rover.set_motion(1.0, angular_cmd, spin_in_place=False)




def run_ros2_mode(robot: Robot, rover: SojournerController, port: int = 9871):
    """
    Recibe comandos de velocidad desde el nodo puente ROS 2 (terrarover_bridge)
    vía UDP local (127.0.0.1:9871) con watchdog de seguridad de 0.5 s.
    Formato paquete: "linear_norm,angular_norm,spin_int"
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", port))
    sock.setblocking(False)

    rover.set_speed_factor(1.0)
    print(f"[TerraRover] Modo ROS2 activo -> Escuchando /cmd_vel en UDP 127.0.0.1:{port}")

    last_cmd_time = 0.0
    elapsed = 0.0
    dt = rover.timestep / 1000.0
    lin_cmd, ang_cmd, spin_cmd = 0.0, 0.0, False

    while robot.step(rover.timestep) != -1:
        while True:
            try:
                data, _ = sock.recvfrom(256)
                parts = data.decode("utf-8").strip().split(",")
                if len(parts) >= 3:
                    lin_cmd = float(parts[0])
                    ang_cmd = float(parts[1])
                    spin_cmd = bool(int(parts[2]))
                    last_cmd_time = elapsed
            except BlockingIOError:
                break
            except ValueError:
                break

        # Watchdog: detener si no llegan comandos de ROS 2 en > 0.5 s
        if (elapsed - last_cmd_time) > 0.5:
            rover.stop()
        else:
            rover.set_motion(lin_cmd, ang_cmd, spin_in_place=spin_cmd)

        elapsed += dt


def main():
    robot = Robot()
    rover = SojournerController(robot)

    mode = sys.argv[1].lower() if len(sys.argv) > 1 else "manual"
    if mode == "demo":
        run_demo_mode(robot, rover)
    elif mode == "ros2":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 9871
        run_ros2_mode(robot, rover, port)
    elif mode == "auto_eval":
        goal_x = float(sys.argv[2]) if len(sys.argv) > 2 else 17.0
        goal_y = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
        run_auto_eval_mode(robot, rover, goal_x, goal_y)
    else:
        run_manual_mode(robot, rover)


if __name__ == "__main__":
    main()
