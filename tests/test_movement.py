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


class TestEnPassantMovement:
    def test_white_en_passant_capture(self):
        board = create_empty_board()
        # White pawn on rank 5 (row 3, col 4: e5)
        board.set_piece(3, 4, Piece(PieceColor.WHITE, PieceType.PAWN))
        # Black pawn on rank 7 (row 1, col 3: d7)
        board.set_piece(1, 3, Piece(PieceColor.BLACK, PieceType.PAWN))

        # Black advances d7 to d5 (row 1, col 3 -> row 3, col 3)
        board.move_piece(1, 3, 3, 3)
        assert board.en_passant_target == (2, 3)

        # White e5 pawn should have en passant move to (2, 3) in addition to (2, 4)
        moves = board.get_valid_moves(3, 4)
        assert (2, 3) in moves
        assert (2, 4) in moves

        # White captures en passant
        captured = board.move_piece(3, 4, 2, 3)
        assert captured is not None
        assert captured.color == PieceColor.BLACK
        assert captured.piece_type == PieceType.PAWN
        # Black pawn at (3, 3) must be gone!
        assert board.get_piece(3, 3) is None
        # White pawn is now on (2, 3)
        assert board.get_piece(2, 3) is not None
        assert board.get_piece(2, 3).color == PieceColor.WHITE
        # en_passant_target is cleared
        assert board.en_passant_target is None

    def test_black_en_passant_capture(self):
        board = create_empty_board()
        # Black pawn on rank 4 (row 4, col 3: d4)
        board.set_piece(4, 3, Piece(PieceColor.BLACK, PieceType.PAWN))
        # White pawn on rank 2 (row 6, col 4: e2)
        board.set_piece(6, 4, Piece(PieceColor.WHITE, PieceType.PAWN))

        # White advances e2 to e4 (row 6, col 4 -> row 4, col 4)
        board.move_piece(6, 4, 4, 4)
        assert board.en_passant_target == (5, 4)

        # Black d4 pawn can capture en passant to (5, 4)
        moves = board.get_valid_moves(4, 3)
        assert (5, 4) in moves

        # Black captures en passant
        captured = board.move_piece(4, 3, 5, 4)
        assert captured is not None
        assert captured.color == PieceColor.WHITE
        assert captured.piece_type == PieceType.PAWN
        assert board.get_piece(4, 4) is None
        assert board.get_piece(5, 4).color == PieceColor.BLACK
        assert board.en_passant_target is None

    def test_en_passant_expires_after_other_move(self):
        board = create_empty_board()
        board.set_piece(3, 4, Piece(PieceColor.WHITE, PieceType.PAWN))  # White e5
        board.set_piece(1, 3, Piece(PieceColor.BLACK, PieceType.PAWN))  # Black d7
        board.set_piece(0, 0, Piece(PieceColor.BLACK, PieceType.ROOK))  # Black a8

        # Black advances d7 to d5
        board.move_piece(1, 3, 3, 3)
        assert board.en_passant_target == (2, 3)

        # Black makes another move (e.g. rook moves a8 to b8)
        board.move_piece(0, 0, 0, 1)
        # en passant target is expired!
        assert board.en_passant_target is None

        # White e5 pawn can NO LONGER capture en passant
        moves = board.get_valid_moves(3, 4)
        assert (2, 3) not in moves

    def test_widget_en_passant_click_interaction(self, qapp):
        widget = ChessBoardWidget()
        # 1. White plays e2-e4
        widget.handle_square_clicked(6, 4)
        widget.handle_square_clicked(4, 4)
        # 2. Black plays a7-a6
        widget.handle_square_clicked(1, 0)
        widget.handle_square_clicked(2, 0)
        # 3. White plays e4-e5
        widget.handle_square_clicked(4, 4)
        widget.handle_square_clicked(3, 4)
        # 4. Black plays d7-d5 (2 squares next to White e5 pawn)
        widget.handle_square_clicked(1, 3)
        widget.handle_square_clicked(3, 3)

        # 5. White selects e5 pawn
        widget.handle_square_clicked(3, 4)
        assert (2, 3) in widget.valid_moves  # En passant target d6

        # 6. White clicks d6 to execute en passant
        widget.handle_square_clicked(2, 3)

        # Black d5 pawn must be captured
        assert widget.pieces.get_piece(3, 3) is None
        # White pawn must be on d6 (row 2, col 3)
        pawn = widget.pieces.get_piece(2, 3)
        assert pawn is not None
        assert pawn.color == PieceColor.WHITE
        assert pawn.piece_type == PieceType.PAWN


class TestCastlingMovement:
    def test_white_kingside_and_queenside_castling(self):
        board = create_empty_board()
        board.set_piece(7, 4, Piece(PieceColor.WHITE, PieceType.KING))
        board.set_piece(7, 7, Piece(PieceColor.WHITE, PieceType.ROOK)) # Kingside rook
        board.set_piece(7, 0, Piece(PieceColor.WHITE, PieceType.ROOK)) # Queenside rook

        moves = set(board.get_valid_moves(7, 4))
        # Both castling moves should be available: (7, 6) and (7, 2)
        assert (7, 6) in moves
        assert (7, 2) in moves

        # Execute kingside castle
        board.move_piece(7, 4, 7, 6)
        # King is at (7, 6)
        assert board.get_piece(7, 6).piece_type == PieceType.KING
        assert board.get_piece(7, 4) is None
        # Rook is at (7, 5)
        assert board.get_piece(7, 5).piece_type == PieceType.ROOK
        assert board.get_piece(7, 7) is None

    def test_white_queenside_castling_execution(self):
        board = create_empty_board()
        board.set_piece(7, 4, Piece(PieceColor.WHITE, PieceType.KING))
        board.set_piece(7, 0, Piece(PieceColor.WHITE, PieceType.ROOK))

        moves = set(board.get_valid_moves(7, 4))
        assert (7, 2) in moves

        board.move_piece(7, 4, 7, 2)
        # King at (7, 2)
        assert board.get_piece(7, 2).piece_type == PieceType.KING
        assert board.get_piece(7, 4) is None
        # Rook at (7, 3)
        assert board.get_piece(7, 3).piece_type == PieceType.ROOK
        assert board.get_piece(7, 0) is None

    def test_black_castling(self):
        board = create_empty_board()
        board.set_piece(0, 4, Piece(PieceColor.BLACK, PieceType.KING))
        board.set_piece(0, 7, Piece(PieceColor.BLACK, PieceType.ROOK))
        board.set_piece(0, 0, Piece(PieceColor.BLACK, PieceType.ROOK))

        moves = set(board.get_valid_moves(0, 4))
        assert (0, 6) in moves
        assert (0, 2) in moves

        # Execute black kingside castle
        board.move_piece(0, 4, 0, 6)
        assert board.get_piece(0, 6).piece_type == PieceType.KING
        assert board.get_piece(0, 5).piece_type == PieceType.ROOK
        assert board.get_piece(0, 7) is None

    def test_castling_blocked_by_pieces(self):
        board = create_empty_board()
        board.set_piece(7, 4, Piece(PieceColor.WHITE, PieceType.KING))
        board.set_piece(7, 7, Piece(PieceColor.WHITE, PieceType.ROOK))
        # Place a bishop between King and Kingside Rook
        board.set_piece(7, 5, Piece(PieceColor.WHITE, PieceType.BISHOP))

        moves = board.get_valid_moves(7, 4)
        assert (7, 6) not in moves

    def test_castling_prevented_if_king_has_moved(self):
        board = create_empty_board()
        king = Piece(PieceColor.WHITE, PieceType.KING)
        board.set_piece(7, 4, king)
        board.set_piece(7, 7, Piece(PieceColor.WHITE, PieceType.ROOK))

        king.has_moved = True
        moves = board.get_valid_moves(7, 4)
        assert (7, 6) not in moves

    def test_castling_prevented_if_rook_has_moved(self):
        board = create_empty_board()
        board.set_piece(7, 4, Piece(PieceColor.WHITE, PieceType.KING))
        rook = Piece(PieceColor.WHITE, PieceType.ROOK)
        board.set_piece(7, 7, rook)

        rook.has_moved = True
        moves = board.get_valid_moves(7, 4)
        assert (7, 6) not in moves

    def test_widget_castling_interaction(self, qapp):
        widget = ChessBoardWidget()
        # Clear out pieces between e1 king and h1 rook (f1 bishop, g1 knight)
        widget.pieces.set_piece(7, 5, None)
        widget.pieces.set_piece(7, 6, None)

        # Select King at e1 (7, 4)
        widget.handle_square_clicked(7, 4)
        assert (7, 6) in widget.valid_moves

        # Click g1 (7, 6) to castle kingside
        widget.handle_square_clicked(7, 6)

        # King should now be at g1 (7, 6) and Rook at f1 (7, 5)
        assert widget.pieces.get_piece(7, 6).piece_type == PieceType.KING
        assert widget.pieces.get_piece(7, 5).piece_type == PieceType.ROOK
        assert widget.pieces.get_piece(7, 7) is None


class TestMoveCategories:
    def test_move_category_classification(self):
        board = create_empty_board()
        board.set_piece(7, 4, Piece(PieceColor.WHITE, PieceType.KING))
        board.set_piece(7, 7, Piece(PieceColor.WHITE, PieceType.ROOK))
        board.set_piece(3, 4, Piece(PieceColor.WHITE, PieceType.PAWN))
        # Place opponent pawn that was double-stepped
        board.set_piece(3, 3, Piece(PieceColor.BLACK, PieceType.PAWN))
        board.en_passant_target = (2, 3)

        assert board.get_move_category(7, 4, 7, 6) == "castling"
        assert board.get_move_category(7, 4, 6, 4) == "normal"
        assert board.get_move_category(3, 4, 2, 3) == "en_passant"
        assert board.get_move_category(3, 4, 2, 4) == "normal"

    def test_same_color_pawn_cannot_en_passant(self):
        board = BoardPieces()
        # White moves e2 to e4 (6, 4 -> 4, 4)
        board.move_piece(6, 4, 4, 4)
        assert board.en_passant_target == (5, 4)

        # White d2 pawn (6, 3) must NOT have (5, 4) in valid moves
        white_d2_moves = board.get_valid_moves(6, 3)
        assert (5, 4) not in white_d2_moves
        assert board.get_move_category(6, 3, 5, 4) == "normal"

    def test_turn_enforcement_in_widget(self, qapp):
        widget = ChessBoardWidget()
        assert widget.current_turn == PieceColor.WHITE

        # Try to select black pawn at (1, 3) on White's turn -> should not select
        widget.handle_square_clicked(1, 3)
        assert widget.selected_square is None
        assert widget.valid_moves == []

        # Select and move white pawn at (6, 4) -> (4, 4)
        widget.handle_square_clicked(6, 4)
        assert widget.selected_square == (6, 4)
        widget.handle_square_clicked(4, 4)
        assert widget.selected_square is None
        # Now it is Black's turn
        assert widget.current_turn == PieceColor.BLACK

        # White piece cannot move on Black's turn
        widget.handle_square_clicked(6, 3)
        assert widget.selected_square is None

        # Black can move on Black's turn
        widget.handle_square_clicked(1, 3)
        assert widget.selected_square == (1, 3)
        widget.handle_square_clicked(3, 3)
        assert widget.selected_square is None
        # Back to White's turn
        assert widget.current_turn == PieceColor.WHITE

