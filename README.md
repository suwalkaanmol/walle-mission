# 🤖 Project: WALL-E and EVE's Signal
> **Autonomous Cognitive Agent Exploration & Bayesian Triangulation in a Resource-Constrained Wasteland**

[![GitHub Pages](https://img.shields.io/badge/Demo-Live%20on%20GitHub%20Pages-success?style=for-the-badge&logo=github)](https://suwalkaanmol.github.io/walle-mission/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-orange?style=for-the-badge)](LICENSE)

👉 **Live Interactive Visualizer**: [https://suwalkaanmol.github.io/walle-mission/](https://suwalkaanmol.github.io/walle-mission/)  
👉 **Source Code**: [https://github.com/suwalkaanmol/walle-mission](https://github.com/suwalkaanmol/walle-mission)

---

## 🌟 Overview

This project implements an autonomous cognitive agent (**WALL-E**) designed to locate a lost companion (**EVE**) across an uncertain, obstacle-strewn wasteland environment. 

WALL-E operates under **partial observability (Fog of War)** and strict **battery constraints**, combining:
- **Bayesian Belief Modeling & Grid Updates**
- **Information-Theoretic Shannon Entropy Reduction**
- **A\* Path Planning with Obstacle Avoidance**
- **Dynamic Fail-Safe Energy Reserves & Solar Recharging**

---

## 🎮 Interactive Web Visualizer

You can inspect the entire mission step-by-step or run the simulation directly in your browser:

👉 **[Launch Live Visualizer](https://suwalkaanmol.github.io/walle-mission/)**

### Dashboard Features:
* **Interactive Timeline Scrubber**: Step through tick-by-tick actions, decisions, and movement paths.
* **Bayesian Probability Heatmap**: Watch uncertainty collapse in real-time as WALL-E gathers RF beacon samples and decrypts directional clues.
* **Telemetry HUD**: Live battery meter, current entropy score (bits), coordinates, and cognitive internal thoughts.
* **Fog of War & Radar Overlays**: Visual rendering of active sensor scans and terrain discovery.

---

## 🏗️ Architecture & System Design

```
walle_mission/
├── index.html                         # Interactive Web Visualizer (GitHub Pages entry)
├── walle_game.html                    # Standalone playable web app
├── run_simulation.py                  # CLI simulation runner
├── config/
│   └── mission_earth_wasteland.json   # Mission map, budget, clues, noise parameters
├── sim_env/
│   └── environment.py                 # Ground-truth physics, fog-of-war, sensors & battery
├── agent/
│   ├── belief.py                      # 2D Bayesian Probability Grid & Shannon Entropy
│   ├── planner.py                     # A* pathfinding with obstacle avoidance
│   └── walle.py                       # Cognitive brain, goal arbitrator, and energy monitor
├── reporting/
│   └── reporter.py                    # Structured trace logger & Markdown report generator
├── visualization/
│   ├── ascii_renderer.py              # Terminal live visualization HUD
│   └── html_dashboard.py              # Interactive HTML5 dashboard generator
└── output/
    ├── mission_traces.json            # Step-by-step action, observation, reasoning logs
    ├── MISSION_REPORT.md              # Executive summary and localization metrics
    └── mission_dashboard.html         # Generated simulation report visualizer
```

---

## 🧮 Theoretical Formulation

### 1. Electromagnetic Beacon Decay Model
The radio beacon emitted by EVE follows an empirical path-loss attenuation model with Euclidean distance $d = \sqrt{(x - x_E)^2 + (y - y_E)^2}$:

$$S(d) = \frac{1.0}{1.0 + \left(\frac{d}{3.0}\right)^{1.8}} + \mathcal{N}(0, \sigma^2)$$

* **Passive Mode:** $\sigma = 0.05$ (continuous low-power background reading).
* **Active Radar Sweep:** $\sigma = 0.02$ (narrowband high-precision scan, costs $6.0\%$ battery).

### 2. Bayesian Spatial Belief Update
The agent maintains a 2D spatial probability matrix $P(\text{EVE} = (x, y))$ across all valid terrain cells. Upon observing signal intensity $S_{\text{obs}}$ from position $(x_W, y_W)$:

$$P(\text{EVE} = (x, y) \mid S_{\text{obs}}) \propto \exp\left(-\frac{\left(S_{\text{obs}} - \hat{S}(x, y)\right)^2}{2\sigma^2}\right) \cdot P(\text{EVE} = (x, y))$$

When symbolic clues are discovered (e.g., directional vectors $x \ge 7, y \ge 7$ or proximity radii $d \le 6.0$), inconsistent coordinates are zeroed out and the distribution is re-normalized.

### 3. Shannon Entropy (Uncertainty Quantification)
To mathematically measure how certain WALL-E is about EVE's location:

$$H = -\sum_{x, y} P(x, y) \log_2 P(x, y)$$

* **Initial Entropy:** $\approx 7.72\text{ bits}$ (complete uniform ambiguity across 225 grid cells).
* **Final Converged Entropy:** $\approx 0.32\text{ bits}$ ($>95\%$ uncertainty reduction upon pinpointing target).

### 4. Dynamic Energy Safety Reserve
At every tick, WALL-E calculates the Manhattan energy cost to reach the nearest solar station $S^*$:

$$E_{\text{safe}} = \left(\| \mathbf{x}_W - S^* \|_1 \times \text{Cost}_{\text{move}}\right) + \text{Threshold}_{\text{crit}}$$

If current battery $B \le E_{\text{safe}}$, the agent automatically overrides exploration and initiates an emergency retreat to dock and recharge.

---

## ⚙️ Configuration Format (`config/*.json`)

```json
{
  "mission_name": "WALL-E and EVE's Signal Exploration",
  "map": {
    "width": 15,
    "height": 15,
    "walle_start": [1, 1],
    "eve_location": [12, 13],
    "solar_recharge_stations": [[2, 3], [8, 8], [13, 2]],
    "obstacles": [[3, 1], [3, 2], [7, 5], "..."]
  },
  "resource_budget": {
    "initial_battery": 100.0,
    "max_battery": 100.0,
    "max_time_steps": 100,
    "action_costs": { "move": 2.0, "scan": 6.0, "recharge": -30.0 }
  },
  "sensors": {
    "passive_signal_noise_std": 0.05,
    "active_scan_range": 4,
    "active_scan_noise_std": 0.02
  },
  "clues": [
    {
      "id": "clue_scrap_01",
      "location": [4, 2],
      "type": "directional_hint",
      "data": { "spatial_filter": { "min_x": 7, "min_y": 7 } }
    }
  ]
}
```

---

## 🚀 Running Locally

### Prerequisites
* Python 3.8+ (Pure standard library — zero external dependencies needed to run the core simulation!)

### Execute with Live ASCII Terminal Stream
```bash
python run_simulation.py
```

### Fast Headless Run (Generates Reports & Web Dashboard)
```bash
python run_simulation.py --no-live
```

### Custom Configuration & Adjust Speed
```bash
python run_simulation.py --config config/mission_earth_wasteland.json --delay 0.05
```

---

## 📊 Deliverables & Results

* **Execution Traces:** `output/mission_traces.json` (action, observation, probability distribution, and cognitive reasoning at every tick).
* **Comprehensive Report:** `output/MISSION_REPORT.md` (summary statistics, telemetry artifacts, energy consumption, and findings).
* **Interactive Dashboard:** `index.html` (accessible online via GitHub Pages or opened locally in any browser).

---

## 👨‍💻 Author

**Anmol Suwalka**  
* GitHub: [@suwalkaanmol](https://github.com/suwalkaanmol)  
* Project Repo: [walle-mission](https://github.com/suwalkaanmol/walle-mission)
