from typing import List, Optional
from utils.constants import EMPTY, PLAYER_X, PLAYER_O


class Board:
    """Represents the Tic-Tac-Toe game board."""

    def __init__(self, cells: Optional[List[str]] = None):
        """
        Initializes a new board.

        Args:
            cells: Optional list of 9 cells. If None, creates an empty board.
        """
        if cells is None:
            self.cells = [EMPTY for _ in range(9)]
        else:
            self.cells = cells.copy()
        self.current_player = PLAYER_X

    def get_available_moves(self) -> List[int]:
        """
        Returns a list of indices for empty cells.

        Returns:
            List of available move indices (0-8).
        """
        return [i for i, cell in enumerate(self.cells) if cell == EMPTY]

    def make_move(self, index: int, player: str) -> bool:
        """
        Places a player's symbol at the given index.

        Args:
            index: Board position (0-8).
            player: Player symbol (X or O).

        Returns:
            True if move was successful, False otherwise.
        """
        if self.cells[index] == EMPTY:
            self.cells[index] = player
            self.current_player = PLAYER_O if player == PLAYER_X else PLAYER_X
            return True
        return False

    def undo_move(self, index: int):
        """
        Removes a symbol from the given index.

        Args:
            index: Board position (0-8).
        """
        player = self.cells[index]
        self.cells[index] = EMPTY
        self.current_player = player

    def is_full(self) -> bool:
        """
        Checks if the board has no empty cells.

        Returns:
            True if board is full, False otherwise.
        """
        return EMPTY not in self.cells

    def copy(self) -> 'Board':
        """
        Creates a deep copy of the board.

        Returns:
            A new Board instance with the same state.
        """
        new_board = Board(self.cells)
        new_board.current_player = self.current_player
        return new_board

    def __str__(self) -> str:
        """Returns a string representation of the board."""
        rows = []
        for i in range(0, 9, 3):
            row = ' | '.join(self.cells[i:i+3])
            rows.append(f" {row} ")
        return '\n-----------\n'.join(rows)
