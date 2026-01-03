from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class TreeNode:
    """Represents a node in the Minimax search tree."""
    node_id: int
    parent_id: Optional[int]
    depth: int
    node_type: str  # 'MAX', 'MIN', 'TERMINAL'
    board_state: List[str]
    move: Optional[int]
    score: Optional[int] = None
    is_optimal_path: bool = False
    terminal_type: Optional[str] = None  # 'WIN', 'LOSE', 'TIE'


class NodeCollector:
    """Collects node data during Minimax algorithm execution."""

    def __init__(self):
        """Initializes an empty node collector."""
        self.nodes: List[TreeNode] = []
        self._node_counter = 0
        self._optimal_path_ids: set = set()

    def add_node(
        self,
        parent_id: Optional[int],
        depth: int,
        node_type: str,
        board_state: List[str],
        move: Optional[int] = None,
        score: Optional[int] = None,
        terminal_type: Optional[str] = None
    ) -> int:
        """
        Adds a new node to the collection.

        Args:
            parent_id: ID of the parent node (None for root).
            depth: Depth in the search tree.
            node_type: Type of node ('MAX', 'MIN', or 'TERMINAL').
            board_state: Current board state as list.
            move: The move that led to this state.
            score: Evaluated score for this node.
            terminal_type: Type of terminal state if applicable.

        Returns:
            The ID of the newly created node.
        """
        node_id = self._node_counter
        self._node_counter += 1

        node = TreeNode(
            node_id=node_id,
            parent_id=parent_id,
            depth=depth,
            node_type=node_type,
            board_state=board_state.copy(),
            move=move,
            score=score,
            terminal_type=terminal_type
        )

        self.nodes.append(node)
        return node_id

    def update_score(self, node_id: int, score: int):
        """
        Updates the score of an existing node.

        Args:
            node_id: ID of the node to update.
            score: New score value.
        """
        if 0 <= node_id < len(self.nodes):
            self.nodes[node_id].score = score

    def mark_optimal_path(self, path_ids: List[int]):
        """
        Marks nodes as part of the optimal path.

        Args:
            path_ids: List of node IDs in the optimal path.
        """
        self._optimal_path_ids = set(path_ids)
        for node_id in path_ids:
            if 0 <= node_id < len(self.nodes):
                self.nodes[node_id].is_optimal_path = True

    def get_nodes(self) -> List[TreeNode]:
        """
        Returns all collected nodes.

        Returns:
            List of TreeNode objects.
        """
        return self.nodes

    def get_edges(self) -> List[tuple]:
        """
        Returns all parent-child edges.

        Returns:
            List of (parent_id, child_id) tuples.
        """
        edges = []
        for node in self.nodes:
            if node.parent_id is not None:
                edges.append((node.parent_id, node.node_id))
        return edges

    def clear(self):
        """Clears all collected data for next execution."""
        self.nodes = []
        self._node_counter = 0
        self._optimal_path_ids = set()

    def get_statistics(self) -> Dict:
        """
        Returns statistics about the collected tree.

        Returns:
            Dictionary with tree statistics.
        """
        if not self.nodes:
            return {'total_nodes': 0}

        max_depth = max(node.depth for node in self.nodes)
        terminal_count = sum(1 for node in self.nodes if node.node_type == 'TERMINAL')

        return {
            'total_nodes': len(self.nodes),
            'max_depth': max_depth,
            'terminal_nodes': terminal_count,
            'optimal_path_length': len(self._optimal_path_ids)
        }
