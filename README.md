# 🤖 Project: WALL-E and EVE's Signal
> **Autonomous Cognitive Agent Exploration & Bayesian Triangulation in a Resource-Constrained Wasteland**

---

## 🌟 Overview
This project implements an autonomous cognitive agent (**WALL-E**) designed to locate a lost companion (**EVE**) across an uncertain, obstacle-strewn environment. WALL-E operates under partial observability (Fog of War) and strict battery constraints, combining **Bayesian belief modeling**, **information-theoretic entropy reduction**, **A\* path planning**, and **fail-safe solar recharging**.

---

## 🏗️ Architecture & System Design

```
walle_mission/
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
│   └── html_dashboard.py              # Interactive HTML5 dashboard with timeline scrubber
├── output/
│   ├── mission_traces.json            # Step-by-step action, observation, reasoning logs
│   ├── MISSION_REPORT.md              # Executive summary and localization metrics
│   └── mission_dashboard.html         # Standalone web visualizer
├── run_simulation.py                  # CLI simulation runner
└── README.md                          # Full documentation
```

---

## 🧮 Theoretical Formulation

### 1. Electromagnetic Beacon Decay Model
The radio beacon emitted by EVE follows an empirical path-loss attenuation model with distance $d = \sqrt{(x - x_E)^2 + (y - y_E)^2}$:

$$S(d) = \frac{1.0}{1.0 + \left(\frac{d}{3.0}\right)^{1.8}} + \mathcal{N}(0, \sigma^2)$$

* **Passive Mode:** $\sigma = 0.05$ (continuous low-power background reading).
* **Active Radar Sweep:** $\sigma = 0.02$ (narrowband high-precision scan, costs $6.0\%$ battery).

### 2. Bayesian Spatial Belief Update
The agent maintains a 2D spatial probability matrix $P(\text{EVE} = (x, y))$ across all valid terrain cells. Upon observing signal intensity $S_{\text{obs}}$ from position $(x_W, y_W)$:

$$P(\text{EVE} = (x, y) \mid S_{\text{obs}}) \propto \exp\left(-\frac{\left(S_{\text{obs}} - \hat{S}(x, y)\right)^2}{2\sigma^2}\right) \cdot P(\text{EVE} = (x, y))$$

When symbolic clues are discovered (e.g., directional vectors $x \ge 7, y \ge 7$ or proximity radii $d \le 6.0$), inconsistent coordinates are zeroed out and the distribution is re-normalized.

### 3. Shannon Entropy (Uncertainty Quantification)
To mathematically measure how certain WALL-E is about EVE's position:

$$H = -\sum_{x, y} P(x, y) \log_2 P(x, y)$$

* **Initial Entropy:** $\approx 7.72\text{ bits}$ (complete uniform ambiguity).
* **Final Converged Entropy:** $\approx 0.32\text{ bits}$ ($>95\%$ uncertainty reduction).

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

## 🚀 How to Run

### Requirements
* Pure standard Python 3.8+ (no heavy external libraries required!).

### Execute with Live ASCII Terminal Stream
```bash
python run_simulation.py
```

### Fast Headless Run (Generates Reports & Web Dashboard)
```bash
python run_simulation.py --no-live
```

### Custom Configurations & Adjust Speed
```bash
python run_simulation.py --config config/mission_earth_wasteland.json --delay 0.05
```

---

## 📊 Deliverables & Results Summary

* **Execution Traces:** `output/mission_traces.json` (logs action, observation, probability distribution, and cognitive reasoning at every tick).
* **Comprehensive Report:** `output/MISSION_REPORT.md` (summary statistics, telemetry artifacts recovered, energy analysis, and next steps).
* **Interactive UI Dashboard:** Open `output/mission_dashboard.html` in any web browser to scrub through the steps, view battery levels, and watch the Bayesian heatmap evolve!
