"""NegaScout (Principal Variation Search) AI player implementation."""

import time
from typing import Dict, Tuple, List
from ai.base_player import BasePlayer
from game.board import Board
from game.game_logic import GameLogic
from utils.constants import PLAYER_X, PLAYER_O


class NegaScoutPlayer(BasePlayer):
    """AI player using NegaScout (Principal Variation Search) algorithm.

    NegaScout is an optimization of Alpha-Beta that uses null-window searches
    to quickly verify that non-PV moves are indeed worse than the principal
    variation. It assumes good move ordering - the first move is likely best.

    Key insight: After finding a good move, we only need to prove that
    subsequent moves are NOT better (using a minimal window search).
    """

    def __init__(self, symbol: str):
        """
        Initializes the NegaScout player.

        Args:
            symbol: The player's symbol (X or O).
        """
        super().__init__(symbol)
        self.nodes_evaluated = 0
        self.null_window_searches = 0
        self.re_searches = 0
        self.opponent = PLAYER_O if symbol == PLAYER_X else PLAYER_X
        self.last_alternatives: List[Dict] = []

    def get_move(self, board: Board) -> Tuple[int, Dict]:
        """
        Finds the optimal move using NegaScout algorithm.

        Args:
            board: The current game board.

        Returns:
            Tuple containing:
                - int: The optimal move index.
                - dict: Statistics including null-window and re-search counts.
        """
        start_time = time.perf_counter()
        self.nodes_evaluated = 0
        self.null_window_searches = 0
        self.re_searches = 0
        self.last_alternatives = []

        best_score = float('-inf')
        best_move = -1
        move_scores = []
        alpha = float('-inf')
        beta = float('inf')

        available_moves = board.get_available_moves()

        for i, move in enumerate(available_moves):
            board.make_move(move, self.symbol)

            if i == 0:
                # First move: full window search (this is our PV candidate)
                score = -self._negascout(board, 0, -beta, -alpha, -1)
            else:
                # Subsequent moves: null-window search first
                self.null_window_searches += 1
                score = -self._negascout(board, 0, -alpha - 1, -alpha, -1)

                # If score is within window, re-search with full window
                if alpha < score < beta:
                    self.re_searches += 1
                    score = -self._negascout(board, 0, -beta, -score, -1)

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
            'null_window_searches': self.null_window_searches,
            're_searches': self.re_searches,
            'time_ms': round(elapsed_ms, 3),
            'alternatives': move_scores,
            'chosen_score': best_score
        }

        return best_move, stats

    def _negascout(
        self,
        board: Board,
        depth: int,
        alpha: float,
        beta: float,
        color: int
    ) -> int:
        """
        Recursive NegaScout algorithm using negamax formulation.

        The negamax formulation simplifies the code by always maximizing,
        just with negated values and swapped alpha/beta.

        Args:
            board: The current game board.
            depth: Current depth in the search tree.
            alpha: Lower bound of the search window.
            beta: Upper bound of the search window.
            color: 1 for maximizing (AI), -1 for minimizing (opponent).

        Returns:
            The evaluation score from current player's perspective.
        """
        self.nodes_evaluated += 1

        if GameLogic.is_terminal(board):
            # Evaluate from AI's perspective, then adjust for current player
            raw_score = GameLogic.evaluate(board, self.symbol, depth)
            return color * raw_score

        available_moves = board.get_available_moves()
        current_player = self.symbol if color == 1 else self.opponent

        first_child = True
        value = float('-inf')

        for move in available_moves:
            board.make_move(move, current_player)

            if first_child:
                # Full window search for first child (principal variation)
                child_value = -self._negascout(board, depth + 1, -beta, -alpha, -color)
                first_child = False
            else:
                # Null-window (scout) search
                self.null_window_searches += 1
                child_value = -self._negascout(board, depth + 1, -alpha - 1, -alpha, -color)

                # Re-search if necessary
                if alpha < child_value < beta:
                    self.re_searches += 1
                    child_value = -self._negascout(board, depth + 1, -beta, -child_value, -color)

            board.undo_move(move)

            value = max(value, child_value)
            alpha = max(alpha, value)

            if alpha >= beta:
                break  # Beta cutoff

        return value
