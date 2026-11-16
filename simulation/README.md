# TERRAROVER – Earth Analog Terrain Explorer (Rover Simulation Module)

Módulo de simulación física y evaluación de transitabilidad robótica desarrollado por **Killa Coders** para el **NASA Space Apps Challenge 2026**.

## Estructura del Proyecto
```text
terrarover_rover/
├── controllers/
│   ├── rover_controller/      # Cinemática 6x6 Ackermann + modos manual, demo, auto_eval y ros2
│   └── terrain_evaluator/     # Supervisor de métricas físicas y exportación JSON/CSV
├── docs/                      # Documentación técnica y validación física
├── protos/                    # Modelo 3D y texturas del rover NASA Sojourner
├── results/                   # Salidas cuantitativas (json/, csv/, plots/)
├── ros2_ws/src/terrarover_bridge/ # Nodo puente ROS 2 Jazzy (/cmd_vel, /odom, TF2, telemetría)
├── scripts/
│   ├── dem_converter/         # Conversor GeoTIFF (.tif) -> Webots ElevationGrid (.wbt)
│   ├── data_export/           # Generador de reportes gráficos PNG (matplotlib)
│   └── run_terrarover_eval.sh # Orquestador completo de evaluación
├── terrains/                  # Terrenos de prueba e importados desde DEM
└── worlds/                    # Escenas de simulación Webots (.wbt)








