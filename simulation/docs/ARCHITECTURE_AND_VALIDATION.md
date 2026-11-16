# Arquitectura Técnica y Validación — Módulo de Simulación Robótica (TerraRover)

**Proyecto:** TERRAROVER – Earth Analog Terrain Explorer  
**Equipo:** Killa Coders (NASA Space Apps Challenge 2026)  
**Rol:** Robotics & Rover Simulation Engineer  
**Entorno:** Ubuntu 24.04 LTS | Webots R2025a | ROS 2 Jazzy Jalisco | Python 3.12

---

## 1. Arquitectura del Rover (Modelo NASA Sojourner)
Se emplea el prototipo articulado del **Mars Pathfinder Sojourner** (`protos/Sojourner.proto`), seleccionado por ser un estándar validado de exploración planetaria ligera:
- **Suspensión Rocker-Bogie pasiva:** Dos brazos *rocker* laterales vinculados mediante un diferencial mecánico central y dos *bogies* articulados que mantienen las 6 ruedas en contacto constante con superficies irregulares sin resortes activos.
- **Tracción independiente 6×6:** Motores rotacionales (`FrontLeftWheel`, `MiddleLeftWheel`, `BackLeftWheel`, `FrontRightWheel`, `MiddleRightWheel`, `BackRightWheel`) con diámetro de rueda de `0.13 m` (`WHEEL_RADIUS = 0.065 m`).
- **Dirección Ackermann doble:** Actuadores angulares en las 4 esquinas (`FrontLeftArm`, `FrontRightArm`, `BackLeftArm`, `BackRightArm`), permitiendo giros en arco con diferencial de velocidad interno/externo y rotación sobre el propio eje (*point-turn*).

### Parámetros Físicos y Restricciones
- **Velocidad angular máxima de rueda (`MAX_WHEEL_SPEED`):** `0.6 rad/s` ($\approx 0.039\text{ m/s}$ lineal), fiel al régimen operativo real del Sojourner para garantizar tracción y estabilidad sobre regolito.
- **Fricción de contacto (`coulombFriction`):** `0.8` (suelo rocoso/regolito compacto).
- **Paso de simulación (`basicTimeStep`):** `16 ms` (`62.5 Hz`).
- **Normalización proporcional de velocidades:** En curvas combinadas, las consignas izquierda/derecha se escalan proporcionalmente si alguna supera `0.6 rad/s`, preservando el radio de curvatura Ackermann sin saturar los actuadores.

---

## 2. Pipeline de Integración con Datos Geoespaciales (DEM)
Webots no importa archivos GeoTIFF directamente debido a metadatos de proyección y valores `NoData`. El módulo `scripts/dem_converter/dem_to_webots.py` ejecuta:
1. Lectura de matriz de elevación 2D (`.tif`) y limpieza de valores `NoData`/`NaN`.
2. Normalización de cota base ($Z_{\min} = 0.0\text{ m}$) y remuestreo bilineal controlado (`max_nodes <= 120` por eje) para mantener determinismo en el motor físico ODE.
3. Generación automática de nodo `ElevationGrid` con malla visual PBR y colisión física (`boundingObject`), calculando la altura segura de aparición (`rover_spawn`) y configurando el evaluador.

---

## 3. Métricas de Transitabilidad y Metodología de Evaluación
El controlador `Supervisor` (`controllers/terrain_evaluator/terrain_evaluator.py`) distingue entre mediciones directas del motor físico y métricas algorítmicas derivadas:

| Métrica | Tipo de Medición | Definición Técnica |
| :--- | :--- | :--- |
| `distance_travelled` | Incremental 3D | Suma acumulada de desplazamientos $\sqrt{\Delta x^2 + \Delta y^2 + \Delta z^2}$. |
| `average_speed` | Derivada | Razón entre distancia total recorrida y tiempo simulado transcurrido (`m/s`). |
| `maximum_slope` | Algoritmo filtrado | Inclinación total $\arccos(\cos(\text{roll})\cos(\text{pitch}))$ medida solo durante avance efectivo ($v > 0.012\text{ m/s}$). |
| `max_roll_deg` / `max_pitch_deg` | Cinemática | Ángulos máximos de alabeo y cabeceo extraídos de la matriz de rotación del chasis. |
| `stall_events` | Algoritmo de ventana | Desplazamiento 3D neto $< 0.008\text{ m}$ en ventana de `5.0 s` durante navegación activa. |
| `stability_loss_events` | Umbral crítico | Eventos donde $\vert{}\text{roll}\vert{} > 32^\circ$ o $\vert{}\text{pitch}\vert{} > 35^\circ$. |
| `route_completion` | Progreso espacial | Porcentaje de aproximación neta desde el punto de inicio hacia el *waypoint* objetivo. |

---

## 4. Contrato de Interfaces con Otros Módulos de TerraRover

### Entradas requeridas del módulo Geospatial Data Engineer:
- **Archivo:** Modelo Digital de Elevación recortado en formato **GeoTIFF (`.tif`)** de 32-bit float (elevación en metros).
- **Parámetros:** Resolución espacial horizontal (`pixel_size` en metros/píxel) y coordenadas locales recomendadas de inicio/meta `(start_x, start_y, goal_x, goal_y)`.

### Salidas generadas para Análisis Topográfico e Interfaz de Visualización:
- `results/json/<terrain>_results.json`: Resumen estructurado de métricas y estado (`completed`, `aborted_rollover`, `timeout_partial`).
- `results/csv/<terrain>_telemetry.csv`: Serie temporal completa a `~6.25 Hz` (`time_sec, x, y, z, speed_ms, roll_deg, pitch_deg, slope_deg, ...`).
- `results/plots/<terrain>_analysis.png`: Gráfica de 3 paneles (trayectoria 2D, perfil de pendiente y estabilidad *roll/pitch*).
- **Topics ROS 2 Jazzy (`/cmd_vel`, `/odom`, `/terrarover/telemetry` y `TF2`):** Para teleoperación, navegación externa o visualización en **RViz2**.

---

## 5. Limitaciones del Modelo Físico (Simulación vs. Hardware Real)
1. **Mecánica de suelos (Terramecánica):** Webots utiliza contacto rígido basado en fricción de Coulomb (`ODE`), por lo que no modela hundimiento (*sinkage*) en arena suelta ni compactación granular del regolito.
2. **Escalones verticales:** Como se verificó en las pruebas de Fase 3, escalones verticales rígidos superiores a `~1.3x` el radio de rueda (`> 8.5 cm`) bloquean el avance frontal del Sojourner, lo cual refleja la restricción geométrica real del vehículo.
3. **Validez de resultados:** Un recorrido exitoso (`100%`) en simulación indica **viabilidad cinemática y de estabilidad geométrica** bajo las condiciones modeladas, pero no garantiza por sí solo transitabilidad absoluta en campo sin validar cohesión del suelo y deslizamiento real.
