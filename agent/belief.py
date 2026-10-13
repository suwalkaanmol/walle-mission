import math
from typing import Dict, Any, List, Tuple

class BayesianBeliefMap:
    """
    Maintains a 2D spatial Bayesian probability grid P(EVE at (x, y)).
    Updates dynamically using sensor likelihoods (radio attenuation) and
    symbolic clues (spatial bounding boxes, proximity circles).
    Computes Shannon Entropy to mathematically quantify certainty over time.
    """
    def __init__(self, width: int, height: int, obstacles: set):
        self.width = width
        self.height = height
        self.obstacles = set(obstacles)
        
        # Initialize Uniform Prior over all non-obstacle cells
        valid_cells = []
        for x in range(width):
            for y in range(height):
                if (x, y) not in self.obstacles:
                    valid_cells.append((x, y))
                    
        initial_prob = 1.0 / len(valid_cells) if valid_cells else 0.0
        self.grid: Dict[Tuple[int, int], float] = {}
        for x in range(width):
            for y in range(height):
                if (x, y) in self.obstacles:
                    self.grid[(x, y)] = 0.0
                else:
                    self.grid[(x, y)] = initial_prob

        self.eve_status: str = "Unknown / Awaiting Clues"
        self.entropy_history: List[float] = [self.calculate_entropy()]

    def normalize(self):
        """Normalizes probability grid so the total sum equals 1.0."""
        total = sum(self.grid.values())
        if total > 0.0:
            for k in self.grid:
                self.grid[k] /= total
        else:
            # Fallback uniform if zeroed out
            valid_cells = [k for k in self.grid if k not in self.obstacles]
            p = 1.0 / len(valid_cells)
            for k in self.grid:
                self.grid[k] = p if k not in self.obstacles else 0.0

    def update_from_signal(self, walle_pos: List[int], measured_signal: float, noise_std: float):
        """
        Bayesian update: P(EVE=(x,y) | signal) proportional to P(signal | EVE=(x,y)) * P(EVE=(x,y))
        Likelihood modelled as Gaussian around expected attenuation.
        """
        wx, wy = walle_pos
        variance_2 = 2.0 * (noise_std ** 2)

        for (x, y), prior in self.grid.items():
            if prior <= 0.0 or (x, y) in self.obstacles:
                continue

            dist = math.sqrt((x - wx) ** 2 + (y - wy) ** 2)
            expected_signal = 1.0 / (1.0 + (dist / 3.0) ** 1.8)
            residual = measured_signal - expected_signal
            
            # Gaussian likelihood
            likelihood = math.exp(-(residual ** 2) / variance_2)
            self.grid[(x, y)] = prior * likelihood

        self.normalize()
        self.entropy_history.append(self.calculate_entropy())

    def update_from_clue(self, clue: Dict[str, Any]):
        """
        Applies symbolic constraints from discovered clues to prune improbable coordinates.
        """
        clue_type = clue.get("type")
        data = clue.get("data", {})

        if clue_type == "directional_hint":
            spatial = data.get("spatial_filter", {})
            min_x = spatial.get("min_x", 0)
            min_y = spatial.get("min_y", 0)
            max_x = spatial.get("max_x", self.width - 1)
            max_y = spatial.get("max_y", self.height - 1)

            for (x, y) in list(self.grid.keys()):
                if not (min_x <= x <= max_x and min_y <= y <= max_y):
                    # Zero out cells outside the directional cone
                    self.grid[(x, y)] = 0.0

        elif clue_type == "proximity_hint":
            cx, cy = data.get("center", [0, 0])
            max_r = data.get("max_radius", self.width)

            for (x, y) in list(self.grid.keys()):
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                if dist > max_r:
                    self.grid[(x, y)] = 0.0

        elif clue_type == "status_hint":
            self.eve_status = data.get("eve_status", "Identified")

        self.normalize()
        self.entropy_history.append(self.calculate_entropy())

    def calculate_entropy(self) -> float:
        """Computes Shannon Entropy H = - sum(p * log2(p)). Lower means higher certainty."""
        h = 0.0
        for p in self.grid.values():
            if p > 1e-12:
                h -= p * math.log2(p)
        return round(h, 4)

    def get_most_likely_location(self) -> Tuple[Tuple[int, int], float]:
        """Returns the coordinate with maximum a posteriori (MAP) probability and its confidence."""
        best_coord = max(self.grid, key=self.grid.get)
        confidence = self.grid[best_coord]
        return best_coord, round(confidence, 4)

    def get_top_n_candidates(self, n: int = 5) -> List[Tuple[Tuple[int, int], float]]:
        """Returns the top N candidate coordinates sorted by belief probability."""
        sorted_cells = sorted(self.grid.items(), key=lambda item: item[1], reverse=True)
        return [(coord, round(p, 4)) for coord, p in sorted_cells[:n]]

    def get_regional_confidence(self, center: Tuple[int, int], radius: int = 2) -> float:
        """Computes cumulative probability mass within a small neighborhood of candidate center."""
        cx, cy = center
        mass = 0.0
        for (x, y), p in self.grid.items():
            if abs(x - cx) <= radius and abs(y - cy) <= radius:
                mass += p
        return round(mass, 4)
