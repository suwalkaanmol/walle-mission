import os
import sys
import argparse
import time

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Ensure UTF-8 output encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from sim_env.environment import WastelandEnvironment
from agent.walle import WallEAgent
from reporting.reporter import MissionReporter
from visualization.ascii_renderer import ASCIIRenderer
from visualization.html_dashboard import HTMLDashboardGenerator

def run_mission(config_path: str, live_display: bool = True, delay: float = 0.05):
    print("=" * 65)
    print("[START] AUTONOMOUS MISSION: OPERATION FIND EVE")
    print(f"[CONFIG] Loading Configuration: {config_path}")
    print("=" * 65)

    env = WastelandEnvironment(config_path)
    agent = WallEAgent(env.config)
    
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    reporter = MissionReporter(env.config.get("mission_name", "Operation Find EVE"), output_dir)

    obs = env.reset()
    done = False
    step = 0

    while not done:
        # Agent cognitive decision cycle
        action, direction, reasoning, meta = agent.decide_action(obs)

        # Log trace before executing action
        reporter.log_step(
            time_step=step,
            observation=obs,
            action=action,
            direction=direction or "NONE",
            reasoning=reasoning,
            meta=meta
        )

        if live_display:
            frame = ASCIIRenderer.render_frame(
                env=env,
                walle_pos=obs["walle_pos"],
                battery=obs["battery"],
                step=step,
                reasoning=reasoning,
                mode=meta.get("mode", ""),
                entropy=meta.get("entropy", 0.0),
                belief_map=agent.belief_map,
                visited_tiles=agent.visited_tiles
            )
            print(frame)
            if delay > 0:
                time.sleep(delay)

        # Step the environment
        obs, done, info = env.step(action, direction)
        step += 1

    # Final trace entry upon completion or termination
    best_cand, max_p = agent.belief_map.get_most_likely_location()
    final_meta = {
        "mode": "MISSION_COMPLETE" if info.get("mission_completed") else "TERMINATED",
        "entropy": agent.belief_map.calculate_entropy(),
        "target_candidate": list(best_cand),
        "candidate_probability": max_p,
        "top_candidates": agent.belief_map.get_top_n_candidates(3),
        "battery_status": "EXHAUSTED" if info.get("out_of_battery") else "STABLE"
    }
    reporter.log_step(
        time_step=step,
        observation=obs,
        action="HALT",
        direction="NONE",
        reasoning=info.get("message", "Mission terminated."),
        meta=final_meta
    )

    # Save deliverables
    trace_file = reporter.save_traces()
    report_file = reporter.generate_report(
        final_obs=obs,
        done_info=info,
        belief_map=agent.belief_map,
        start_pos=env.walle_start
    )
    dashboard_path = os.path.join(output_dir, "mission_dashboard.html")
    HTMLDashboardGenerator.generate(env.config, reporter.traces, dashboard_path)

    print("\n" + "=" * 65)
    print("[COMPLETE] MISSION RUN COMPLETE")
    print(f"[*] Result: {'[SUCCESS]' if info.get('mission_completed') else '[FAILED]'}")
    print(f"[*] Outcome: {info.get('message')}")
    print(f"[*] Traces saved to: {trace_file}")
    print(f"[*] Mission Report: {report_file}")
    print(f"[*] Interactive Dashboard: {dashboard_path}")
    print("=" * 65)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WALL-E Autonomous Mission Simulator")
    parser.add_argument(
        "--config",
        type=str,
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "config", "mission_earth_wasteland.json"),
        help="Path to mission configuration file"
    )
    parser.add_argument(
        "--no-live",
        action="store_true",
        help="Disable ASCII live streaming in terminal"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.01,
        help="Delay between steps in live mode (seconds)"
    )

    args = parser.parse_args()
    run_mission(args.config, live_display=not args.no_live, delay=args.delay)
