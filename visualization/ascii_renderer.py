from typing import Dict, Any, List, Set, Tuple

class ASCIIRenderer:
    """
    Renders an ASCII visualization of the wasteland, WALL-E's position,
    recharge stations, obstacles, and belief heatmap.
    """
    @staticmethod
    def render_frame(
        env: Any,
        walle_pos: List[int],
        battery: float,
        step: int,
        reasoning: str,
        mode: str,
        entropy: float,
        belief_map: Any,
        visited_tiles: Set[Tuple[int, int]]
    ) -> str:
        width = env.width
        height = env.height
        lines = []

        header = f"\n+{'-' * (width * 3 + 2)}+\n"
        header += f"| WALL-E WASTELAND EXPLORATION [Tick: {step:02d}] {' ' * max(0, width * 3 - 35)}|\n"
        header += f"+{'-' * (width * 3 + 2)}+"
        lines.append(header)

        # Map grid
        best_cand, max_p = belief_map.get_most_likely_location()

        for y in range(height):
            row_str = "| "
            for x in range(width):
                pos = (x, y)
                if [x, y] == walle_pos and [x, y] == env.eve_location:
                    row_str += "<3 "  # Found EVE!
                elif [x, y] == walle_pos:
                    row_str += " W "  # WALL-E
                elif pos in env.obstacles:
                    row_str += "###"  # Obstacle / Scrap
                elif [x, y] in env.recharge_stations:
                    row_str += " S "  # Solar Station
                elif any(c["location"] == [x, y] and c["discovered"] for c in env.clues):
                    row_str += " ? "  # Clue recovered
                elif pos == best_cand and max_p > 0.2:
                    row_str += " @ "  # High probability candidate
                elif pos in visited_tiles:
                    row_str += " . "  # Visited trail
                else:
                    # Show belief heat intensity
                    p = belief_map.grid.get(pos, 0.0)
                    if p > 0.05:
                        row_str += " : "
                    else:
                        row_str += "   "
            row_str += "|"
            lines.append(row_str)

        footer = f"+{'-' * (width * 3 + 2)}+"
        lines.append(footer)

        # Battery Bar
        bar_len = 20
        filled = int((battery / 100.0) * bar_len)
        battery_bar = "=" * filled + "-" * (bar_len - filled)

        lines.append(f" [Battery] [{battery_bar}] {battery:.1f}%")
        lines.append(f" [Sensor] Mode: {mode} | Entropy: {entropy:.2f} bits | MAP Target: {list(best_cand)} ({max_p*100:.1f}%)")
        lines.append(f" [Cognition] Decision: {reasoning}")
        lines.append(" Legend: W: WALL-E | <3: Found EVE | S: Solar Station | ###: Obstacle | ?: Clue | @: Target | .: Trail")
        return "\n".join(lines)
