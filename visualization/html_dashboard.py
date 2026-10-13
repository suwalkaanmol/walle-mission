import json
import os
from typing import List, Dict, Any

class HTMLDashboardGenerator:
    """
    Builds a standalone, responsive HTML5 + JavaScript interactive visualizer
    that lets users step through the mission ticks, visualize the Bayesian heatmap,
    watch WALL-E's battery and path, and inspect reasoning logs.
    """
    @staticmethod
    def generate(
        config: Dict[str, Any],
        traces: List[Dict[str, Any]],
        output_path: str
    ):
        traces_json = json.dumps(traces)
        config_json = json.dumps(config)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>WALL-E & EVE Autonomous Mission Visualizer</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --accent: #f59e0b;
      --accent-glow: rgba(245, 158, 11, 0.3);
      --eve-color: #38bdf8;
      --text: #f1f5f9;
      --text-muted: #94a3b8;
      --border: #334155;
      --obstacle: #475569;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
    body {{ background: var(--bg); color: var(--text); padding: 20px; }}
    .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid var(--border); padding-bottom: 15px; }}
    .title h1 {{ font-size: 1.6rem; color: var(--accent); }}
    .title p {{ font-size: 0.85rem; color: var(--text-muted); }}
    
    .container {{ display: grid; grid-template-columns: 520px 1fr; gap: 20px; }}
    .panel {{ background: var(--card-bg); border-radius: 12px; padding: 20px; border: 1px solid var(--border); }}
    
    /* Grid Styling */
    .grid-container {{
      display: grid;
      grid-template-columns: repeat(15, 1fr);
      grid-template-rows: repeat(15, 1fr);
      gap: 2px;
      width: 480px;
      height: 480px;
      background: #090d16;
      border: 2px solid var(--border);
      border-radius: 8px;
      padding: 4px;
      margin: 0 auto;
    }}
    .cell {{
      background: #1e293b;
      border-radius: 3px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      position: relative;
      transition: background 0.2s ease;
    }}
    .cell.obstacle {{ background: var(--obstacle); }}
    .cell.solar {{ background: #854d0e; }}
    .cell.solar::after {{ content: '☀️'; font-size: 12px; }}
    .cell.visited {{ background: #1e3a5f; }}
    .cell.visited::after {{ content: '·'; color: #60a5fa; font-weight: bold; font-size: 18px; }}
    .cell.walle {{ background: #d97706 !important; box-shadow: 0 0 10px #f59e0b; z-index: 5; }}
    .cell.walle::after {{ content: '🤖'; font-size: 16px; }}
    .cell.eve-found {{ background: #0284c7 !important; box-shadow: 0 0 12px #38bdf8; z-index: 6; }}
    .cell.eve-found::after {{ content: '❤️'; font-size: 16px; }}
    .cell.target-cand::before {{
      content: '';
      position: absolute;
      width: 80%;
      height: 80%;
      border: 1.5px dashed var(--accent);
      border-radius: 50%;
    }}

    /* Controls */
    .controls {{ margin-top: 15px; display: flex; flex-direction: column; gap: 10px; }}
    .btn-row {{ display: flex; gap: 10px; justify-content: center; }}
    button {{
      background: #334155;
      color: white;
      border: none;
      padding: 8px 16px;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 600;
      transition: 0.2s;
    }}
    button:hover {{ background: var(--accent); color: #000; }}
    input[type=range] {{ width: 100%; accent-color: var(--accent); }}

    /* Telemetry HUD */
    .hud {{ display: flex; flex-direction: column; gap: 15px; }}
    .stat-card {{ background: #0f172a; padding: 12px 16px; border-radius: 8px; border-left: 4px solid var(--accent); }}
    .stat-title {{ font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); }}
    .stat-val {{ font-size: 1.2rem; font-weight: bold; margin-top: 4px; }}
    
    .battery-bar-wrap {{ width: 100%; height: 12px; background: #334155; border-radius: 6px; overflow: hidden; margin-top: 6px; }}
    .battery-fill {{ height: 100%; width: 100%; background: #22c55e; transition: width 0.3s, background 0.3s; }}
    
    .reasoning-box {{
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 12px;
      font-family: monospace;
      font-size: 0.85rem;
      line-height: 1.4;
      min-height: 90px;
      color: #cbd5e1;
    }}
    .legend {{ display: flex; gap: 12px; font-size: 0.8rem; color: var(--text-muted); justify-content: center; margin-top: 10px; flex-wrap: wrap; }}
    .legend span {{ display: flex; align-items: center; gap: 4px; }}
  </style>
</head>
<body>
  <div class="header">
    <div class="title">
      <h1>🚀 WALL-E & EVE Autonomous Mission Dashboard</h1>
      <p>Real-Time Bayesian Triangulation & Resource-Aware Trajectory Simulation</p>
    </div>
    <div id="step-badge" style="font-size: 1.1rem; font-weight: bold; color: var(--accent);">Tick: 0</div>
  </div>

  <div class="container">
    <!-- Left: 2D Grid Visualizer -->
    <div class="panel">
      <div id="grid" class="grid-container"></div>
      
      <div class="controls">
        <input type="range" id="scrubber" min="0" max="0" value="0">
        <div class="btn-row">
          <button id="btn-prev">◀ Prev</button>
          <button id="btn-play">▶ Play</button>
          <button id="btn-next">Next ▶</button>
          <button id="btn-reset">↺ Reset</button>
        </div>
      </div>

      <div class="legend">
        <span>🤖 WALL-E</span>
        <span>☀️ Solar Station</span>
        <span>██ Obstacle</span>
        <span>· Path</span>
        <span>🎯 MAP Target</span>
        <span>❤️ Found EVE</span>
      </div>
    </div>

    <!-- Right: Telemetry & Cognitive HUD -->
    <div class="panel hud">
      <div class="stat-card">
        <div class="stat-title">Resource Status (Battery Storage)</div>
        <div class="stat-val" id="hud-battery">100.0%</div>
        <div class="battery-bar-wrap">
          <div id="battery-fill" class="battery-fill"></div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
        <div class="stat-card">
          <div class="stat-title">Decision Engine Mode</div>
          <div class="stat-val" id="hud-mode" style="font-size: 1rem; color: #38bdf8;">INIT</div>
        </div>
        <div class="stat-card">
          <div class="stat-title">Belief Entropy</div>
          <div class="stat-val" id="hud-entropy">-- bits</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-title">EVE MAP Localization (Highest Probability)</div>
        <div class="stat-val" id="hud-target">[?, ?] (0%)</div>
      </div>

      <div class="stat-card">
        <div class="stat-title">Autonomous Cognitive Reasoning Trace</div>
        <div class="reasoning-box" id="hud-reasoning">Awaiting mission initialization...</div>
      </div>
    </div>
  </div>

  <script>
    const config = {config_json};
    const traces = {traces_json};
    const width = config.map.width;
    const height = config.map.height;
    const obstacles = new Set(config.map.obstacles.map(o => `${{o[0]}},${{o[1]}}`));
    const solars = new Set(config.map.solar_recharge_stations.map(s => `${{s[0]}},${{s[1]}}`));

    const gridEl = document.getElementById('grid');
    const scrubber = document.getElementById('scrubber');
    const btnPlay = document.getElementById('btn-play');
    const btnPrev = document.getElementById('btn-prev');
    const btnNext = document.getElementById('btn-next');
    const btnReset = document.getElementById('btn-reset');
    
    scrubber.max = traces.length - 1;

    let currentStep = 0;
    let isPlaying = false;
    let playInterval = null;

    // Build static cells
    const cells = [];
    for (let y = 0; y < height; y++) {{
      for (let x = 0; x < width; x++) {{
        const cell = document.createElement('div');
        cell.className = 'cell';
        const key = `${{x}},${{y}}`;
        if (obstacles.has(key)) cell.classList.add('obstacle');
        else if (solars.has(key)) cell.classList.add('solar');
        gridEl.appendChild(cell);
        cells.push({{ x, y, el: cell }});
      }}
    }}

    function renderStep(idx) {{
      if (idx < 0 || idx >= traces.length) return;
      const t = traces[idx];
      currentStep = idx;
      scrubber.value = idx;
      document.getElementById('step-badge').innerText = `Tick: ${{t.time_step}} / ${{traces.length - 1}}`;

      // Update Telemetry
      const batt = t.battery_level;
      document.getElementById('hud-battery').innerText = `${{batt.toFixed(1)}}%`;
      const battFill = document.getElementById('battery-fill');
      battFill.style.width = `${{batt}}%`;
      battFill.style.background = batt < 25 ? '#ef4444' : (batt < 50 ? '#f59e0b' : '#22c55e');

      document.getElementById('hud-mode').innerText = t.decision_mode;
      document.getElementById('hud-entropy').innerText = `${{t.entropy.toFixed(2)}} bits`;
      document.getElementById('hud-target').innerText = `${{JSON.stringify(t.belief_target)}} (${{(t.target_confidence * 100).toFixed(1)}}%)`;
      document.getElementById('hud-reasoning').innerText = t.reasoning;

      // Track visited trail up to this step
      const visitedSet = new Set();
      for (let i = 0; i <= idx; i++) {{
        visitedSet.add(`${{traces[i].walle_position[0]}},${{traces[i].walle_position[1]}}`);
      }}

      const wx = t.walle_position[0];
      const wy = t.walle_position[1];
      const tx = t.belief_target[0];
      const ty = t.belief_target[1];

      cells.forEach(c => {{
        const key = `${{c.x}},${{c.y}}`;
        c.el.classList.remove('walle', 'visited', 'target-cand', 'eve-found');

        if (visitedSet.has(key) && !obstacles.has(key) && !solars.has(key)) {{
          c.el.classList.add('visited');
        }}

        if (c.x === tx && c.y === ty && t.target_confidence > 0.25) {{
          c.el.classList.add('target-cand');
        }}

        if (c.x === wx && c.y === wy) {{
          if (c.x === config.map.eve_location[0] && c.y === config.map.eve_location[1]) {{
            c.el.classList.add('eve-found');
          }} else {{
            c.el.classList.add('walle');
          }}
        }}
      }});
    }}

    function togglePlay() {{
      if (isPlaying) {{
        clearInterval(playInterval);
        btnPlay.innerText = '▶ Play';
        isPlaying = false;
      }} else {{
        isPlaying = true;
        btnPlay.innerText = '⏸ Pause';
        playInterval = setInterval(() => {{
          if (currentStep < traces.length - 1) {{
            renderStep(currentStep + 1);
          }} else {{
            togglePlay();
          }}
        }}, 350);
      }}
    }}

    scrubber.addEventListener('input', (e) => renderStep(parseInt(e.target.value)));
    btnPlay.addEventListener('click', togglePlay);
    btnNext.addEventListener('click', () => renderStep(Math.min(traces.length - 1, currentStep + 1)));
    btnPrev.addEventListener('click', () => renderStep(Math.max(0, currentStep - 1)));
    btnReset.addEventListener('click', () => {{
      if (isPlaying) togglePlay();
      renderStep(0);
    }});

    // Initial render
    renderStep(0);
  </script>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        return output_path
