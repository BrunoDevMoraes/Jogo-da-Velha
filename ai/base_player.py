from abc import ABC, abstractmethod
from typing import Dict, Tuple
from game.board import Board


class BasePlayer(ABC):
    """Abstract base class for all AI players."""

    def __init__(self, symbol: str):
        """
        Initializes the player with a symbol.

        Args:
            symbol: The player's symbol (X or O).
        """
        self.symbol = symbol

    @abstractmethod
    def get_move(self, board: Board) -> Tuple[int, Dict]:
        """
        Determines the best move for the current board state.

        Args:
            board: The current game board.

        Returns:
            Tuple containing:
                - int: The chosen move index (0-8).
                - dict: Statistics about the decision (nodes_evaluated, time_ms).
        """
        pass

    def get_name(self) -> str:
        """
        Returns the name of the AI algorithm.

        Returns:
            Name of the player type.
        """
        return self.__class__.__name__
