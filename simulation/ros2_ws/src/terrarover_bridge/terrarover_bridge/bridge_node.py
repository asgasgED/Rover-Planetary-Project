#!/usr/bin/env python3
"""
TerraRover - Nodo Puente ROS 2 Jazzy (Fase 6)
Equipo: Killa Coders | NASA Space Apps Challenge 2026
Descripción:
    Interfaz estándar ROS 2 entre el simulador Webots y los demás módulos de TerraRover:
      - Suscribe  : /cmd_vel (geometry_msgs/Twist) -> envía consignas al rover en Webots.
      - Publica   : /odom (nav_msgs/Odometry) + TF (odom -> base_link) para RViz2.
      - Publica   : /terrarover/telemetry (std_msgs/String JSON) en tiempo real.
"""

import json
import math
import socket
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from tf2_ros import TransformBroadcaster


class TerraRoverBridgeNode(Node):
    MAX_LINEAR_MS = 0.039   # Velocidad lineal máxima física del Sojourner (0.6 rad/s * 0.065 m)
    MAX_ANGULAR_RADS = 0.35

    def __init__(self):
        super().__init__("terrarover_bridge_node")

        # Sockets UDP locales hacia/desde los controladores de Webots
        self.rx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rx_sock.bind(("127.0.0.1", 9870))
        self.rx_sock.setblocking(False)

        self.tx_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rover_cmd_addr = ("127.0.0.1", 9871)

        # Publicadores ROS 2
        self.odom_pub = self.create_publisher(Odometry, "/odom", 10)
        self.telemetry_pub = self.create_publisher(String, "/terrarover/telemetry", 10)
        self.tf_broadcaster = TransformBroadcaster(self)

        # Suscriptor de comandos de velocidad estándar
        self.cmd_sub = self.create_subscription(Twist, "/cmd_vel", self.cmd_vel_callback, 10)

        # Timer a 20 Hz para procesar telemetría entrante desde Webots
        self.timer = self.create_timer(0.05, self.poll_webots_telemetry)
        self.get_logger().info(
            "TerraRover ROS 2 Bridge activo | Suscrito a /cmd_vel | Publicando /odom, TF y /terrarover/telemetry"
        )

    def cmd_vel_callback(self, msg: Twist):
        lin_norm = max(-1.0, min(1.0, msg.linear.x / self.MAX_LINEAR_MS))
        # Invertir signo angular para alinear convención ENU (+Z antihorario) con Ackermann del proto
        ang_norm = max(-1.0, min(1.0, -msg.angular.z / self.MAX_ANGULAR_RADS))
        spin = 1 if (abs(lin_norm) < 0.05 and abs(ang_norm) > 0.1) else 0

        packet = f"{lin_norm:.3f},{ang_norm:.3f},{spin}".encode("utf-8")
        self.tx_sock.sendto(packet, self.rover_cmd_addr)

    def poll_webots_telemetry(self):
        latest_raw = None
        while True:
            try:
                data, _ = self.rx_sock.recvfrom(2048)
                latest_raw = data.decode("utf-8")
            except BlockingIOError:
                break

        if not latest_raw:
            return

        # 1. Publicar JSON crudo en /terrarover/telemetry
        t_msg = String()
        t_msg.data = latest_raw
        self.telemetry_pub.publish(t_msg)

        # 2. Publicar Odometry y TF2 (odom -> base_link)
        try:
            d = json.loads(latest_raw)
        except json.JSONDecodeError:
            return

        now = self.get_clock().now().to_msg()
        x = float(d.get("x", 0.0))
        y = float(d.get("y", 0.0))
        z = float(d.get("z", 0.0))
        yaw = float(d.get("yaw_rad", 0.0))
        speed = float(d.get("speed_ms", 0.0))

        qz = math.sin(yaw * 0.5)
        qw = math.cos(yaw * 0.5)

        odom = Odometry()
        odom.header.stamp = now
        odom.header.frame_id = "odom"
        odom.child_frame_id = "base_link"
        odom.pose.pose.position.x = x
        odom.pose.pose.position.y = y
        odom.pose.pose.position.z = z
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.twist.twist.linear.x = speed
        self.odom_pub.publish(odom)

        tf_msg = TransformStamped()
        tf_msg.header.stamp = now
        tf_msg.header.frame_id = "odom"
        tf_msg.child_frame_id = "base_link"
        tf_msg.transform.translation.x = x
        tf_msg.transform.translation.y = y
        tf_msg.transform.translation.z = z
        tf_msg.transform.rotation.z = qz
        tf_msg.transform.rotation.w = qw
        self.tf_broadcaster.sendTransform(tf_msg)


def main(args=None):
    rclpy.init(args=args)
    node = TerraRoverBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
