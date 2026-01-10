"""Alpha-Beta Pruning with Transposition Table AI player implementation."""

import time
from typing import Dict, Tuple, List, Optional
from ai.base_player import BasePlayer
from game.board import Board
from game.game_logic import GameLogic
from utils.constants import PLAYER_X, PLAYER_O


# Transposition table entry flags
EXACT = 'EXACT'      # Exact minimax value
LOWER_BOUND = 'LOWER'  # Score is a lower bound (failed high)
UPPER_BOUND = 'UPPER'  # Score is an upper bound (failed low)


class AlphaBetaTTPlayer(BasePlayer):
    """AI player using Alpha-Beta Pruning with Transposition Table.

    The transposition table stores previously evaluated positions to avoid
    redundant computation when the same position is reached via different
    move sequences.
    """

    def __init__(self, symbol: str):
        """
        Initializes the Alpha-Beta TT player.

        Args:
            symbol: The player's symbol (X or O).
        """
        super().__init__(symbol)
        self.nodes_evaluated = 0
        self.nodes_pruned = 0
        self.tt_hits = 0
        self.tt_stores = 0
        self.opponent = PLAYER_O if symbol == PLAYER_X else PLAYER_X
        self.transposition_table: Dict[tuple, Tuple[int, int, str]] = {}
        self.last_alternatives: List[Dict] = []

    def get_move(self, board: Board) -> Tuple[int, Dict]:
        """
        Finds the optimal move using Alpha-Beta with Transposition Table.

        Args:
            board: The current game board.

        Returns:
            Tuple containing:
                - int: The optimal move index.
                - dict: Statistics including TT hit rate.
        """
        start_time = time.perf_counter()
        self.nodes_evaluated = 0
        self.nodes_pruned = 0
        self.tt_hits = 0
        self.tt_stores = 0
        self.transposition_table.clear()
        self.last_alternatives = []

        best_score = float('-inf')
        best_move = -1
        move_scores = []
        alpha = float('-inf')
        beta = float('inf')

        for move in board.get_available_moves():
            board.make_move(move, self.symbol)
            score = self._alpha_beta_tt(board, 0, alpha, beta, False)
            board.undo_move(move)

            move_scores.append({'position': move, 'score': score})

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)

        self.last_alternatives = move_scores

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        total_lookups = self.tt_hits + self.nodes_evaluated
        hit_rate = (self.tt_hits / total_lookups * 100) if total_lookups > 0 else 0

        stats = {
            'nodes_evaluated': self.nodes_evaluated,
            'nodes_pruned': self.nodes_pruned,
            'tt_hits': self.tt_hits,
            'tt_stores': self.tt_stores,
            'tt_hit_rate': round(hit_rate, 1),
            'time_ms': round(elapsed_ms, 3),
            'alternatives': move_scores,
            'chosen_score': best_score
        }

        return best_move, stats

    def _board_hash(self, board: Board) -> tuple:
        """Creates a hashable key for the board state."""
        return tuple(board.cells)

    def _tt_lookup(
        self,
        board_hash: tuple,
        depth: int,
        alpha: float,
        beta: float
    ) -> Optional[int]:
        """
        Looks up a position in the transposition table.

        Args:
            board_hash: Hash of the board position.
            depth: Current search depth.
            alpha: Current alpha value.
            beta: Current beta value.

        Returns:
            The stored score if applicable, None otherwise.
        """
        if board_hash not in self.transposition_table:
            return None

        stored_score, stored_depth, flag = self.transposition_table[board_hash]

        # Only use entries from equal or deeper searches
        if stored_depth < depth:
            return None

        self.tt_hits += 1

        if flag == EXACT:
            return stored_score
        elif flag == LOWER_BOUND and stored_score >= beta:
            return stored_score
        elif flag == UPPER_BOUND and stored_score <= alpha:
            return stored_score

        return None

    def _tt_store(
        self,
        board_hash: tuple,
        depth: int,
        score: int,
        flag: str
    ):
        """
        Stores a position in the transposition table.

        Args:
            board_hash: Hash of the board position.
            depth: Search depth at which this score was computed.
            score: The computed score.
            flag: EXACT, LOWER_BOUND, or UPPER_BOUND.
        """
        # Always replace (simple replacement scheme)
        self.transposition_table[board_hash] = (score, depth, flag)
        self.tt_stores += 1

    def _alpha_beta_tt(
        self,
        board: Board,
        depth: int,
        alpha: float,
        beta: float,
        is_maximizing: bool
    ) -> int:
        """
        Recursive Alpha-Beta with Transposition Table.

        Args:
            board: The current game board.
            depth: Current depth in the search tree.
            alpha: Best value the maximizer can guarantee.
            beta: Best value the minimizer can guarantee.
            is_maximizing: True if maximizing player's turn.

        Returns:
            The evaluation score for the current board state.
        """
        original_alpha = alpha
        board_hash = self._board_hash(board)

        # Check transposition table
        tt_value = self._tt_lookup(board_hash, depth, alpha, beta)
        if tt_value is not None:
            return tt_value

        self.nodes_evaluated += 1

        if GameLogic.is_terminal(board):
            score = GameLogic.evaluate(board, self.symbol, depth)
            self._tt_store(board_hash, depth, score, EXACT)
            return score

        if is_maximizing:
            value = float('-inf')
            for move in board.get_available_moves():
                board.make_move(move, self.symbol)
                value = max(value, self._alpha_beta_tt(board, depth + 1, alpha, beta, False))
                board.undo_move(move)

                alpha = max(alpha, value)
                if beta <= alpha:
                    self.nodes_pruned += 1
                    break

            # Store in transposition table with appropriate flag
            if value <= original_alpha:
                flag = UPPER_BOUND
            elif value >= beta:
                flag = LOWER_BOUND
            else:
                flag = EXACT
            self._tt_store(board_hash, depth, value, flag)

            return value
        else:
            value = float('inf')
            for move in board.get_available_moves():
                board.make_move(move, self.opponent)
                value = min(value, self._alpha_beta_tt(board, depth + 1, alpha, beta, True))
                board.undo_move(move)

                beta = min(beta, value)
                if beta <= alpha:
                    self.nodes_pruned += 1
                    break

            # Store in transposition table with appropriate flag
            if value <= original_alpha:
                flag = UPPER_BOUND
            elif value >= beta:
                flag = LOWER_BOUND
            else:
                flag = EXACT
            self._tt_store(board_hash, depth, value, flag)

            return value
