"""Alpha-Beta Pruning with D4 Symmetry Reduction AI player implementation."""

import time
from typing import Dict, Tuple, List, Optional
from ai.base_player import BasePlayer
from ai.symmetry_utils import (
    get_canonical_form,
    get_symmetry_index,
    transform_move,
    ALL_SYMMETRIES
)
from game.board import Board
from game.game_logic import GameLogic
from utils.constants import PLAYER_X, PLAYER_O


# Transposition table entry flags
EXACT = 'EXACT'
LOWER_BOUND = 'LOWER'
UPPER_BOUND = 'UPPER'


class AlphaBetaSymmetryPlayer(BasePlayer):
    """AI player using Alpha-Beta Pruning with D4 Symmetry Reduction.

    Uses the 8 symmetries of the Tic-Tac-Toe board (rotations and reflections)
    to dramatically reduce the search space by treating symmetric positions
    as equivalent.

    The D4 dihedral group includes:
    - 4 rotations: 0°, 90°, 180°, 270°
    - 4 reflections: horizontal, vertical, main diagonal, anti-diagonal
    """

    def __init__(self, symbol: str):
        """
        Initializes the Alpha-Beta Symmetry player.

        Args:
            symbol: The player's symbol (X or O).
        """
        super().__init__(symbol)
        self.nodes_evaluated = 0
        self.nodes_pruned = 0
        self.symmetry_hits = 0
        self.unique_positions = 0
        self.opponent = PLAYER_O if symbol == PLAYER_X else PLAYER_X
        self.transposition_table: Dict[tuple, Tuple[int, int, str]] = {}
        self.last_alternatives: List[Dict] = []

    def get_move(self, board: Board) -> Tuple[int, Dict]:
        """
        Finds the optimal move using Alpha-Beta with Symmetry Reduction.

        Args:
            board: The current game board.

        Returns:
            Tuple containing:
                - int: The optimal move index.
                - dict: Statistics including symmetry reduction metrics.
        """
        start_time = time.perf_counter()
        self.nodes_evaluated = 0
        self.nodes_pruned = 0
        self.symmetry_hits = 0
        self.unique_positions = 0
        self.transposition_table.clear()
        self.last_alternatives = []

        best_score = float('-inf')
        best_move = -1
        move_scores = []
        alpha = float('-inf')
        beta = float('inf')

        # Get unique moves considering symmetry
        available_moves = board.get_available_moves()
        evaluated_canonical_forms = set()

        for move in available_moves:
            board.make_move(move, self.symbol)

            # Check if this position (or a symmetric equivalent) was already evaluated
            canonical = get_canonical_form(board.cells)

            if canonical in evaluated_canonical_forms:
                # Find the score from an equivalent move
                board.undo_move(move)
                # Use the score from the equivalent position
                for prev in move_scores:
                    board.make_move(prev['position'], self.symbol)
                    if get_canonical_form(board.cells) == canonical:
                        board.undo_move(prev['position'])
                        move_scores.append({'position': move, 'score': prev['score']})
                        self.symmetry_hits += 1
                        break
                    board.undo_move(prev['position'])
                continue

            evaluated_canonical_forms.add(canonical)
            score = self._alpha_beta_symmetry(board, 0, alpha, beta, False)
            board.undo_move(move)

            move_scores.append({'position': move, 'score': score})

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)

        self.last_alternatives = move_scores
        self.unique_positions = len(self.transposition_table)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        stats = {
            'nodes_evaluated': self.nodes_evaluated,
            'nodes_pruned': self.nodes_pruned,
            'symmetry_hits': self.symmetry_hits,
            'unique_positions': self.unique_positions,
            'time_ms': round(elapsed_ms, 3),
            'alternatives': move_scores,
            'chosen_score': best_score
        }

        return best_move, stats

    def _tt_lookup(
        self,
        canonical: tuple,
        depth: int,
        alpha: float,
        beta: float
    ) -> Optional[int]:
        """
        Looks up a canonical position in the transposition table.

        Args:
            canonical: Canonical form of the board position.
            depth: Current search depth.
            alpha: Current alpha value.
            beta: Current beta value.

        Returns:
            The stored score if applicable, None otherwise.
        """
        if canonical not in self.transposition_table:
            return None

        stored_score, stored_depth, flag = self.transposition_table[canonical]

        if stored_depth < depth:
            return None

        # Only count as hit when we actually use the value
        if flag == EXACT:
            self.symmetry_hits += 1
            return stored_score
        elif flag == LOWER_BOUND and stored_score >= beta:
            self.symmetry_hits += 1
            return stored_score
        elif flag == UPPER_BOUND and stored_score <= alpha:
            self.symmetry_hits += 1
            return stored_score

        return None

    def _tt_store(
        self,
        canonical: tuple,
        depth: int,
        score: int,
        flag: str
    ):
        """
        Stores a canonical position in the transposition table.

        Args:
            canonical: Canonical form of the board position.
            depth: Search depth at which this score was computed.
            score: The computed score.
            flag: EXACT, LOWER_BOUND, or UPPER_BOUND.
        """
        self.transposition_table[canonical] = (score, depth, flag)

    def _alpha_beta_symmetry(
        self,
        board: Board,
        depth: int,
        alpha: float,
        beta: float,
        is_maximizing: bool
    ) -> int:
        """
        Recursive Alpha-Beta with Symmetry-based Transposition Table.

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

        # Use canonical form for lookups
        canonical = get_canonical_form(board.cells)

        # Check transposition table
        tt_value = self._tt_lookup(canonical, depth, alpha, beta)
        if tt_value is not None:
            return tt_value

        self.nodes_evaluated += 1

        if GameLogic.is_terminal(board):
            score = GameLogic.evaluate(board, self.symbol, depth)
            self._tt_store(canonical, depth, score, EXACT)
            return score

        if is_maximizing:
            value = float('-inf')
            for move in board.get_available_moves():
                board.make_move(move, self.symbol)
                value = max(value, self._alpha_beta_symmetry(board, depth + 1, alpha, beta, False))
                board.undo_move(move)

                alpha = max(alpha, value)
                if beta <= alpha:
                    self.nodes_pruned += 1
                    break

            if value <= original_alpha:
                flag = UPPER_BOUND
            elif value >= beta:
                flag = LOWER_BOUND
            else:
                flag = EXACT
            self._tt_store(canonical, depth, value, flag)

            return value
        else:
            value = float('inf')
            for move in board.get_available_moves():
                board.make_move(move, self.opponent)
                value = min(value, self._alpha_beta_symmetry(board, depth + 1, alpha, beta, True))
                board.undo_move(move)

                beta = min(beta, value)
                if beta <= alpha:
                    self.nodes_pruned += 1
                    break

            if value <= original_alpha:
                flag = UPPER_BOUND
            elif value >= beta:
                flag = LOWER_BOUND
            else:
                flag = EXACT
            self._tt_store(canonical, depth, value, flag)

            return value
