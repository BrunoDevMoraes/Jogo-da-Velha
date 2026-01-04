import time
from typing import Dict, Tuple, Optional, List
from ai.base_player import BasePlayer
from game.board import Board
from game.game_logic import GameLogic
from utils.constants import PLAYER_X, PLAYER_O


class AlphaBetaPlayer(BasePlayer):
    """AI player using the Minimax algorithm with Alpha-Beta Pruning optimization."""

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
        Finds the optimal move using Minimax algorithm with Alpha-Beta Pruning.

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
            score = self._alpha_beta(board, 0, False, alpha, beta)
            board.undo_move(move)

            move_scores.append({'position': move, 'score': score})

            if score > best_score:
                best_score = score
                best_move = move

            # Atualiza alpha para o próximo nível
            alpha = max(alpha, best_score)

        self.last_alternatives = move_scores

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        stats = {
            'nodes_evaluated': self.nodes_evaluated,
            'nodes_pruned': self.nodes_pruned,
            'time_ms': round(elapsed_ms, 3),
            'alternatives': move_scores,
            'chosen_score': best_score,
            'pruning_rate': round((self.nodes_pruned / max(self.nodes_evaluated + self.nodes_pruned, 1)) * 100, 2)
        }

        return best_move, stats

    def _alpha_beta(
        self, 
        board: Board, 
        depth: int, 
        is_maximizing: bool, 
        alpha: float, 
        beta: float
    ) -> int:
        """
        Recursive Alpha-Beta Pruning algorithm with depth-aware scoring.

        Args:
            board: The current game board.
            depth: Current depth in the search tree.
            is_maximizing: True if maximizing player's turn.
            alpha: The best value that the maximizing player can guarantee.
            beta: The best value that the minimizing player can guarantee.

        Returns:
            The evaluation score for the current board state.
        """
        self.nodes_evaluated += 1

        if GameLogic.is_terminal(board):
            return GameLogic.evaluate(board, self.symbol, depth)

        if is_maximizing:
            best_score = float('-inf')
            moves = board.get_available_moves()
            for i, move in enumerate(moves):
                board.make_move(move, self.symbol)
                score = self._alpha_beta(board, depth + 1, False, alpha, beta)
                board.undo_move(move)
                
                best_score = max(best_score, score)
                alpha = max(alpha, best_score)
                
                # Poda alfa-beta: se beta <= alpha, podemos cortar este ramo
                if beta <= alpha:
                    # Conta os movimentos restantes que foram podados
                    self.nodes_pruned += len(moves) - i - 1
                    break  # Poda beta
                    
            return best_score
        else:
            best_score = float('inf')
            moves = board.get_available_moves()
            for i, move in enumerate(moves):
                board.make_move(move, self.opponent)
                score = self._alpha_beta(board, depth + 1, True, alpha, beta)
                board.undo_move(move)
                
                best_score = min(best_score, score)
                beta = min(beta, best_score)
                
                # Poda alfa-beta: se beta <= alpha, podemos cortar este ramo
                if beta <= alpha:
                    # Conta os movimentos restantes que foram podados
                    self.nodes_pruned += len(moves) - i - 1
                    break  # Poda alfa
                    
            return best_score

