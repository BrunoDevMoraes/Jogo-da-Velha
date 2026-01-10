"""Symmetry utilities for Tic-Tac-Toe board using the D4 dihedral group.

The D4 group has 8 symmetries:
- 4 rotations: 0°, 90°, 180°, 270°
- 4 reflections: horizontal, vertical, main diagonal, anti-diagonal

Board indices:
    0 | 1 | 2
    ---------
    3 | 4 | 5
    ---------
    6 | 7 | 8
"""

from typing import List, Tuple


# Transformation mappings for each symmetry operation
# Each tuple shows where index i moves to in the transformed board

# Identity (no change)
IDENTITY = (0, 1, 2, 3, 4, 5, 6, 7, 8)

# Rotation 90° clockwise
# 0 1 2    6 3 0
# 3 4 5 -> 7 4 1
# 6 7 8    8 5 2
ROTATE_90 = (6, 3, 0, 7, 4, 1, 8, 5, 2)

# Rotation 180°
# 0 1 2    8 7 6
# 3 4 5 -> 5 4 3
# 6 7 8    2 1 0
ROTATE_180 = (8, 7, 6, 5, 4, 3, 2, 1, 0)

# Rotation 270° clockwise (or 90° counter-clockwise)
# 0 1 2    2 5 8
# 3 4 5 -> 1 4 7
# 6 7 8    0 3 6
ROTATE_270 = (2, 5, 8, 1, 4, 7, 0, 3, 6)

# Horizontal reflection (flip over vertical axis)
# 0 1 2    2 1 0
# 3 4 5 -> 5 4 3
# 6 7 8    8 7 6
REFLECT_HORIZONTAL = (2, 1, 0, 5, 4, 3, 8, 7, 6)

# Vertical reflection (flip over horizontal axis)
# 0 1 2    6 7 8
# 3 4 5 -> 3 4 5
# 6 7 8    0 1 2
REFLECT_VERTICAL = (6, 7, 8, 3, 4, 5, 0, 1, 2)

# Main diagonal reflection (top-left to bottom-right)
# 0 1 2    0 3 6
# 3 4 5 -> 1 4 7
# 6 7 8    2 5 8
REFLECT_MAIN_DIAGONAL = (0, 3, 6, 1, 4, 7, 2, 5, 8)

# Anti-diagonal reflection (top-right to bottom-left)
# 0 1 2    8 5 2
# 3 4 5 -> 7 4 1
# 6 7 8    6 3 0
REFLECT_ANTI_DIAGONAL = (8, 5, 2, 7, 4, 1, 6, 3, 0)

# All 8 symmetries of D4 group
ALL_SYMMETRIES = [
    IDENTITY,
    ROTATE_90,
    ROTATE_180,
    ROTATE_270,
    REFLECT_HORIZONTAL,
    REFLECT_VERTICAL,
    REFLECT_MAIN_DIAGONAL,
    REFLECT_ANTI_DIAGONAL,
]


def apply_symmetry(board_state: List[str], symmetry: Tuple[int, ...]) -> Tuple[str, ...]:
    """
    Applies a symmetry transformation to a board state.

    Args:
        board_state: List of 9 elements representing the board.
        symmetry: Tuple mapping indices to their transformed positions.

    Returns:
        Transformed board state as a tuple.
    """
    return tuple(board_state[symmetry[i]] for i in range(9))


def get_all_symmetric_forms(board_state: List[str]) -> List[Tuple[str, ...]]:
    """
    Gets all 8 symmetric forms of a board state.

    Args:
        board_state: List of 9 elements representing the board.

    Returns:
        List of 8 tuples, each representing a symmetric form.
    """
    return [apply_symmetry(board_state, sym) for sym in ALL_SYMMETRIES]


def get_canonical_form(board_state: List[str]) -> Tuple[str, ...]:
    """
    Returns the canonical (lexicographically smallest) form of a board state.

    This ensures that all symmetric positions map to the same canonical form,
    enabling effective transposition table lookups.

    Args:
        board_state: List of 9 elements representing the board.

    Returns:
        The canonical form as a tuple.
    """
    symmetric_forms = get_all_symmetric_forms(board_state)
    return min(symmetric_forms)


def get_symmetry_index(board_state: List[str]) -> int:
    """
    Returns the index of the symmetry that produces the canonical form.

    Args:
        board_state: List of 9 elements representing the board.

    Returns:
        Index (0-7) of the symmetry transformation.
    """
    symmetric_forms = get_all_symmetric_forms(board_state)
    canonical = min(symmetric_forms)
    return symmetric_forms.index(canonical)


def transform_move(move: int, symmetry_index: int) -> int:
    """
    Transforms a move index according to a symmetry.

    When we find the best move in a canonical form, we need to
    transform it back to the original board orientation.

    Args:
        move: Move index (0-8) in the canonical form.
        symmetry_index: Index of the symmetry that was applied.

    Returns:
        Move index in the original board orientation.
    """
    # The inverse transformation: if applying symmetry S to board gives position P,
    # then to get the move in original coords, we need to find where 'move' came from
    symmetry = ALL_SYMMETRIES[symmetry_index]
    # symmetry[i] tells us where position i goes
    # We need the inverse: where did position 'move' come from?
    return symmetry.index(move)


def get_inverse_symmetry(symmetry_index: int) -> Tuple[int, ...]:
    """
    Gets the inverse symmetry transformation.

    Args:
        symmetry_index: Index of the symmetry (0-7).

    Returns:
        The inverse symmetry mapping.
    """
    symmetry = ALL_SYMMETRIES[symmetry_index]
    inverse = [0] * 9
    for i, j in enumerate(symmetry):
        inverse[j] = i
    return tuple(inverse)


def count_unique_positions(board_states: List[List[str]]) -> int:
    """
    Counts the number of unique positions considering symmetries.

    Args:
        board_states: List of board states.

    Returns:
        Number of unique positions.
    """
    canonical_forms = set()
    for state in board_states:
        canonical_forms.add(get_canonical_form(state))
    return len(canonical_forms)
