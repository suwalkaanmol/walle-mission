import json
import math
import random
from typing import Dict, Any, Tuple, List, Optional

class WastelandEnvironment:
    """
    Simulated Wasteland Environment for WALL-E.
    Manages true world state, physics, battery depletion, sensor signal decay,
    and clue discovery. The agent only observes partial state through sensors.
    """
    def __init__(self, config_path: str):
        with open(config_path, "r") as f:
            self.config = json.load(f)

        self.width: int = self.config["map"]["width"]
        self.height: int = self.config["map"]["height"]
        self.seed: int = self.config["map"].get("seed", 42)
        random.seed(self.seed)

        self.walle_start: List[int] = list(self.config["map"]["walle_start"])
        self.eve_location: List[int] = list(self.config["map"]["eve_location"])
        self.eve_status: str = self.config["map"].get("eve_initial_status", "Dormant Beacon Active")
        self.recharge_stations: List[List[int]] = self.config["map"]["solar_recharge_stations"]
        self.obstacles: set = set(tuple(o) for o in self.config["map"]["obstacles"])

        # Resource budget
        budget = self.config["resource_budget"]
        self.initial_battery: float = budget["initial_battery"]
        self.max_battery: float = budget["max_battery"]
        self.max_time_steps: int = budget["max_time_steps"]
        self.action_costs: Dict[str, float] = budget["action_costs"]

        # Sensors
        sensors = self.config["sensors"]
        self.passive_noise_std: float = sensors.get("passive_signal_noise_std", 0.05)
        self.scan_range: int = sensors.get("active_scan_range", 4)
        self.scan_noise_std: float = sensors.get("active_scan_noise_std", 0.02)

        # Clues
        self.clues: List[Dict[str, Any]] = [dict(c) for c in self.config["clues"]]

        # State variables
        self.walle_pos: List[int] = list(self.walle_start)
        self.battery: float = self.initial_battery
        self.time_step: int = 0
        self.mission_completed: bool = False
        self.discovered_clue_ids: set = set()

    def reset(self) -> Dict[str, Any]:
        """Resets the simulation to the initial state."""
        self.walle_pos = list(self.walle_start)
        self.battery = self.initial_battery
        self.time_step = 0
        self.mission_completed = False
        self.discovered_clue_ids.clear()
        for c in self.clues:
            c["discovered"] = False

        return self._generate_observation(action_taken="INIT", action_success=True)

    def _calc_distance_to_eve(self, pos: List[int]) -> float:
        return math.sqrt((pos[0] - self.eve_location[0]) ** 2 + (pos[1] - self.eve_location[1]) ** 2)

    def _calculate_signal_strength(self, pos: List[int], noise_std: float) -> float:
        """
        Simulates electromagnetic beacon intensity with path-loss decay and Gaussian sensor noise.
        Intensity is normalized between 0.0 and 1.0.
        """
        dist = self._calc_distance_to_eve(pos)
        # Standard inverse square decay: S = 1 / (1 + (d / 3)^2)
        base_signal = 1.0 / (1.0 + (dist / 3.0) ** 1.8)
        noise = random.gauss(0.0, noise_std)
        return max(0.0, min(1.0, round(base_signal + noise, 4)))

    def is_valid_tile(self, x: int, y: int) -> bool:
        """Checks if a tile is inside boundaries and not blocked by scrap/obstacles."""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        if (x, y) in self.obstacles:
            return False
        return True

    def is_on_recharge_station(self) -> bool:
        return self.walle_pos in self.recharge_stations

    def step(self, action: str, direction: Optional[str] = None) -> Tuple[Dict[str, Any], bool, Dict[str, Any]]:
        """
        Executes an action in the environment.
        Actions:
        - "MOVE": Requires direction ("UP", "DOWN", "LEFT", "RIGHT")
        - "SCAN": Perform active radar sweep (reveals clues & high-precision beacon reading)
        - "RECHARGE": Absorb solar radiation (only allowed at solar recharge stations)
        - "WAIT": Idle conservation
        """
        action = action.upper()
        self.time_step += 1
        success = True
        message = ""

        # Apply battery cost
        cost = self.action_costs.get(action.lower(), 1.0)
        
        if action == "MOVE":
            dx, dy = 0, 0
            if direction == "UP":
                dy = -1
            elif direction == "DOWN":
                dy = 1
            elif direction == "LEFT":
                dx = -1
            elif direction == "RIGHT":
                dx = 1
            else:
                success = False
                message = f"Invalid move direction: {direction}"

            new_x = self.walle_pos[0] + dx
            new_y = self.walle_pos[1] + dy

            if success:
                if self.is_valid_tile(new_x, new_y):
                    self.walle_pos = [new_x, new_y]
                    self.battery -= cost
                    message = f"Moved {direction} to [{new_x}, {new_y}]."
                else:
                    success = False
                    self.battery -= (cost * 0.5)  # minor penalty for bump
                    message = f"Movement blocked: [{new_x}, {new_y}] is an obstacle or out of bounds."

        elif action == "SCAN":
            self.battery -= cost
            message = f"Executed active radar scan at [{self.walle_pos[0]}, {self.walle_pos[1]}]."

        elif action == "RECHARGE":
            if self.is_on_recharge_station():
                recharge_amount = abs(cost)  # recharge cost is negative in config
                self.battery = min(self.max_battery, self.battery + recharge_amount)
                message = f"Solar recharge successful! +{recharge_amount}% battery."
            else:
                success = False
                self.battery -= 1.0
                message = "Recharge failed: WALL-E is not at a Solar Recharge Station."

        elif action == "WAIT":
            self.battery -= cost
            message = "Idling in power-saving mode."

        else:
            success = False
            message = f"Unknown action: {action}"

        # Ensure battery stays bounded
        self.battery = round(max(0.0, self.battery), 2)

        # Check for mission end conditions
        if self.walle_pos == self.eve_location:
            self.mission_completed = True
            message += " SUCCESS: WALL-E has reached EVE!"

        done = False
        if self.mission_completed:
            done = True
        elif self.battery <= 0.0:
            done = True
            message += " CRITICAL FAILURE: WALL-E ran out of battery in the wasteland."
        elif self.time_step >= self.max_time_steps:
            done = True
            message += " TIMEOUT: Maximum mission time exceeded."

        obs = self._generate_observation(action_taken=action, action_success=success, action_message=message)
        info = {
            "success": success,
            "message": message,
            "mission_completed": self.mission_completed,
            "out_of_battery": (self.battery <= 0.0),
            "eve_location_ground_truth": self.eve_location
        }
        return obs, done, info

    def _generate_observation(self, action_taken: str, action_success: bool, action_message: str = "") -> Dict[str, Any]:
        """Generates the observation payload visible to the agent."""
        is_scan = (action_taken == "SCAN" and action_success)
        noise = self.scan_noise_std if is_scan else self.passive_noise_std
        signal_val = self._calculate_signal_strength(self.walle_pos, noise_std=noise)

        # Clue detection: Clues are discovered if WALL-E is directly on the tile,
        # or within scan_range during an active SCAN action.
        newly_discovered_clues = []
        for clue in self.clues:
            clue_pos = clue["location"]
            dist = math.sqrt((self.walle_pos[0] - clue_pos[0]) ** 2 + (self.walle_pos[1] - clue_pos[1]) ** 2)
            
            is_detected = False
            if dist == 0:  # Direct contact
                is_detected = True
            elif is_scan and dist <= self.scan_range:  # Radar sweep
                is_detected = True

            if is_detected and clue["id"] not in self.discovered_clue_ids:
                clue["discovered"] = True
                self.discovered_clue_ids.add(clue["id"])
                newly_discovered_clues.append(clue)

        # Local terrain observation (3x3 grid around WALL-E)
        local_grid = {}
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                tx, ty = self.walle_pos[0] + dx, self.walle_pos[1] + dy
                tile_type = "EMPTY"
                if not (0 <= tx < self.width and 0 <= ty < self.height):
                    tile_type = "OUT_OF_BOUNDS"
                elif (tx, ty) in self.obstacles:
                    tile_type = "OBSTACLE"
                elif [tx, ty] in self.recharge_stations:
                    tile_type = "SOLAR_STATION"
                elif [tx, ty] == self.eve_location and (tx, ty) == tuple(self.walle_pos):
                    tile_type = "EVE_DIRECT_CONTACT"
                local_grid[f"({tx},{ty})"] = tile_type

        return {
            "time_step": self.time_step,
            "walle_pos": list(self.walle_pos),
            "battery": self.battery,
            "signal_strength": signal_val,
            "signal_mode": "ACTIVE_HIGH_PRECISION" if is_scan else "PASSIVE_BEACON",
            "at_solar_station": self.is_on_recharge_station(),
            "local_surroundings": local_grid,
            "discovered_clues": newly_discovered_clues,
            "all_known_clues": [c for c in self.clues if c["id"] in self.discovered_clue_ids],
            "action_feedback": {
                "action": action_taken,
                "success": action_success,
                "message": action_message
            }
        }
