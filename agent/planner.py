import heapq
from typing import List, Tuple, Optional, Set

class GridPlanner:
    """
    A* pathfinding and navigation utilities for WALL-E.
    Finds shortest paths avoiding terrain obstacles.
    """
    def __init__(self, width: int, height: int, obstacles: Set[Tuple[int, int]]):
        self.width = width
        self.height = height
        self.obstacles = set(obstacles)

    def is_traversable(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height and (x, y) not in self.obstacles

    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        # Manhattan distance heuristic
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """Returns sequence of coordinates [(x1, y1), (x2, y2), ...] from start to goal."""
        if start == goal:
            return [start]
        if not self.is_traversable(goal[0], goal[1]):
            # If exact goal is an obstacle, find nearest traversable neighbor
            goal = self.find_nearest_traversable(goal)
            if not goal:
                return None

        frontier = []
        heapq.heappush(frontier, (0, start))
        came_from = {start: None}
        cost_so_far = {start: 0}

        while frontier:
            _, current = heapq.heappop(frontier)

            if current == goal:
                break

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                next_node = (current[0] + dx, current[1] + dy)
                if not self.is_traversable(next_node[0], next_node[1]):
                    continue

                new_cost = cost_so_far[current] + 1
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    priority = new_cost + self.heuristic(next_node, goal)
                    heapq.heappush(frontier, (priority, next_node))
                    came_from[next_node] = current

        if goal not in came_from:
            return None

        # Reconstruct path
        path = []
        curr = goal
        while curr:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
        return path

    def find_nearest_traversable(self, target: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        for r in range(1, 4):
            for dx in range(-r, r + 1):
                for dy in range(-r, r + 1):
                    cand = (target[0] + dx, target[1] + dy)
                    if self.is_traversable(cand[0], cand[1]):
                        return cand
        return None

    @staticmethod
    def get_direction(curr: Tuple[int, int], nxt: Tuple[int, int]) -> str:
        dx = nxt[0] - curr[0]
        dy = nxt[1] - curr[1]
        if dx == 1:
            return "RIGHT"
        elif dx == -1:
            return "LEFT"
        elif dy == 1:
            return "DOWN"
        elif dy == -1:
            return "UP"
        return "WAIT"
