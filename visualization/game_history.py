from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class MoveAnalysis:
    """Analysis of a single move with alternatives."""
    move_number: int
    player: str
    algorithm: str  # Nome do algoritmo (ex: 'Alpha-Beta')
    chosen_position: int
    chosen_score: int
    board_before: List[str]
    board_after: List[str]
    alternatives: List[Dict]  # [{position: int, score: int}, ...]
    nodes_evaluated: int
    time_ms: float
    is_terminal: bool = False
    result: Optional[str] = None  # 'WIN_X', 'WIN_O', 'TIE'

class GameHistoryCollector:
    """Collects game history for end-of-game visualization."""

    def __init__(self):
        self.moves: List[MoveAnalysis] = []
        self._current_move_number = 0

    def record_move(
        self,
        player: str,
        algorithm: str,
        chosen_position: int,
        chosen_score: int,
        board_before: List[str],
        board_after: List[str],
        alternatives: List[Dict],
        nodes_evaluated: int,
        time_ms: float
    ):
        self._current_move_number += 1
        move = MoveAnalysis(
            move_number=self._current_move_number,
            player=player,
            algorithm=algorithm,
            chosen_position=chosen_position,
            chosen_score=chosen_score,
            board_before=board_before.copy(),
            board_after=board_after.copy(),
            alternatives=alternatives,
            nodes_evaluated=nodes_evaluated,
            time_ms=time_ms
        )
        self.moves.append(move)

    def set_game_result(self, result: str):
        if self.moves:
            self.moves[-1].is_terminal = True
            self.moves[-1].result = result

    def get_total_nodes(self) -> int:
        return sum(m.nodes_evaluated for m in self.moves)

    def get_total_time(self) -> float:
        return sum(m.time_ms for m in self.moves)

    def get_ai_moves(self) -> List[MoveAnalysis]:
        return self.moves

    def clear(self):
        self.moves = []
        self._current_move_number = 0

    def has_moves(self) -> bool:
        return len(self.moves) > 0