"""Data structures for collecting complete game trees for various algorithms."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from game.board import Board
from game.game_logic import GameLogic
from utils.constants import PLAYER_X, PLAYER_O


@dataclass
class TreeNode:
    """Represents a node in a game search tree.

    Extended to support algorithm-specific information:
    - Alpha-Beta: pruned branches, alpha/beta values
    - Transposition Table: TT hits
    - Symmetry: canonical form detection
    """
    board_state: List[str]
    player: str  # Player who will move from this state
    is_maximizing: bool
    depth: int
    move_made: Optional[int] = None  # The move that led to this state
    score: Optional[int] = None
    children: List['TreeNode'] = field(default_factory=list)
    is_terminal: bool = False
    result: Optional[str] = None  # 'WIN_X', 'WIN_O', 'TIE', None

    # Alpha-Beta specific
    alpha: Optional[float] = None
    beta: Optional[float] = None
    was_pruned: bool = False  # True if this branch was cut off
    pruned_children_count: int = 0  # Number of children that were not explored

    # Transposition Table specific
    tt_hit: bool = False  # True if score came from TT lookup
    tt_flag: Optional[str] = None  # 'EXACT', 'LOWER', 'UPPER'

    # Symmetry specific
    canonical_form: Optional[tuple] = None
    is_symmetric_duplicate: bool = False  # True if equivalent position was already evaluated
    symmetry_source: Optional[int] = None  # Move index of the original symmetric position

    
    def to_dict(self) -> Dict[str, Any]:
        """Converts the node to a dictionary for JSON serialization."""
        base_dict = {
            'board': self.board_state,
            'player': self.player,
            'is_max': self.is_maximizing,
            'depth': self.depth,
            'move': self.move_made,
            'score': self.score,
            'is_terminal': self.is_terminal,
            'result': self.result,
            'children': [child.to_dict() for child in self.children],
            # Alpha-Beta
            'alpha': self.alpha,
            'beta': self.beta,
            'was_pruned': self.was_pruned,
            'pruned_children_count': self.pruned_children_count,
            # Transposition Table
            'tt_hit': self.tt_hit,
            'tt_flag': self.tt_flag,
            # Symmetry
            'is_symmetric_duplicate': self.is_symmetric_duplicate,
            'symmetry_source': self.symmetry_source,
        }
        return base_dict

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


class AlphaBetaTreeCollector:
    """Collects the Alpha-Beta pruning tree showing which branches were pruned."""

    def __init__(self, ai_symbol: str):
        """
        Initializes the Alpha-Beta tree collector.

        Args:
            ai_symbol: The symbol of the AI player (X or O).
        """
        self.ai_symbol = ai_symbol
        self.opponent = PLAYER_O if ai_symbol == PLAYER_X else PLAYER_X
        self.root: Optional[TreeNode] = None
        self.nodes_evaluated = 0
        self.nodes_pruned = 0

    def build_tree(self, board: Board) -> TreeNode:
        """
        Builds the Alpha-Beta tree from the current board state.

        Args:
            board: The current game board.

        Returns:
            The root node of the tree.
        """
        self.nodes_evaluated = 0
        self.nodes_pruned = 0
        self.root = self._build_node(
            board, 0, True, None,
            float('-inf'), float('inf')
        )
        return self.root

    def _build_node(
        self,
        board: Board,
        depth: int,
        is_maximizing: bool,
        move_made: Optional[int],
        alpha: float,
        beta: float
    ) -> TreeNode:
        """
        Recursively builds a tree node with Alpha-Beta pruning information.

        Args:
            board: Current board state.
            depth: Current depth in the tree.
            is_maximizing: True if this is a maximizing node.
            move_made: The move that led to this state.
            alpha: Current alpha value.
            beta: Current beta value.

        Returns:
            The constructed TreeNode with pruning information.
        """
        self.nodes_evaluated += 1
        current_player = self.ai_symbol if is_maximizing else self.opponent

        node = TreeNode(
            board_state=board.cells.copy(),
            player=current_player,
            is_maximizing=is_maximizing,
            depth=depth,
            move_made=move_made,
            alpha=alpha,
            beta=beta
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

        # Build children with Alpha-Beta pruning
        available_moves = board.get_available_moves()
        pruned = False

        if is_maximizing:
            value = float('-inf')
            for i, move in enumerate(available_moves):
                if pruned:
                    # Count remaining moves as pruned
                    node.pruned_children_count += 1
                    self.nodes_pruned += 1
                    continue

                board.make_move(move, current_player)
                child = self._build_node(
                    board, depth + 1, False, move, alpha, beta
                )
                node.children.append(child)
                board.undo_move(move)

                value = max(value, child.score)
                alpha = max(alpha, value)

                if beta <= alpha:
                    # Mark that pruning happened
                    child.was_pruned = False  # This child was evaluated
                    pruned = True
                    # Remaining children will be marked as pruned

            node.score = value
        else:
            value = float('inf')
            for i, move in enumerate(available_moves):
                if pruned:
                    node.pruned_children_count += 1
                    self.nodes_pruned += 1
                    continue

                board.make_move(move, current_player)
                child = self._build_node(
                    board, depth + 1, True, move, alpha, beta
                )
                node.children.append(child)
                board.undo_move(move)

                value = min(value, child.score)
                beta = min(beta, value)

                if beta <= alpha:
                    pruned = True

            node.score = value

        # Update final alpha/beta values
        node.alpha = alpha
        node.beta = beta

        return node

    def _evaluate(self, board: Board, depth: int) -> int:
        """Evaluates the board from the AI's perspective."""
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
            'root_score': self.root.score,
            'nodes_pruned': self.nodes_pruned,
            'algorithm': 'Alpha-Beta'
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


class AlphaBetaTTTreeCollector:
    """Collects Alpha-Beta tree with Transposition Table hit information."""

    def __init__(self, ai_symbol: str):
        """
        Initializes the Alpha-Beta TT tree collector.

        Args:
            ai_symbol: The symbol of the AI player (X or O).
        """
        self.ai_symbol = ai_symbol
        self.opponent = PLAYER_O if ai_symbol == PLAYER_X else PLAYER_X
        self.root: Optional[TreeNode] = None
        self.nodes_evaluated = 0
        self.nodes_pruned = 0
        self.tt_hits = 0
        self.tt_stores = 0
        self.transposition_table: Dict[tuple, Tuple[int, int, str]] = {}

    def build_tree(self, board: Board) -> TreeNode:
        """
        Builds the Alpha-Beta TT tree from the current board state.

        Args:
            board: The current game board.

        Returns:
            The root node of the tree.
        """
        self.nodes_evaluated = 0
        self.nodes_pruned = 0
        self.tt_hits = 0
        self.tt_stores = 0
        self.transposition_table.clear()
        self.root = self._build_node(
            board, 0, True, None,
            float('-inf'), float('inf')
        )
        return self.root

    def _board_hash(self, board: Board) -> tuple:
        """Creates a hashable key for the board state."""
        return tuple(board.cells)

    def _build_node(
        self,
        board: Board,
        depth: int,
        is_maximizing: bool,
        move_made: Optional[int],
        alpha: float,
        beta: float
    ) -> TreeNode:
        """
        Recursively builds a tree node with TT lookup information.
        """
        current_player = self.ai_symbol if is_maximizing else self.opponent
        original_alpha = alpha
        board_hash = self._board_hash(board)

        node = TreeNode(
            board_state=board.cells.copy(),
            player=current_player,
            is_maximizing=is_maximizing,
            depth=depth,
            move_made=move_made,
            alpha=alpha,
            beta=beta
        )

        # Check TT for existing entry
        if board_hash in self.transposition_table:
            stored_score, stored_depth, flag = self.transposition_table[board_hash]
            if stored_depth <= depth:
                if flag == 'EXACT':
                    node.tt_hit = True
                    node.tt_flag = flag
                    node.score = stored_score
                    node.is_terminal = True
                    self.tt_hits += 1
                    return node
                elif flag == 'LOWER' and stored_score >= beta:
                    node.tt_hit = True
                    node.tt_flag = flag
                    node.score = stored_score
                    node.is_terminal = True
                    self.tt_hits += 1
                    return node
                elif flag == 'UPPER' and stored_score <= alpha:
                    node.tt_hit = True
                    node.tt_flag = flag
                    node.score = stored_score
                    node.is_terminal = True
                    self.tt_hits += 1
                    return node

        self.nodes_evaluated += 1

        # Check terminal state
        winner = GameLogic.check_winner(board)
        if winner:
            node.is_terminal = True
            node.result = 'WIN_X' if winner == PLAYER_X else 'WIN_O'
            node.score = self._evaluate(board, depth)
            self._store_tt(board_hash, depth, node.score, 'EXACT')
            return node

        if board.is_full():
            node.is_terminal = True
            node.result = 'TIE'
            node.score = 0
            self._store_tt(board_hash, depth, 0, 'EXACT')
            return node

        # Build children with Alpha-Beta pruning
        available_moves = board.get_available_moves()
        pruned = False

        if is_maximizing:
            value = float('-inf')
            for move in available_moves:
                if pruned:
                    node.pruned_children_count += 1
                    self.nodes_pruned += 1
                    continue

                board.make_move(move, current_player)
                child = self._build_node(board, depth + 1, False, move, alpha, beta)
                node.children.append(child)
                board.undo_move(move)

                value = max(value, child.score)
                alpha = max(alpha, value)

                if beta <= alpha:
                    pruned = True

            node.score = value

            # Store in TT
            if value <= original_alpha:
                flag = 'UPPER'
            elif value >= beta:
                flag = 'LOWER'
            else:
                flag = 'EXACT'
            self._store_tt(board_hash, depth, value, flag)
            node.tt_flag = flag
        else:
            value = float('inf')
            for move in available_moves:
                if pruned:
                    node.pruned_children_count += 1
                    self.nodes_pruned += 1
                    continue

                board.make_move(move, current_player)
                child = self._build_node(board, depth + 1, True, move, alpha, beta)
                node.children.append(child)
                board.undo_move(move)

                value = min(value, child.score)
                beta = min(beta, value)

                if beta <= alpha:
                    pruned = True

            node.score = value

            if value <= original_alpha:
                flag = 'UPPER'
            elif value >= beta:
                flag = 'LOWER'
            else:
                flag = 'EXACT'
            self._store_tt(board_hash, depth, value, flag)
            node.tt_flag = flag

        node.alpha = alpha
        node.beta = beta

        return node

    def _store_tt(self, board_hash: tuple, depth: int, score: int, flag: str):
        """Stores a position in the transposition table."""
        self.transposition_table[board_hash] = (score, depth, flag)
        self.tt_stores += 1

    def _evaluate(self, board: Board, depth: int) -> int:
        """Evaluates the board from the AI's perspective."""
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

        total_lookups = self.tt_hits + self.nodes_evaluated
        hit_rate = (self.tt_hits / total_lookups * 100) if total_lookups > 0 else 0

        return {
            'total_nodes': self.root.count_nodes(),
            'leaf_nodes': self.root.count_leaves(),
            'max_depth': self.root.get_max_depth(),
            'root_score': self.root.score,
            'nodes_pruned': self.nodes_pruned,
            'tt_hits': self.tt_hits,
            'tt_stores': self.tt_stores,
            'tt_hit_rate': round(hit_rate, 1),
            'algorithm': 'Alpha-Beta + TT'
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


class AlphaBetaSymmetryTreeCollector:
    """Collects Alpha-Beta tree with D4 symmetry reduction information."""

    def __init__(self, ai_symbol: str):
        """
        Initializes the Alpha-Beta Symmetry tree collector.

        Args:
            ai_symbol: The symbol of the AI player (X or O).
        """
        self.ai_symbol = ai_symbol
        self.opponent = PLAYER_O if ai_symbol == PLAYER_X else PLAYER_X
        self.root: Optional[TreeNode] = None
        self.nodes_evaluated = 0
        self.nodes_pruned = 0
        self.symmetry_hits = 0
        self.unique_positions = 0
        self.transposition_table: Dict[tuple, Tuple[int, int, str]] = {}

    def _get_canonical_form(self, cells: List[str]) -> tuple:
        """Gets the canonical (lexicographically smallest) form of the board."""
        # All 8 symmetries of D4 group
        def rotate_90(b):
            return [b[6], b[3], b[0], b[7], b[4], b[1], b[8], b[5], b[2]]

        def reflect_horizontal(b):
            return [b[6], b[7], b[8], b[3], b[4], b[5], b[0], b[1], b[2]]

        def reflect_vertical(b):
            return [b[2], b[1], b[0], b[5], b[4], b[3], b[8], b[7], b[6]]

        forms = [cells]
        current = cells
        # 3 rotations
        for _ in range(3):
            current = rotate_90(current)
            forms.append(current)
        # Reflect and 3 rotations
        reflected = reflect_horizontal(cells)
        forms.append(reflected)
        current = reflected
        for _ in range(3):
            current = rotate_90(current)
            forms.append(current)

        # Return lexicographically smallest
        return tuple(min(tuple(f) for f in forms))

    def build_tree(self, board: Board) -> TreeNode:
        """
        Builds the Alpha-Beta Symmetry tree from the current board state.

        Args:
            board: The current game board.

        Returns:
            The root node of the tree.
        """
        self.nodes_evaluated = 0
        self.nodes_pruned = 0
        self.symmetry_hits = 0
        self.transposition_table.clear()
        self.root = self._build_node(
            board, 0, True, None,
            float('-inf'), float('inf')
        )
        self.unique_positions = len(self.transposition_table)
        return self.root

    def _build_node(
        self,
        board: Board,
        depth: int,
        is_maximizing: bool,
        move_made: Optional[int],
        alpha: float,
        beta: float
    ) -> TreeNode:
        """
        Recursively builds a tree node with symmetry detection.
        """
        current_player = self.ai_symbol if is_maximizing else self.opponent
        original_alpha = alpha
        canonical = self._get_canonical_form(board.cells)

        node = TreeNode(
            board_state=board.cells.copy(),
            player=current_player,
            is_maximizing=is_maximizing,
            depth=depth,
            move_made=move_made,
            alpha=alpha,
            beta=beta,
            canonical_form=canonical
        )

        # Check TT using canonical form
        if canonical in self.transposition_table:
            stored_score, stored_depth, flag = self.transposition_table[canonical]
            if stored_depth <= depth:
                if flag == 'EXACT':
                    node.tt_hit = True
                    node.tt_flag = flag
                    node.is_symmetric_duplicate = True
                    node.score = stored_score
                    node.is_terminal = True
                    self.symmetry_hits += 1
                    return node
                elif flag == 'LOWER' and stored_score >= beta:
                    node.tt_hit = True
                    node.tt_flag = flag
                    node.is_symmetric_duplicate = True
                    node.score = stored_score
                    node.is_terminal = True
                    self.symmetry_hits += 1
                    return node
                elif flag == 'UPPER' and stored_score <= alpha:
                    node.tt_hit = True
                    node.tt_flag = flag
                    node.is_symmetric_duplicate = True
                    node.score = stored_score
                    node.is_terminal = True
                    self.symmetry_hits += 1
                    return node

        self.nodes_evaluated += 1

        # Check terminal state
        winner = GameLogic.check_winner(board)
        if winner:
            node.is_terminal = True
            node.result = 'WIN_X' if winner == PLAYER_X else 'WIN_O'
            node.score = self._evaluate(board, depth)
            self._store_tt(canonical, depth, node.score, 'EXACT')
            return node

        if board.is_full():
            node.is_terminal = True
            node.result = 'TIE'
            node.score = 0
            self._store_tt(canonical, depth, 0, 'EXACT')
            return node

        # Build children with Alpha-Beta pruning
        available_moves = board.get_available_moves()
        pruned = False

        if is_maximizing:
            value = float('-inf')
            for move in available_moves:
                if pruned:
                    node.pruned_children_count += 1
                    self.nodes_pruned += 1
                    continue

                board.make_move(move, current_player)
                child = self._build_node(board, depth + 1, False, move, alpha, beta)
                node.children.append(child)
                board.undo_move(move)

                value = max(value, child.score)
                alpha = max(alpha, value)

                if beta <= alpha:
                    pruned = True

            node.score = value

            if value <= original_alpha:
                flag = 'UPPER'
            elif value >= beta:
                flag = 'LOWER'
            else:
                flag = 'EXACT'
            self._store_tt(canonical, depth, value, flag)
            node.tt_flag = flag
        else:
            value = float('inf')
            for move in available_moves:
                if pruned:
                    node.pruned_children_count += 1
                    self.nodes_pruned += 1
                    continue

                board.make_move(move, current_player)
                child = self._build_node(board, depth + 1, True, move, alpha, beta)
                node.children.append(child)
                board.undo_move(move)

                value = min(value, child.score)
                beta = min(beta, value)

                if beta <= alpha:
                    pruned = True

            node.score = value

            if value <= original_alpha:
                flag = 'UPPER'
            elif value >= beta:
                flag = 'LOWER'
            else:
                flag = 'EXACT'
            self._store_tt(canonical, depth, value, flag)
            node.tt_flag = flag

        node.alpha = alpha
        node.beta = beta

        return node

    def _store_tt(self, canonical: tuple, depth: int, score: int, flag: str):
        """Stores a canonical position in the transposition table."""
        self.transposition_table[canonical] = (score, depth, flag)

    def _evaluate(self, board: Board, depth: int) -> int:
        """Evaluates the board from the AI's perspective."""
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
            'root_score': self.root.score,
            'nodes_pruned': self.nodes_pruned,
            'symmetry_hits': self.symmetry_hits,
            'unique_positions': self.unique_positions,
            'algorithm': 'Alpha-Beta + Symmetry'
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
