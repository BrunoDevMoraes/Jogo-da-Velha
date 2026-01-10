"""Data structures for collecting the complete Minimax tree."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from game.board import Board
from game.game_logic import GameLogic
from utils.constants import PLAYER_X, PLAYER_O


@dataclass
class TreeNode:
    """Represents a node in the Minimax tree."""
    board_state: List[str]
    player: str  # Player who will move from this state
    is_maximizing: bool
    depth: int
    move_made: Optional[int] = None  # The move that led to this state
    score: Optional[int] = None
    children: List['TreeNode'] = field(default_factory=list)
    is_terminal: bool = False
    result: Optional[str] = None  # 'WIN_X', 'WIN_O', 'TIE', None

    def to_dict(self) -> Dict[str, Any]:
        """Converts the node to a dictionary for JSON serialization."""
        return {
            'board': self.board_state,
            'player': self.player,
            'is_max': self.is_maximizing,
            'depth': self.depth,
            'move': self.move_made,
            'score': self.score,
            'is_terminal': self.is_terminal,
            'result': self.result,
            'children': [child.to_dict() for child in self.children]
        }

    def count_nodes(self) -> int:
        """Counts total nodes in this subtree."""
        return 1 + sum(child.count_nodes() for child in self.children)

    def count_leaves(self) -> int:
        """Counts leaf nodes in this subtree."""
        if not self.children:
            return 1
        return sum(child.count_leaves() for child in self.children)

    def get_max_depth(self) -> int:
        """Returns the maximum depth of this subtree."""
        if not self.children:
            return self.depth
        return max(child.get_max_depth() for child in self.children)


class MinimaxTreeCollector:
    """Collects the complete Minimax tree during algorithm execution."""

    def __init__(self, ai_symbol: str):
        """
        Initializes the tree collector.

        Args:
            ai_symbol: The symbol of the AI player (X or O).
        """
        self.ai_symbol = ai_symbol
        self.opponent = PLAYER_O if ai_symbol == PLAYER_X else PLAYER_X
        self.root: Optional[TreeNode] = None
        self.nodes_evaluated = 0

    def build_tree(self, board: Board) -> TreeNode:
        """
        Builds the complete Minimax tree from the current board state.

        Args:
            board: The current game board.

        Returns:
            The root node of the tree.
        """
        self.nodes_evaluated = 0
        self.root = self._build_node(board, 0, True, None)
        return self.root

    def _build_node(
        self,
        board: Board,
        depth: int,
        is_maximizing: bool,
        move_made: Optional[int]
    ) -> TreeNode:
        """
        Recursively builds a tree node and its children.

        Args:
            board: Current board state.
            depth: Current depth in the tree.
            is_maximizing: True if this is a maximizing node.
            move_made: The move that led to this state.

        Returns:
            The constructed TreeNode.
        """
        self.nodes_evaluated += 1
        current_player = self.ai_symbol if is_maximizing else self.opponent

        node = TreeNode(
            board_state=board.cells.copy(),
            player=current_player,
            is_maximizing=is_maximizing,
            depth=depth,
            move_made=move_made
        )

        # Check terminal state
        winner = GameLogic.check_winner(board)
        if winner:
            node.is_terminal = True
            node.result = 'WIN_X' if winner == PLAYER_X else 'WIN_O'
            node.score = self._evaluate(board, depth)
            return node

        if board.is_full():
            node.is_terminal = True
            node.result = 'TIE'
            node.score = 0
            return node

        # Build children for each possible move
        available_moves = board.get_available_moves()

        for move in available_moves:
            board.make_move(move, current_player)
            child = self._build_node(board, depth + 1, not is_maximizing, move)
            node.children.append(child)
            board.undo_move(move)

        # Calculate score using minimax logic
        if is_maximizing:
            node.score = max(child.score for child in node.children)
        else:
            node.score = min(child.score for child in node.children)

        return node

    def _evaluate(self, board: Board, depth: int) -> int:
        """
        Evaluates the board from the AI's perspective.

        Args:
            board: The board to evaluate.
            depth: Current depth.

        Returns:
            Score value.
        """
        winner = GameLogic.check_winner(board)
        if winner == self.ai_symbol:
            return 10 - depth
        elif winner is not None:
            return -10 + depth
        return 0

    def get_statistics(self) -> Dict[str, Any]:
        """Returns statistics about the tree."""
        if not self.root:
            return {}

        return {
            'total_nodes': self.root.count_nodes(),
            'leaf_nodes': self.root.count_leaves(),
            'max_depth': self.root.get_max_depth(),
            'root_score': self.root.score
        }

    def get_tree_for_visualization(self) -> Dict[str, Any]:
        """Returns the tree structure for visualization."""
        if not self.root:
            return {}

        return {
            'tree': self.root.to_dict(),
            'stats': self.get_statistics(),
            'ai_symbol': self.ai_symbol
        }
