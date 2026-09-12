"""Unit and integration tests for pawn promotion and floating selection window."""

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
from check_mate import is_in_check, is_checkmate, move_leads_to_mate
from board import ChessBoardWidget
from promotion import PromotionDialog, prompt_promotion


def create_empty_board() -> BoardPieces:
    """Helper to create a board with no pieces."""
    board = BoardPieces()
    board.grid = [[None for _ in range(8)] for _ in range(8)]
    return board


class TestPromotionDialog:
    def test_promotion_dialog_default_is_queen(self, qapp):
        dialog = PromotionDialog(PieceColor.WHITE)
        assert dialog.selected_piece_type == PieceType.QUEEN
        dialog.close()

    def test_promotion_dialog_select_pieces(self, qapp):
        for p_type in (PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT):
            dialog = PromotionDialog(PieceColor.BLACK)
            dialog._on_piece_selected(p_type)
            assert dialog.selected_piece_type == p_type
            dialog.close()

    def test_prompt_promotion_helper(self, qapp):
        with patch.object(PromotionDialog, "exec") as mock_exec:
            piece_type = prompt_promotion(PieceColor.WHITE)
            mock_exec.assert_called_once()
            assert piece_type == PieceType.QUEEN


class TestBoardPiecesPromotePawn:
    def test_promote_pawn_to_queen(self):
        board = create_empty_board()
        board.set_piece(0, 4, Piece(PieceColor.WHITE, PieceType.PAWN))
        promoted = board.promote_pawn(0, 4, PieceType.QUEEN)

        assert promoted.piece_type == PieceType.QUEEN
        assert promoted.color == PieceColor.WHITE
        assert board.get_piece(0, 4).piece_type == PieceType.QUEEN

    def test_promote_pawn_to_knight(self):
        board = create_empty_board()
        board.set_piece(7, 3, Piece(PieceColor.BLACK, PieceType.PAWN))
        promoted = board.promote_pawn(7, 3, PieceType.KNIGHT)

        assert promoted.piece_type == PieceType.KNIGHT
        assert promoted.color == PieceColor.BLACK
        assert board.get_piece(7, 3).piece_type == PieceType.KNIGHT


class TestPromotionMateCheckingSpecificPiece:
    def test_promotion_leads_to_mate_specifically_for_promoted_piece(self):
        board = create_empty_board()
        # Black king trapped at (0, 0) by White pawns
        board.set_piece(0, 0, Piece(PieceColor.BLACK, PieceType.KING))
        board.set_piece(1, 1, Piece(PieceColor.WHITE, PieceType.PAWN))
        board.set_piece(2, 0, Piece(PieceColor.WHITE, PieceType.KING))

        # White pawn at (1, 7) can move to (0, 7)
        board.set_piece(1, 7, Piece(PieceColor.WHITE, PieceType.PAWN))

        # 1. Promoting to QUEEN at (0, 7) controls row 0, delivering checkmate to king at (0, 0)
        leads_mate_queen, winner_queen = move_leads_to_mate(
            board, 1, 7, 0, 7, promotion=PieceType.QUEEN
        )
        assert leads_mate_queen is True
        assert winner_queen == PieceColor.WHITE

        # 2. Promoting to ROOK at (0, 7) also controls row 0, delivering checkmate
        leads_mate_rook, winner_rook = move_leads_to_mate(
            board, 1, 7, 0, 7, promotion=PieceType.ROOK
        )
        assert leads_mate_rook is True
        assert winner_rook == PieceColor.WHITE

        # 3. Promoting to BISHOP at (0, 7) does NOT control row 0 (light-square diagonal) -> NOT checkmate!
        leads_mate_bishop, winner_bishop = move_leads_to_mate(
            board, 1, 7, 0, 7, promotion=PieceType.BISHOP
        )
        assert leads_mate_bishop is False
        assert winner_bishop is None

        # 4. Promoting to KNIGHT at (0, 7) cannot reach (0, 0) -> NOT checkmate!
        leads_mate_knight, winner_knight = move_leads_to_mate(
            board, 1, 7, 0, 7, promotion=PieceType.KNIGHT
        )
        assert leads_mate_knight is False
        assert winner_knight is None


class TestWidgetTurnBasedPromotion:
    def test_white_pawn_promotes_to_queen(self, qapp):
        widget = ChessBoardWidget()
        widget.pieces = create_empty_board()
        widget.pieces.set_piece(7, 4, Piece(PieceColor.WHITE, PieceType.KING))
        widget.pieces.set_piece(0, 4, Piece(PieceColor.BLACK, PieceType.KING))
        # White pawn at (1, 0) advancing to (0, 0)
        widget.pieces.set_piece(1, 0, Piece(PieceColor.WHITE, PieceType.PAWN))

        # Select White pawn at (1, 0)
        widget.handle_square_clicked(1, 0)
        assert (0, 0) in widget.valid_moves

        # Move to (0, 0) with mocked promotion dialog returning QUEEN
        with patch("board.prompt_promotion", return_value=PieceType.QUEEN) as mock_prompt:
            widget.handle_square_clicked(0, 0)
            mock_prompt.assert_called_once_with(PieceColor.WHITE, widget)

        piece_at_target = widget.pieces.get_piece(0, 0)
        assert piece_at_target is not None
        assert piece_at_target.color == PieceColor.WHITE
        assert piece_at_target.piece_type == PieceType.QUEEN

    def test_black_pawn_promotes_to_knight(self, qapp):
        widget = ChessBoardWidget()
        widget.pieces = create_empty_board()
        widget.pieces.set_piece(7, 4, Piece(PieceColor.WHITE, PieceType.KING))
        widget.pieces.set_piece(0, 4, Piece(PieceColor.BLACK, PieceType.KING))
        # Black pawn at (6, 0) advancing to (7, 0)
        widget.pieces.set_piece(6, 0, Piece(PieceColor.BLACK, PieceType.PAWN))
        widget.current_turn = PieceColor.BLACK

        # Select Black pawn at (6, 0)
        widget.handle_square_clicked(6, 0)
        assert (7, 0) in widget.valid_moves

        with patch("board.prompt_promotion", return_value=PieceType.KNIGHT) as mock_prompt:
            widget.handle_square_clicked(7, 0)
            mock_prompt.assert_called_once_with(PieceColor.BLACK, widget)

        piece_at_target = widget.pieces.get_piece(7, 0)
        assert piece_at_target is not None
        assert piece_at_target.color == PieceColor.BLACK
        assert piece_at_target.piece_type == PieceType.KNIGHT

    def test_promotion_delivering_checkmate_ends_game(self, qapp):
        widget = ChessBoardWidget()
        widget.pieces = create_empty_board()
        # Black king trapped at (0, 0)
        widget.pieces.set_piece(0, 0, Piece(PieceColor.BLACK, PieceType.KING))
        widget.pieces.set_piece(1, 1, Piece(PieceColor.WHITE, PieceType.PAWN))
        widget.pieces.set_piece(2, 0, Piece(PieceColor.WHITE, PieceType.KING))

        # White pawn at (1, 7)
        widget.pieces.set_piece(1, 7, Piece(PieceColor.WHITE, PieceType.PAWN))

        widget.handle_square_clicked(1, 7)
        assert (0, 7) in widget.valid_moves

        with patch("board.prompt_promotion", return_value=PieceType.QUEEN), \
             patch.object(QMessageBox, "information") as mock_info:
            widget.handle_square_clicked(0, 7)

            assert widget.game_over is True
            mock_info.assert_called_once()
            args, _ = mock_info.call_args
            assert "WHITE WON" in args[2]


class TestWidgetFreeMovePromotion:
    def test_free_move_promotion_mate_cancelled_by_user(self, qapp):
        widget = ChessBoardWidget(free_move=True)
        widget.pieces = create_empty_board()
        widget.pieces.set_piece(0, 0, Piece(PieceColor.BLACK, PieceType.KING))
        widget.pieces.set_piece(1, 1, Piece(PieceColor.WHITE, PieceType.PAWN))
        widget.pieces.set_piece(2, 0, Piece(PieceColor.WHITE, PieceType.KING))
        widget.pieces.set_piece(1, 7, Piece(PieceColor.WHITE, PieceType.PAWN))

        widget.handle_square_clicked(1, 7)
        assert (0, 7) in widget.valid_moves

        # Promotes to Queen (which delivers mate) but user answers 'No' to "End game?"
        with patch("board.prompt_promotion", return_value=PieceType.QUEEN), \
             patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.No) as mock_q, \
             patch.object(QMessageBox, "information") as mock_info:
            widget.handle_square_clicked(0, 7)

            mock_q.assert_called_once()
            # Move was cancelled
            assert widget.pieces.get_piece(1, 7).piece_type == PieceType.PAWN
            assert widget.pieces.get_piece(0, 7) is None
            assert widget.game_over is False
            mock_info.assert_not_called()

    def test_free_move_promotion_mate_allowed_by_user(self, qapp):
        widget = ChessBoardWidget(free_move=True)
        widget.pieces = create_empty_board()
        widget.pieces.set_piece(0, 0, Piece(PieceColor.BLACK, PieceType.KING))
        widget.pieces.set_piece(1, 1, Piece(PieceColor.WHITE, PieceType.PAWN))
        widget.pieces.set_piece(2, 0, Piece(PieceColor.WHITE, PieceType.KING))
        widget.pieces.set_piece(1, 7, Piece(PieceColor.WHITE, PieceType.PAWN))

        widget.handle_square_clicked(1, 7)
        assert (0, 7) in widget.valid_moves

        # Promotes to Queen and user allows the move
        with patch("board.prompt_promotion", return_value=PieceType.QUEEN), \
             patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes) as mock_q, \
             patch.object(QMessageBox, "information") as mock_info:
            widget.handle_square_clicked(0, 7)

            mock_q.assert_called_once()
            # Move was made and promoted
            assert widget.pieces.get_piece(0, 7).piece_type == PieceType.QUEEN
            assert widget.pieces.get_piece(1, 7) is None
            assert widget.game_over is True
            mock_info.assert_called_once()
            args, _ = mock_info.call_args
            assert "WHITE WON" in args[2]

    def test_free_move_underpromotion_not_mating_proceeds_without_end_game_prompt(self, qapp):
        widget = ChessBoardWidget(free_move=True)
        widget.pieces = create_empty_board()
        widget.pieces.set_piece(0, 0, Piece(PieceColor.BLACK, PieceType.KING))
        widget.pieces.set_piece(1, 1, Piece(PieceColor.WHITE, PieceType.PAWN))
        widget.pieces.set_piece(2, 0, Piece(PieceColor.WHITE, PieceType.KING))
        widget.pieces.set_piece(1, 7, Piece(PieceColor.WHITE, PieceType.PAWN))

        widget.handle_square_clicked(1, 7)

        # Underpromoting to Bishop does NOT lead to mate
        with patch("board.prompt_promotion", return_value=PieceType.BISHOP), \
             patch.object(QMessageBox, "question") as mock_q:
            widget.handle_square_clicked(0, 7)

            # Did NOT ask "End game?" because underpromotion to bishop did NOT deliver mate!
            mock_q.assert_not_called()
            assert widget.pieces.get_piece(0, 7).piece_type == PieceType.BISHOP
            assert widget.game_over is False
