from typing import Optional
from game.board import Board
from utils.constants import PLAYER_X, PLAYER_O, WIN_SCORE, LOSE_SCORE, TIE_SCORE


WIN_COMBINATIONS = [
    [0, 1, 2],  # top row
    [3, 4, 5],  # middle row
    [6, 7, 8],  # bottom row
    [0, 3, 6],  # left column
    [1, 4, 7],  # center column
    [2, 5, 8],  # right column
    [0, 4, 8],  # diagonal
    [2, 4, 6],  # anti-diagonal
]


class GameLogic:
    """Contains the game rules and evaluation logic."""

    @staticmethod
    def check_winner(board: Board) -> Optional[str]:
        """
        Determines if there is a winner on the board.

        Args:
            board: The current game board.

        Returns:
            The winning player symbol (X or O), or None if no winner.
        """
        for combo in WIN_COMBINATIONS:
            a, b, c = combo
            if board.cells[a] != ' ' and board.cells[a] == board.cells[b] == board.cells[c]:
                return board.cells[a]
        return None

    @staticmethod
    def is_terminal(board: Board) -> bool:
        """
        Checks if the game has ended (win or draw).

        Args:
            board: The current game board.

        Returns:
            True if game is over, False otherwise.
        """
        return GameLogic.check_winner(board) is not None or board.is_full()

    @staticmethod
    def evaluate(board: Board, maximizing_player: str, depth: int = 0) -> int:
        """
        Evaluates the board state with depth-aware scoring.

        Args:
            board: The current game board.
            maximizing_player: The player trying to maximize score.
            depth: Current depth in the search tree.

        Returns:
            Score value: positive for maximizing player win,
            negative for loss, zero for tie.
        """
        winner = GameLogic.check_winner(board)

        if winner == maximizing_player:
            return WIN_SCORE - depth
        elif winner is not None:
            return LOSE_SCORE + depth
        else:
            return TIE_SCORE
