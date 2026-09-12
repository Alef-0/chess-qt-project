"""Unit tests for chess piece movement and blocking rules."""

import os
import sys
from pathlib import Path
import pytest

# Ensure src is in sys.path
SRC_DIR = Path(__file__).parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Use offscreen platform for Qt in headless / test environments
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication
from pieces import BoardPieces, Piece, PieceColor, PieceType
from board import ChessBoardWidget


@pytest.fixture(scope="session")
def qapp():
    """Ensure a single QApplication instance exists for widget testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def create_empty_board() -> BoardPieces:
    """Helper to create a board with no pieces."""
    board = BoardPieces()
    board.grid = [[None for _ in range(8)] for _ in range(8)]
    return board


class TestPawnMovement:
    def test_white_pawn_initial_two_squares(self):
        board = BoardPieces()  # Standard starting setup
        moves = board.get_valid_moves(6, 4)  # e2 pawn
        assert (5, 4) in moves
        assert (4, 4) in moves
        assert len(moves) == 2

    def test_white_pawn_blocked_one_step(self):
        board = create_empty_board()
        board.set_piece(6, 4, Piece(PieceColor.WHITE, PieceType.PAWN))
        # Place blocking piece right in front
        board.set_piece(5, 4, Piece(PieceColor.BLACK, PieceType.PAWN))
        moves = board.get_valid_moves(6, 4)
        assert len(moves) == 0

    def test_white_pawn_blocked_two_step_only(self):
        board = create_empty_board()
        board.set_piece(6, 4, Piece(PieceColor.WHITE, PieceType.PAWN))
        # Square at distance 2 is blocked, distance 1 is empty
        board.set_piece(4, 4, Piece(PieceColor.BLACK, PieceType.PAWN))
        moves = board.get_valid_moves(6, 4)
        assert moves == [(5, 4)]

    def test_white_pawn_diagonal_captures(self):
        board = create_empty_board()
        board.set_piece(4, 4, Piece(PieceColor.WHITE, PieceType.PAWN))
        board.set_piece(3, 3, Piece(PieceColor.BLACK, PieceType.ROOK))   # Enemy left
        board.set_piece(3, 5, Piece(PieceColor.BLACK, PieceType.BISHOP)) # Enemy right
        board.set_piece(3, 4, Piece(PieceColor.BLACK, PieceType.PAWN))   # Enemy straight ahead (blocks forward)

        moves = set(board.get_valid_moves(4, 4))
        # Forward is blocked by enemy pawn, both diagonals have enemy pieces
        assert moves == {(3, 3), (3, 5)}

    def test_white_pawn_cannot_capture_friendly_piece(self):
        board = create_empty_board()
        board.set_piece(4, 4, Piece(PieceColor.WHITE, PieceType.PAWN))
        board.set_piece(3, 3, Piece(PieceColor.WHITE, PieceType.KNIGHT)) # Friendly piece
        moves = board.get_valid_moves(4, 4)
        assert (3, 3) not in moves
        assert (3, 4) in moves

    def test_black_pawn_movement_and_captures(self):
        board = BoardPieces()
        # Black d7 pawn (row 1, col 3)
        moves = board.get_valid_moves(1, 3)
        assert (2, 3) in moves
        assert (3, 3) in moves
        assert len(moves) == 2

        # Test capture
        board = create_empty_board()
        board.set_piece(1, 3, Piece(PieceColor.BLACK, PieceType.PAWN))
        board.set_piece(2, 4, Piece(PieceColor.WHITE, PieceType.KNIGHT))
        moves = set(board.get_valid_moves(1, 3))
        assert (2, 3) in moves
        assert (3, 3) in moves
        assert (2, 4) in moves
        assert len(moves) == 3


class TestRookMovement:
    def test_rook_unobstructed_center(self):
        board = create_empty_board()
        board.set_piece(3, 3, Piece(PieceColor.WHITE, PieceType.ROOK))
        moves = board.get_valid_moves(3, 3)
        # In an empty 8x8 board, rook has 14 moves (7 in row, 7 in col)
        assert len(moves) == 14

    def test_rook_blocked_by_friendly_and_captures_enemy(self):
        board = create_empty_board()
        board.set_piece(3, 3, Piece(PieceColor.WHITE, PieceType.ROOK))
        board.set_piece(3, 1, Piece(PieceColor.WHITE, PieceType.PAWN))   # Friendly left
        board.set_piece(3, 6, Piece(PieceColor.BLACK, PieceType.BISHOP)) # Enemy right
        board.set_piece(1, 3, Piece(PieceColor.BLACK, PieceType.KNIGHT)) # Enemy up
        board.set_piece(5, 3, Piece(PieceColor.WHITE, PieceType.QUEEN))  # Friendly down

        moves = set(board.get_valid_moves(3, 3))
        # Left: (3, 2) only; (3, 1) is friendly so blocked
        assert (3, 2) in moves
        assert (3, 1) not in moves
        assert (3, 0) not in moves

        # Right: (3, 4), (3, 5), (3, 6) capture; (3, 7) blocked
        assert (3, 4) in moves
        assert (3, 5) in moves
        assert (3, 6) in moves
        assert (3, 7) not in moves

        # Up: (2, 3), (1, 3) capture; (0, 3) blocked
        assert (2, 3) in moves
        assert (1, 3) in moves
        assert (0, 3) not in moves

        # Down: (4, 3) only; (5, 3) is friendly so blocked
        assert (4, 3) in moves
        assert (5, 3) not in moves


class TestBishopMovement:
    def test_bishop_unobstructed_center(self):
        board = create_empty_board()
        board.set_piece(4, 4, Piece(PieceColor.WHITE, PieceType.BISHOP))
        moves = board.get_valid_moves(4, 4)
        # 13 diagonal squares
        assert len(moves) == 13

    def test_bishop_blocking_and_capture(self):
        board = create_empty_board()
        board.set_piece(4, 4, Piece(PieceColor.WHITE, PieceType.BISHOP))
        board.set_piece(2, 2, Piece(PieceColor.WHITE, PieceType.PAWN))  # Friendly up-left
        board.set_piece(6, 6, Piece(PieceColor.BLACK, PieceType.ROOK))  # Enemy down-right

        moves = set(board.get_valid_moves(4, 4))
        # Up-left: (3, 3) only; (2, 2) blocked
        assert (3, 3) in moves
        assert (2, 2) not in moves
        assert (1, 1) not in moves

        # Down-right: (5, 5), (6, 6) capture; (7, 7) blocked
        assert (5, 5) in moves
        assert (6, 6) in moves
        assert (7, 7) not in moves


class TestQueenMovement:
    def test_queen_combines_rook_and_bishop(self):
        board = create_empty_board()
        board.set_piece(4, 4, Piece(PieceColor.WHITE, PieceType.QUEEN))
        moves = board.get_valid_moves(4, 4)
        # 14 orthogonal + 13 diagonal = 27 moves from (4, 4)
        assert len(moves) == 27


class TestKnightMovement:
    def test_knight_moves_and_jumping(self):
        board = create_empty_board()
        board.set_piece(4, 4, Piece(PieceColor.WHITE, PieceType.KNIGHT))
        # Surround knight with pieces to verify jumping
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr != 0 or dc != 0:
                    board.set_piece(4 + dr, 4 + dc, Piece(PieceColor.WHITE, PieceType.PAWN))

        # Put an enemy piece on one destination and a friendly piece on another
        board.set_piece(2, 3, Piece(PieceColor.BLACK, PieceType.ROOK))   # Enemy
        board.set_piece(2, 5, Piece(PieceColor.WHITE, PieceType.BISHOP)) # Friendly

        moves = set(board.get_valid_moves(4, 4))
        # Knight jumps over all 8 surrounding pawns!
        # Can capture enemy at (2, 3)
        assert (2, 3) in moves
        # Cannot capture friendly at (2, 5)
        assert (2, 5) not in moves
        # Empty landing squares: (3, 2), (3, 6), (5, 2), (5, 6), (6, 3), (6, 5)
        expected = {(2, 3), (3, 2), (3, 6), (5, 2), (5, 6), (6, 3), (6, 5)}
        assert moves == expected

    def test_knight_on_initial_board(self):
        board = BoardPieces()
        # White b1 knight (row 7, col 1)
        moves = set(board.get_valid_moves(7, 1))
        # Can jump over pawns to a3 (5, 0) and c3 (5, 2)
        assert moves == {(5, 0), (5, 2)}


class TestKingMovement:
    def test_king_center_moves(self):
        board = create_empty_board()
        board.set_piece(3, 3, Piece(PieceColor.WHITE, PieceType.KING))
        board.set_piece(2, 3, Piece(PieceColor.WHITE, PieceType.PAWN)) # Friendly up
        board.set_piece(2, 4, Piece(PieceColor.BLACK, PieceType.PAWN)) # Enemy up-right

        moves = set(board.get_valid_moves(3, 3))
        assert (2, 3) not in moves  # Blocked by friendly
        assert (2, 4) in moves      # Can capture enemy
        # King has 8 adjacent squares, 1 blocked = 7 valid moves
        assert len(moves) == 7

    def test_king_corner_bounds(self):
        board = create_empty_board()
        board.set_piece(0, 0, Piece(PieceColor.WHITE, PieceType.KING))
        moves = set(board.get_valid_moves(0, 0))
        assert moves == {(0, 1), (1, 0), (1, 1)}


class TestBoardWidgetInteraction:
    def test_widget_selection_and_moving(self, qapp):
        widget = ChessBoardWidget()
        widget.resize(600, 600)

        # Initial state: nothing selected
        assert widget.selected_square is None
        assert len(widget.valid_moves) == 0

        # Click on e2 white pawn (row 6, col 4)
        widget.handle_square_clicked(6, 4)
        assert widget.selected_square == (6, 4)
        assert (5, 4) in widget.valid_moves
        assert (4, 4) in widget.valid_moves

        # Move e2 pawn to e4 (row 4, col 4)
        widget.handle_square_clicked(4, 4)
        assert widget.selected_square is None
        assert len(widget.valid_moves) == 0
        assert widget.pieces.get_piece(6, 4) is None
        moved_piece = widget.pieces.get_piece(4, 4)
        assert moved_piece is not None
        assert moved_piece.piece_type == PieceType.PAWN
        assert moved_piece.color == PieceColor.WHITE

    def test_widget_switch_piece_selection(self, qapp):
        widget = ChessBoardWidget()
        widget.handle_square_clicked(6, 4)  # Select e2 pawn
        assert widget.selected_square == (6, 4)

        # Click on d2 pawn (row 6, col 3) -> should switch selection
        widget.handle_square_clicked(6, 3)
        assert widget.selected_square == (6, 3)
        assert (5, 3) in widget.valid_moves
        assert (4, 3) in widget.valid_moves

    def test_widget_deselect_on_invalid_click(self, qapp):
        widget = ChessBoardWidget()
        widget.handle_square_clicked(6, 4)  # Select e2 pawn
        assert widget.selected_square == (6, 4)

        # Click an empty square that is not a valid move (e.g. row 3, col 4)
        widget.handle_square_clicked(3, 4)
        assert widget.selected_square is None
        assert widget.valid_moves == []
