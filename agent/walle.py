from typing import Dict, Any, Tuple, List, Optional
from agent.belief import BayesianBeliefMap
from agent.planner import GridPlanner

class WallEAgent:
    """
    Autonomous Cognitive Agent for WALL-E.
    Combines:
    1. Bayesian Belief Tracking (radio signal likelihood + clue constraints)
    2. Dynamic Resource Management (battery threshold vs solar station distance)
    3. Strategic Goal Arbitration (Survival, Clue Hunting, Radar Sweep, EVE Rescue)
    4. Full Action Reasoning Logging
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.width = config["map"]["width"]
        self.height = config["map"]["height"]
        self.obstacles = set(tuple(o) for o in config["map"]["obstacles"])
        self.solar_stations = [tuple(s) for s in config["map"]["solar_recharge_stations"]]

        self.belief_map = BayesianBeliefMap(self.width, self.height, self.obstacles)
        self.planner = GridPlanner(self.width, self.height, self.obstacles)

        self.safety_margin = config["resource_budget"].get("critical_battery_threshold", 25.0)
        self.visited_tiles: set = set()
        self.scanned_locations: set = set()
        self.investigated_clue_ids: set = set()

        # Step counter for periodic radar sweeps
        self.steps_since_last_scan: int = 0
        self.current_mode: str = "INITIAL_SURVEY"

    def find_nearest_solar_station(self, current_pos: Tuple[int, int]) -> Tuple[Tuple[int, int], int]:
        """Finds closest solar station and Manhattan distance."""
        best_station = self.solar_stations[0]
        min_dist = float('inf')
        for station in self.solar_stations:
            dist = abs(current_pos[0] - station[0]) + abs(current_pos[1] - station[1])
            if dist < min_dist:
                min_dist = dist
                best_station = station
        return best_station, min_dist

    def decide_action(self, obs: Dict[str, Any]) -> Tuple[str, Optional[str], str, Dict[str, Any]]:
        """
        Processes incoming sensory observation, updates internal belief state,
        arbitrates goals, and returns (action, direction, reasoning_string, trace_metadata).
        """
        walle_pos = tuple(obs["walle_pos"])
        battery = obs["battery"]
        signal_strength = obs["signal_strength"]
        signal_mode = obs["signal_mode"]
        at_solar = obs["at_solar_station"]
        self.visited_tiles.add(walle_pos)

        # 1. Update Belief Map from sensory observation
        noise_std = (
            self.config["sensors"]["active_scan_noise_std"]
            if signal_mode == "ACTIVE_HIGH_PRECISION"
            else self.config["sensors"]["passive_signal_noise_std"]
        )
        self.belief_map.update_from_signal(list(walle_pos), signal_strength, noise_std)

        # 2. Update Belief Map from any newly discovered clues
        new_clues = obs.get("discovered_clues", [])
        for clue in new_clues:
            self.belief_map.update_from_clue(clue)
            self.investigated_clue_ids.add(clue["id"])

        # Current state assessments
        entropy = self.belief_map.calculate_entropy()
        best_eve_coord, max_prob = self.belief_map.get_most_likely_location()
        top_candidates = self.belief_map.get_top_n_candidates(3)
        nearest_solar, dist_to_solar = self.find_nearest_solar_station(walle_pos)

        # Battery budget to reach safety
        move_cost = self.config["resource_budget"]["action_costs"]["move"]
        energy_needed_for_solar = (dist_to_solar * move_cost) + self.safety_margin

        action = "WAIT"
        direction = None
        reasoning = ""
        self.steps_since_last_scan += 1

        # -------------------------------------------------------------
        # BEHAVIOR ARBITRATION TREE
        # -------------------------------------------------------------

        # Priority 1: Recharge if currently on solar panel and battery is depleted
        if at_solar and battery < 85.0:
            self.current_mode = "RECHARGING_SOLAR"
            action = "RECHARGE"
            reasoning = f"WALL-E is docked at Solar Station {list(walle_pos)}. Battery is {battery:.1f}%. Charging solar cells to full capacity."

        # Priority 2: Critical Battery -> Route to Solar Station
        elif battery <= energy_needed_for_solar:
            self.current_mode = "RETREAT_TO_RECHARGE"
            path = self.planner.find_path(walle_pos, nearest_solar)
            if path and len(path) > 1:
                direction = GridPlanner.get_direction(walle_pos, path[1])
                action = "MOVE"
                reasoning = (
                    f"CRITICAL BATTERY WARNING ({battery:.1f}% <= {energy_needed_for_solar:.1f}% safety reserve). "
                    f"Retreating towards nearest Solar Station at {nearest_solar} (est. distance: {dist_to_solar} steps)."
                )
            else:
                action = "WAIT"
                reasoning = f"Battery low ({battery:.1f}%), waiting or station unreachable."

        # Priority 3: High certainty of EVE's location -> Advance directly to rescue
        elif max_prob > 0.35 or entropy < 2.5:
            self.current_mode = "CONVERGE_ON_EVE"
            target = best_eve_coord
            if walle_pos == target:
                action = "SCAN"
                self.steps_since_last_scan = 0
                reasoning = (
                    f"WALL-E reached peak belief coordinate {target} (probability: {max_prob * 100:.1f}%). "
                    "Conducting active radar sweep to confirm EVE visual contact."
                )
            else:
                path = self.planner.find_path(walle_pos, target)
                if path and len(path) > 1:
                    direction = GridPlanner.get_direction(walle_pos, path[1])
                    action = "MOVE"
                    reasoning = (
                        f"High confidence localization achieved! Target: {target} (P={max_prob * 100:.1f}%, Entropy={entropy:.2f}). "
                        f"Navigating {direction} along optimal A* trajectory."
                    )
                else:
                    action = "SCAN"
                    reasoning = f"Path to target {target} obstructed. Scanning surroundings."

        # Priority 4: Clue Investigation (if clues remain unvisited and entropy is still high)
        elif self._has_unvisited_clues() and entropy > 3.0:
            self.current_mode = "CLUE_INVESTIGATION"
            target_clue = self._get_next_clue_target(walle_pos)
            if target_clue:
                clue_loc = tuple(target_clue["location"])
                dist_to_clue = abs(walle_pos[0] - clue_loc[0]) + abs(walle_pos[1] - clue_loc[1])

                if dist_to_clue <= 3 and self.steps_since_last_scan >= 4:
                    action = "SCAN"
                    self.steps_since_last_scan = 0
                    reasoning = f"Within proximity ({dist_to_clue} tiles) of unrecovered artifact at {clue_loc}. Emitting active radar pulse to acquire telemetry."
                else:
                    path = self.planner.find_path(walle_pos, clue_loc)
                    if path and len(path) > 1:
                        direction = GridPlanner.get_direction(walle_pos, path[1])
                        action = "MOVE"
                        reasoning = f"Entropy is elevated ({entropy:.2f}). Moving towards artifact clue {target_clue['id']} at {clue_loc} to isolate EVE's coordinates."
                    else:
                        action = "SCAN"
                        reasoning = "Clue location unreachable, scanning local sector."
            else:
                action = "SCAN"
                reasoning = "Surveying local sector."

        # Priority 5: Periodic Radar Sweep to Triangulate (Active Scan)
        elif self.steps_since_last_scan >= 7 and battery > 40.0:
            self.current_mode = "ACTIVE_TRIANGULATION"
            action = "SCAN"
            self.steps_since_last_scan = 0
            reasoning = (
                f"Radio ambiguity detected across sectors (Entropy: {entropy:.2f}). "
                f"Firing active beacon radar to obtain low-noise sensor reading and eliminate false positives."
            )

        # Priority 6: Default Exploration towards highest probability gradient
        else:
            self.current_mode = "EXPLORATION_GRADIENT"
            target = best_eve_coord
            path = self.planner.find_path(walle_pos, target)
            if path and len(path) > 1:
                direction = GridPlanner.get_direction(walle_pos, path[1])
                action = "MOVE"
                reasoning = (
                    f"Exploring along probability gradient towards candidate {target} "
                    f"(Top candidate probability: {max_prob * 100:.1f}%, Entropy: {entropy:.2f})."
                )
            else:
                action = "WAIT"
                reasoning = "Holding position to conserve battery."

        trace_meta = {
            "mode": self.current_mode,
            "target_candidate": list(best_eve_coord),
            "candidate_probability": max_prob,
            "top_candidates": top_candidates,
            "entropy": entropy,
            "battery_status": "CRITICAL" if battery <= energy_needed_for_solar else "HEALTHY",
            "nearest_solar_dist": dist_to_solar
        }

        return action, direction, reasoning, trace_meta

    def _has_unvisited_clues(self) -> bool:
        for c in self.config["clues"]:
            if c["id"] not in self.investigated_clue_ids:
                return True
        return False

    def _get_next_clue_target(self, current_pos: Tuple[int, int]) -> Optional[Dict[str, Any]]:
        unvisited = [c for c in self.config["clues"] if c["id"] not in self.investigated_clue_ids]
        if not unvisited:
            return None
        # Closest clue
        return min(unvisited, key=lambda c: abs(current_pos[0] - c["location"][0]) + abs(current_pos[1] - c["location"][1]))
