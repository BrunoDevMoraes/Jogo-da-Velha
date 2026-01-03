import random
import time
from typing import Dict, Tuple
from ai.base_player import BasePlayer
from game.board import Board


class RandomPlayer(BasePlayer):
    """AI player that makes random moves."""

    def get_move(self, board: Board) -> Tuple[int, Dict]:
        """
        Selects a random available move.

        Args:
            board: The current game board.

        Returns:
            Tuple containing:
                - int: A randomly chosen move index.
                - dict: Statistics (nodes_evaluated=1, time_ms).
        """
        start_time = time.perf_counter()

        available = board.get_available_moves()
        move = random.choice(available) if available else -1

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        stats = {
            'nodes_evaluated': 1,
            'time_ms': round(elapsed_ms, 3)
        }

        return move, stats
