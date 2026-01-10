"""Alpha-Beta Pruning AI player implementation."""

import time
from typing import Dict, Tuple, List
from ai.base_player import BasePlayer
from game.board import Board
from game.game_logic import GameLogic
from utils.constants import PLAYER_X, PLAYER_O


class AlphaBetaPlayer(BasePlayer):
    """AI player using Alpha-Beta Pruning algorithm.

    Alpha-Beta pruning reduces the search space from O(b^d) to O(b^(d/2))
    in the best case by eliminating branches that cannot affect the final
    decision.
    """

    def __init__(self, symbol: str):
        """
        Initializes the Alpha-Beta player.

        Args:
            symbol: The player's symbol (X or O).
        """
        super().__init__(symbol)
        self.nodes_evaluated = 0
        self.nodes_pruned = 0
        self.opponent = PLAYER_O if symbol == PLAYER_X else PLAYER_X
        self.last_alternatives: List[Dict] = []

    def get_move(self, board: Board) -> Tuple[int, Dict]:
        """
        Finds the optimal move using Alpha-Beta Pruning.

        Args:
            board: The current game board.

        Returns:
            Tuple containing:
                - int: The optimal move index.
                - dict: Statistics (nodes_evaluated, nodes_pruned, time_ms, alternatives).
        """
        start_time = time.perf_counter()
        self.nodes_evaluated = 0
        self.nodes_pruned = 0
        self.last_alternatives = []

        best_score = float('-inf')
        best_move = -1
        move_scores = []
        alpha = float('-inf')
        beta = float('inf')

        for move in board.get_available_moves():
            board.make_move(move, self.symbol)
            score = self._alpha_beta(board, 0, alpha, beta, False)
            board.undo_move(move)

            move_scores.append({'position': move, 'score': score})

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)

        self.last_alternatives = move_scores

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        stats = {
            'nodes_evaluated': self.nodes_evaluated,
            'nodes_pruned': self.nodes_pruned,
            'time_ms': round(elapsed_ms, 3),
            'alternatives': move_scores,
            'chosen_score': best_score
        }

        return best_move, stats

    def _alpha_beta(
        self,
        board: Board,
        depth: int,
        alpha: float,
        beta: float,
        is_maximizing: bool
    ) -> int:
        """
        Recursive Alpha-Beta algorithm with pruning.

        Args:
            board: The current game board.
            depth: Current depth in the search tree.
            alpha: Best value the maximizer can guarantee.
            beta: Best value the minimizer can guarantee.
            is_maximizing: True if maximizing player's turn.

        Returns:
            The evaluation score for the current board state.
        """
        self.nodes_evaluated += 1

        if GameLogic.is_terminal(board):
            return GameLogic.evaluate(board, self.symbol, depth)

        if is_maximizing:
            value = float('-inf')
            for move in board.get_available_moves():
                board.make_move(move, self.symbol)
                value = max(value, self._alpha_beta(board, depth + 1, alpha, beta, False))
                board.undo_move(move)

                alpha = max(alpha, value)
                if beta <= alpha:
                    self.nodes_pruned += 1
                    break  # Beta cutoff

            return value
        else:
            value = float('inf')
            for move in board.get_available_moves():
                board.make_move(move, self.opponent)
                value = min(value, self._alpha_beta(board, depth + 1, alpha, beta, True))
                board.undo_move(move)

                beta = min(beta, value)
                if beta <= alpha:
                    self.nodes_pruned += 1
                    break  # Alpha cutoff

            return value
