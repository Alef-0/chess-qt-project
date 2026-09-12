"""Check, checkmate, and move legality detection logic for chess."""

from typing import List, Optional, Tuple
from pieces import BoardPieces, Piece, PieceColor, PieceType


def find_king(board: BoardPieces, color: PieceColor) -> Optional[Tuple[int, int]]:
    """Finds the coordinates (row, col) of the king of the specified color."""
    for r in range(8):
        for c in range(8):
            piece = board.get_piece(r, c)
            if piece is not None and piece.piece_type == PieceType.KING and piece.color == color:
                return (r, c)
    return None


def is_in_check(board: BoardPieces, color: PieceColor) -> bool:
    """Returns True if the king of the given color is currently under attack."""
    king_pos = find_king(board, color)
    if king_pos is None:
        return False
    enemy_color = PieceColor.BLACK if color == PieceColor.WHITE else PieceColor.WHITE
    return board.is_square_attacked(king_pos[0], king_pos[1], enemy_color)


def is_move_legal(
    board: BoardPieces,
    from_row: int,
    from_col: int,
    to_row: int,
    to_col: int,
    promotion: Optional[PieceType] = None,
) -> bool:
    """Checks if making the move leaves the moving player's king in check.

    Directly evaluates king safety by temporarily simulating the candidate move on the
    board grid and reverting it afterwards, avoiding an exhaustive move search.
    """
    moving_piece = board.get_piece(from_row, from_col)
    if moving_piece is None:
        return False

    category = board.get_move_category(from_row, from_col, to_row, to_col)
    orig_to_piece = board.get_piece(to_row, to_col)

    ep_pawn = None
    if category == "en_passant":
        ep_pawn = board.get_piece(from_row, to_col)
        board.grid[from_row][to_col] = None

    castling_rook = None
    orig_rook_pos = None
    dest_rook_pos = None
    if category == "castling":
        rook_col = 7 if to_col == 6 else 0
        target_rook_col = 5 if to_col == 6 else 3
        castling_rook = board.get_piece(from_row, rook_col)
        orig_rook_pos = (from_row, rook_col)
        dest_rook_pos = (from_row, target_rook_col)
        board.grid[from_row][target_rook_col] = castling_rook
        board.grid[from_row][rook_col] = None

    placed_piece = moving_piece
    if promotion is not None:
        placed_piece = Piece(moving_piece.color, promotion)

    # Apply candidate move to grid
    board.grid[to_row][to_col] = placed_piece
    board.grid[from_row][from_col] = None

    # Verify if moving player's king is safe
    king_safe = not is_in_check(board, moving_piece.color)

    # Revert board grid to exact original state
    board.grid[from_row][from_col] = moving_piece
    board.grid[to_row][to_col] = orig_to_piece

    if category == "en_passant":
        board.grid[from_row][to_col] = ep_pawn

    if category == "castling" and orig_rook_pos and dest_rook_pos:
        board.grid[dest_rook_pos[0]][dest_rook_pos[1]] = None
        board.grid[orig_rook_pos[0]][orig_rook_pos[1]] = castling_rook

    return king_safe


def get_legal_moves(board: BoardPieces, row: int, col: int) -> List[Tuple[int, int]]:
    """Returns all pseudo-legal moves for the piece at (row, col) that do not leave own king in check."""
    valid_moves = board.get_valid_moves(row, col)
    return [(r, c) for r, c in valid_moves if is_move_legal(board, row, col, r, c)]


def has_any_legal_moves(board: BoardPieces, color: PieceColor) -> bool:
    """Checks if the player of the given color has at least one legal move.

    Iterates over all pieces of the given color and short-circuits as soon as one legal move is found.
    """
    for r in range(8):
        for c in range(8):
            piece = board.get_piece(r, c)
            if piece is not None and piece.color == color:
                candidate_moves = board.get_valid_moves(r, c)
                for to_r, to_c in candidate_moves:
                    if is_move_legal(board, r, c, to_r, to_c):
                        return True
    return False


def is_checkmate(board: BoardPieces, color: PieceColor) -> bool:
    """Returns True if the player of the given color is in checkmate (in check with no legal moves)."""
    return is_in_check(board, color) and not has_any_legal_moves(board, color)


def move_leads_to_mate(
    board: BoardPieces,
    from_row: int,
    from_col: int,
    to_row: int,
    to_col: int,
    promotion: Optional[PieceType] = None,
) -> Tuple[bool, Optional[PieceColor]]:
    """Evaluates whether the candidate move results in a game-ending mate state.

    Simulates the move and checks:
    1. If the opponent is checkmated -> returns (True, moving_piece.color)
    2. If the moving player's king is left in check/mate -> returns (True, enemy_color)

    Returns:
        (True, winning_color) if the move leads to a mate.
        (False, None) otherwise.
    """
    moving_piece = board.get_piece(from_row, from_col)
    if moving_piece is None:
        return False, None

    enemy_color = PieceColor.BLACK if moving_piece.color == PieceColor.WHITE else PieceColor.WHITE
    category = board.get_move_category(from_row, from_col, to_row, to_col)
    orig_to_piece = board.get_piece(to_row, to_col)

    ep_pawn = None
    if category == "en_passant":
        ep_pawn = board.get_piece(from_row, to_col)
        board.grid[from_row][to_col] = None

    castling_rook = None
    orig_rook_pos = None
    dest_rook_pos = None
    if category == "castling":
        rook_col = 7 if to_col == 6 else 0
        target_rook_col = 5 if to_col == 6 else 3
        castling_rook = board.get_piece(from_row, rook_col)
        orig_rook_pos = (from_row, rook_col)
        dest_rook_pos = (from_row, target_rook_col)
        board.grid[from_row][target_rook_col] = castling_rook
        board.grid[from_row][rook_col] = None

    placed_piece = moving_piece
    if promotion is not None:
        placed_piece = Piece(moving_piece.color, promotion)

    # Apply move temporarily
    board.grid[to_row][to_col] = placed_piece
    board.grid[from_row][from_col] = None

    leads_to_mate = False
    winner: Optional[PieceColor] = None

    if is_checkmate(board, enemy_color):
        leads_to_mate = True
        winner = moving_piece.color
    elif is_in_check(board, moving_piece.color):
        leads_to_mate = True
        winner = enemy_color

    # Revert board
    board.grid[from_row][from_col] = moving_piece
    board.grid[to_row][to_col] = orig_to_piece

    if category == "en_passant":
        board.grid[from_row][to_col] = ep_pawn

    if category == "castling" and orig_rook_pos and dest_rook_pos:
        board.grid[dest_rook_pos[0]][dest_rook_pos[1]] = None
        board.grid[orig_rook_pos[0]][orig_rook_pos[1]] = castling_rook

    return leads_to_mate, winner
