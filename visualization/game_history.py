from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class MoveAnalysis:
    """Analysis of a single move with alternatives."""
    move_number: int
    player: str
    chosen_position: int
    chosen_score: int
    board_before: List[str]
    board_after: List[str]
    alternatives: List[Dict]  # [{position: int, score: int}, ...]
    nodes_evaluated: int
    time_ms: float
    algorithm_name: Optional[str] = None  # Name of the AI algorithm used (e.g., "MinimaxPlayer", "AlphaBetaPlayer")
    nodes_pruned: Optional[int] = None  # Number of nodes pruned (for Alpha-Beta)
    is_terminal: bool = False
    result: Optional[str] = None  # 'WIN_X', 'WIN_O', 'TIE'


class GameHistoryCollector:
    """Collects game history for end-of-game visualization."""

    def __init__(self):
        """Initializes an empty game history."""
        self.moves: List[MoveAnalysis] = []
        self._current_move_number = 0

    def record_move(
        self,
        player: str,
        chosen_position: int,
        chosen_score: int,
        board_before: List[str],
        board_after: List[str],
        alternatives: List[Dict],
        nodes_evaluated: int,
        time_ms: float,
        algorithm_name: Optional[str] = None,
        nodes_pruned: Optional[int] = None
    ):
        """
        Records a move with its analysis.

        Args:
            player: The player making the move (X or O).
            chosen_position: The position chosen (0-8).
            chosen_score: The minimax score of the chosen move.
            board_before: Board state before the move.
            board_after: Board state after the move.
            alternatives: List of alternative moves with scores.
            nodes_evaluated: Number of nodes evaluated.
            time_ms: Time taken to compute the move.
            algorithm_name: Name of the AI algorithm used (e.g., "MinimaxPlayer", "AlphaBetaPlayer").
            nodes_pruned: Number of nodes pruned (for Alpha-Beta algorithm).
        """
        self._current_move_number += 1

        move = MoveAnalysis(
            move_number=self._current_move_number,
            player=player,
            chosen_position=chosen_position,
            chosen_score=chosen_score,
            board_before=board_before.copy(),
            board_after=board_after.copy(),
            alternatives=alternatives,
            nodes_evaluated=nodes_evaluated,
            time_ms=time_ms,
            algorithm_name=algorithm_name,
            nodes_pruned=nodes_pruned
        )

        self.moves.append(move)

    def set_game_result(self, result: str):
        """
        Sets the final game result.

        Args:
            result: 'WIN_X', 'WIN_O', or 'TIE'.
        """
        if self.moves:
            self.moves[-1].is_terminal = True
            self.moves[-1].result = result

    def get_total_nodes(self) -> int:
        """Returns total nodes evaluated across all moves."""
        return sum(m.nodes_evaluated for m in self.moves)

    def get_total_time(self) -> float:
        """Returns total computation time in milliseconds."""
        return sum(m.time_ms for m in self.moves)

    def get_ai_moves(self) -> List[MoveAnalysis]:
        """Returns only AI moves (useful for visualization)."""
        return self.moves

    def clear(self):
        """Clears all recorded history."""
        self.moves = []
        self._current_move_number = 0

    def has_moves(self) -> bool:
        """Returns True if there are recorded moves."""
        return len(self.moves) > 0
