"""Unit and integration tests for check, checkmate, turn impedance, and free move handling."""

import os
import sys
from pathlib import Path
from unittest.mock import patch
import pytest

# Ensure src is in sys.path
SRC_DIR = Path(__file__).parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Headless Qt
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt6.QtWidgets import QApplication, QMessageBox
from pieces import BoardPieces, Piece, PieceColor, PieceType
from check_mate import (
    find_king,
    is_in_check,
    is_move_legal,
    get_legal_moves,
    has_any_legal_moves,
    is_checkmate,
    move_leads_to_mate,
)
from board import ChessBoardWidget


def create_empty_board() -> BoardPieces:
    """Helper to create a board with no pieces."""
    board = BoardPieces()
    board.grid = [[None for _ in range(8)] for _ in range(8)]
    return board


class TestKingFindingAndCheck:
    def test_find_king_initial_position(self):
        board = BoardPieces()
        assert find_king(board, PieceColor.WHITE) == (7, 4)
        assert find_king(board, PieceColor.BLACK) == (0, 4)

    def test_find_king_none_when_absent(self):
        board = create_empty_board()
        assert find_king(board, PieceColor.WHITE) is None
        assert find_king(board, PieceColor.BLACK) is None

    def test_not_in_check_initial_position(self):
        board = BoardPieces()
        assert not is_in_check(board, PieceColor.WHITE)
        assert not is_in_check(board, PieceColor.BLACK)

    def test_in_check_by_rook(self):
        board = create_empty_board()
        board.set_piece(7, 4, Piece(PieceColor.WHITE, PieceType.KING))
        board.set_piece(0, 4, Piece(PieceColor.BLACK, PieceType.ROOK))
        assert is_in_check(board, PieceColor.WHITE)
        assert not is_in_check(board, PieceColor.BLACK)

    def test_in_check_by_bishop(self):
        board = create_empty_board()
        board.set_piece(7, 4, Piece(PieceColor.WHITE, PieceType.KING))
        board.set_piece(4, 1, Piece(PieceColor.BLACK, PieceType.BISHOP))
        assert is_in_check(board, PieceColor.WHITE)

    def test_in_check_by_knight(self):
        board = create_empty_board()
        board.set_piece(7, 4, Piece(PieceColor.WHITE, PieceType.KING))
        board.set_piece(5, 3, Piece(PieceColor.BLACK, PieceType.KNIGHT))
        assert is_in_check(board, PieceColor.WHITE)

    def test_in_check_by_pawn(self):
        board = create_empty_board()
        board.set_piece(4, 4, Piece(PieceColor.WHITE, PieceType.KING))
        # Black pawn at (3, 3) attacks down-right to (4, 4)
        board.set_piece(3, 3, Piece(PieceColor.BLACK, PieceType.PAWN))
        assert is_in_check(board, PieceColor.WHITE)


class TestMoveLegalityAndImpedance:
    def test_pinned_piece_cannot_move_off_pin_line(self):
        board = create_empty_board()
        board.set_piece(7, 4, Piece(PieceColor.WHITE, PieceType.KING))
        # White rook at (5, 4) shielding king from Black rook at (0, 4)
        board.set_piece(5, 4, Piece(PieceColor.WHITE, PieceType.ROOK))
        board.set_piece(0, 4, Piece(PieceColor.BLACK, PieceType.ROOK))

        assert not is_in_check(board, PieceColor.WHITE)

        # White rook can only move along the pin ray (col 4)
        legal_moves = get_legal_moves(board, 5, 4)
        for r, c in legal_moves:
            assert c == 4  # Cannot move horizontally off the file!
        assert (5, 3) not in legal_moves
        assert (5, 5) not in legal_moves
        assert (0, 4) in legal_moves  # Can capture pinning rook
        assert (6, 4) in legal_moves  # Can move back toward king

    def test_pinned_knight_has_no_moves(self):
        board = create_empty_board()
        board.set_piece(7, 4, Piece(PieceColor.WHITE, PieceType.KING))
        board.set_piece(6, 4, Piece(PieceColor.WHITE, PieceType.KNIGHT))
        board.set_piece(0, 4, Piece(PieceColor.BLACK, PieceType.ROOK))

        # Knight cannot jump away without exposing king
        legal_moves = get_legal_moves(board, 6, 4)
        assert len(legal_moves) == 0

    def test_king_cannot_move_into_check(self):
        board = create_empty_board()
        board.set_piece(7, 4, Piece(PieceColor.WHITE, PieceType.KING))
        # Black rook controls file 3
        board.set_piece(0, 3, Piece(PieceColor.BLACK, PieceType.ROOK))

        legal_moves = get_legal_moves(board, 7, 4)
        # King cannot move to (6, 3) or (7, 3) because col 3 is attacked
        assert (6, 3) not in legal_moves
        assert (7, 3) not in legal_moves
        # Can move to col 4 and 5
        assert (6, 4) in legal_moves
        assert (6, 5) in legal_moves
        assert (7, 5) in legal_moves

    def test_king_cannot_move_adjacent_to_enemy_king(self):
        board = create_empty_board()
        board.set_piece(4, 4, Piece(PieceColor.WHITE, PieceType.KING))
        board.set_piece(2, 4, Piece(PieceColor.BLACK, PieceType.KING))

        legal_moves = get_legal_moves(board, 4, 4)
        # Row 3 is between the kings; squares (3, 3), (3, 4), (3, 5) are attacked by Black king
        assert (3, 3) not in legal_moves
        assert (3, 4) not in legal_moves
        assert (3, 5) not in legal_moves

    def test_piece_can_block_check(self):
        board = create_empty_board()
        board.set_piece(7, 4, Piece(PieceColor.WHITE, PieceType.KING))
        # Black rook delivers check from (7, 0)
        board.set_piece(7, 0, Piece(PieceColor.BLACK, PieceType.ROOK))
        # White bishop at (5, 2)
        board.set_piece(5, 2, Piece(PieceColor.WHITE, PieceType.BISHOP))

        assert is_in_check(board, PieceColor.WHITE)
        bishop_moves = get_legal_moves(board, 5, 2)
        # Bishop can only move to (7, 4) which is friendly king (no) or interpose at (7, 0..3)
        # From (5, 2), bishop diagonals: (6, 1), (7, 0) capture, (6, 3), (7, 4)
        # Bishop can capture checking rook at (7, 0)!
        assert (7, 0) in bishop_moves
        # Bishop cannot move to (4, 1) because it does not resolve check!
        assert (4, 1) not in bishop_moves

    def test_piece_can_capture_checking_piece(self):
        board = create_empty_board()
        board.set_piece(7, 4, Piece(PieceColor.WHITE, PieceType.KING))
        # Black knight checking at (5, 3)
        board.set_piece(5, 3, Piece(PieceColor.BLACK, PieceType.KNIGHT))
        # White pawn at (6, 2) can capture knight at (5, 3)
        board.set_piece(6, 2, Piece(PieceColor.WHITE, PieceType.PAWN))

        assert is_in_check(board, PieceColor.WHITE)
        pawn_moves = get_legal_moves(board, 6, 2)
        assert pawn_moves == [(5, 3)]  # Capturing the checking knight is the ONLY legal move for this pawn


class TestCheckmateDetection:
    def test_fools_mate(self):
        # 1. f3 e5 2. g4 Qh4#
        board = BoardPieces()
        board.move_piece(6, 5, 5, 5)  # f2 -> f3
        board.move_piece(1, 4, 3, 4)  # e7 -> e5
        board.move_piece(6, 6, 4, 6)  # g2 -> g4
        board.move_piece(0, 3, 4, 7)  # d8 -> h4 (Qh4)

        assert is_in_check(board, PieceColor.WHITE)
        assert not has_any_legal_moves(board, PieceColor.WHITE)
        assert is_checkmate(board, PieceColor.WHITE)
        assert not is_checkmate(board, PieceColor.BLACK)

    def test_scholars_mate(self):
        # 1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7#
        board = BoardPieces()
        board.move_piece(6, 4, 4, 4)  # e2 -> e4
        board.move_piece(1, 4, 3, 4)  # e7 -> e5
        board.move_piece(7, 3, 3, 7)  # d1 -> h5 (Qh5)
        board.move_piece(0, 1, 2, 2)  # b8 -> c6 (Nc6)
        board.move_piece(7, 5, 4, 2)  # f1 -> c4 (Bc4)
        board.move_piece(0, 6, 2, 5)  # g8 -> f6 (Nf6)
        board.move_piece(3, 7, 1, 5)  # Qh5 x f7#

        assert is_in_check(board, PieceColor.BLACK)
        assert not has_any_legal_moves(board, PieceColor.BLACK)
        assert is_checkmate(board, PieceColor.BLACK)
        assert not is_checkmate(board, PieceColor.WHITE)

    def test_back_rank_mate(self):
        board = create_empty_board()
        board.set_piece(0, 4, Piece(PieceColor.BLACK, PieceType.KING))
        # Black pawns trapping king on back rank
        board.set_piece(1, 3, Piece(PieceColor.BLACK, PieceType.PAWN))
        board.set_piece(1, 4, Piece(PieceColor.BLACK, PieceType.PAWN))
        board.set_piece(1, 5, Piece(PieceColor.BLACK, PieceType.PAWN))
        # White rook delivering check on back rank
        board.set_piece(0, 0, Piece(PieceColor.WHITE, PieceType.ROOK))

        assert is_in_check(board, PieceColor.BLACK)
        assert is_checkmate(board, PieceColor.BLACK)

    def test_check_not_mate_when_king_can_step_away(self):
        board = create_empty_board()
        board.set_piece(0, 4, Piece(PieceColor.BLACK, PieceType.KING))
        board.set_piece(0, 0, Piece(PieceColor.WHITE, PieceType.ROOK))

        assert is_in_check(board, PieceColor.BLACK)
        # King can step down to row 1
        assert has_any_legal_moves(board, PieceColor.BLACK)
        assert not is_checkmate(board, PieceColor.BLACK)


class TestWidgetTurnBasedCheckAndMate:
    def test_turn_based_checkmate_triggers_popup_and_ends_game(self, qapp):
        widget = ChessBoardWidget()

        # Play Fool's mate:
        # 1. White f2-f3 (6, 5 -> 5, 5)
        widget.handle_square_clicked(6, 5)
        widget.handle_square_clicked(5, 5)

        # 2. Black e7-e5 (1, 4 -> 3, 4)
        widget.handle_square_clicked(1, 4)
        widget.handle_square_clicked(3, 4)

        # 3. White g2-g4 (6, 6 -> 4, 6)
        widget.handle_square_clicked(6, 6)
        widget.handle_square_clicked(4, 6)

        # 4. Black Qh4# (0, 3 -> 4, 7)
        with patch.object(QMessageBox, "information") as mock_info:
            widget.handle_square_clicked(0, 3)
            widget.handle_square_clicked(4, 7)

            assert widget.game_over is True
            mock_info.assert_called_once()
            # Dialog title and text
            args, _ = mock_info.call_args
            assert "BLACK WON" in args[2]

        # Further clicks should be ignored because game_over is True
        widget.handle_square_clicked(6, 0)
        assert widget.selected_square is None

    def test_turn_based_impedes_illegal_moves_leaving_king_in_check(self, qapp):
        widget = ChessBoardWidget()
        # White plays e4 (6, 4 -> 4, 4)
        widget.handle_square_clicked(6, 4)
        widget.handle_square_clicked(4, 4)
        # Black plays e5 (1, 4 -> 3, 4)
        widget.handle_square_clicked(1, 4)
        widget.handle_square_clicked(3, 4)
        # White plays Qh5 (7, 3 -> 3, 7)
        widget.handle_square_clicked(7, 3)
        widget.handle_square_clicked(3, 7)

        # Black king at (0, 4). Black f7 pawn at (1, 5) is attacked by Qh5 diagonally
        # White now plays Qxf7+ check
        widget.pieces.set_piece(1, 5, Piece(PieceColor.WHITE, PieceType.QUEEN))
        widget.pieces.set_piece(3, 7, None)
        # Black is in check
        assert is_in_check(widget.pieces, PieceColor.BLACK)

        # Black selects d7 pawn (1, 3)
        widget.handle_square_clicked(1, 3)
        # d7 pawn cannot move because moving it does NOT get king out of check!
        assert widget.valid_moves == []

        # Black selects e8 king (0, 4)
        widget.handle_square_clicked(0, 4)
        # King can capture queen at (1, 5) or move to (1, 4)
        assert (1, 5) in widget.valid_moves


class TestWidgetFreeMoveEndGameHandling:
    def test_free_move_popup_reject_cancels_move(self, qapp):
        widget = ChessBoardWidget(free_move=True)
        # Set up a position where White Queen can deliver mate to Black king
        widget.pieces = create_empty_board()
        widget.pieces.set_piece(0, 4, Piece(PieceColor.BLACK, PieceType.KING))
        widget.pieces.set_piece(1, 3, Piece(PieceColor.BLACK, PieceType.PAWN))
        widget.pieces.set_piece(1, 4, Piece(PieceColor.BLACK, PieceType.PAWN))
        widget.pieces.set_piece(1, 5, Piece(PieceColor.BLACK, PieceType.PAWN))
        widget.pieces.set_piece(2, 0, Piece(PieceColor.WHITE, PieceType.ROOK))

        # Select White Rook at (2, 0)
        widget.handle_square_clicked(2, 0)
        assert (0, 0) in widget.valid_moves

        # Moving to (0, 0) delivers back-rank mate!
        # Mock QMessageBox.question returning 'No' (do NOT allow move)
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No) as mock_q, \
             patch.object(QMessageBox, "information") as mock_info:
            widget.handle_square_clicked(0, 0)

            mock_q.assert_called_once()
            # Move was NOT made!
            assert widget.pieces.get_piece(0, 0) is None
            assert widget.pieces.get_piece(2, 0) is not None
            assert widget.game_over is False
            mock_info.assert_not_called()

    def test_free_move_popup_allow_executes_move_and_ends_game(self, qapp):
        widget = ChessBoardWidget(free_move=True)
        widget.pieces = create_empty_board()
        widget.pieces.set_piece(0, 4, Piece(PieceColor.BLACK, PieceType.KING))
        widget.pieces.set_piece(1, 3, Piece(PieceColor.BLACK, PieceType.PAWN))
        widget.pieces.set_piece(1, 4, Piece(PieceColor.BLACK, PieceType.PAWN))
        widget.pieces.set_piece(1, 5, Piece(PieceColor.BLACK, PieceType.PAWN))
        widget.pieces.set_piece(2, 0, Piece(PieceColor.WHITE, PieceType.ROOK))

        widget.handle_square_clicked(2, 0)
        assert (0, 0) in widget.valid_moves

        # Mock QMessageBox.question returning 'Yes' (allow move)
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes) as mock_q, \
             patch.object(QMessageBox, "information") as mock_info:
            widget.handle_square_clicked(0, 0)

            mock_q.assert_called_once()
            # Move was made!
            assert widget.pieces.get_piece(0, 0) is not None
            assert widget.pieces.get_piece(2, 0) is None
            assert widget.game_over is True
            mock_info.assert_called_once()
            args, _ = mock_info.call_args
            assert "WHITE WON" in args[2]


class TestPaintEventAndVisuals:
    def test_paint_event_with_king_in_check(self, qapp):
        widget = ChessBoardWidget()
        widget.resize(600, 600)
        # Clear blocking pawn on file 4
        widget.pieces.set_piece(1, 4, None)
        # Put white rook on e-file attacking black king at (0, 4)
        widget.pieces.set_piece(2, 4, Piece(PieceColor.WHITE, PieceType.ROOK))

        assert is_in_check(widget.pieces, PieceColor.BLACK)

        # Trigger paint event; ensures no rendering errors or exceptions occur
        widget.repaint()


class TestFreeMoveSelfMate:
    def test_free_move_moving_king_into_check_prompts_end_game(self, qapp):
        widget = ChessBoardWidget(free_move=True)
        widget.pieces = create_empty_board()
        # White king at (7, 4)
        widget.pieces.set_piece(7, 4, Piece(PieceColor.WHITE, PieceType.KING))
        # Black rook controlling file 3
        widget.pieces.set_piece(0, 3, Piece(PieceColor.BLACK, PieceType.ROOK))

        # White selects king
        widget.handle_square_clicked(7, 4)
        # (7, 3) is a valid piece move, but moves into check
        assert (7, 3) in widget.valid_moves

        # Moving king to (7, 3) leads to mate/loss for White
        with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes) as mock_q, \
             patch.object(QMessageBox, "information") as mock_info:
            widget.handle_square_clicked(7, 3)

            mock_q.assert_called_once()
            assert widget.game_over is True
            mock_info.assert_called_once()
            args, _ = mock_info.call_args
            assert "BLACK WON" in args[2]
