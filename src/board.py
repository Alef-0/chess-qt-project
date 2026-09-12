"""Chess board implementation using PyQt6."""

import math
import signal
import sys
from typing import List, Optional, Tuple
from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPen, QPolygonF, QResizeEvent
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from pieces import BoardPieces, PieceColor, PieceType
from check_mate import find_king, is_in_check, is_checkmate, get_legal_moves, move_leads_to_mate
from promotion import prompt_promotion
from menu import MainMenuWidget, TutorialDialog, CreditsDialog


class ChessBoardWidget(QWidget):
    """Widget responsible for rendering a resizable 8x8 chessboard while maintaining aspect ratio."""

    game_over_signal = pyqtSignal(str)
    turn_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None, free_move: bool = False) -> None:
        super().__init__(parent)
        # Colors configured within [50, 225] range to avoid display strain
        self.dark_square_color = QColor(50, 50, 50)       # Minimum brightness bound
        self.light_square_color = QColor(225, 225, 225)   # Maximum brightness bound
        self.border_color = QColor(115, 70, 40)           # Natural brown border
        self.background_color = QColor(30, 30, 30)        # Letterbox background

        # Pieces placement and state
        self.pieces = BoardPieces()

        # Selection and movement state
        self.selected_square: Optional[Tuple[int, int]] = None
        self.valid_moves: List[Tuple[int, int]] = []

        # Turn management: turn is enabled by default, --free-move disables it
        self.current_turn: PieceColor = PieceColor.WHITE
        self.turn_enabled: bool = not free_move
        self.game_over: bool = False

    def reset_game(self, free_move: Optional[bool] = None) -> None:
        """Resets board pieces, active selections, and turn state for a new game."""
        self.pieces = BoardPieces()
        _, _, square_size = self.get_board_geometry()
        if square_size > 0:
            self.pieces.update_size(max(1, round(square_size)))
        self.selected_square = None
        self.valid_moves = []
        self.current_turn = PieceColor.WHITE
        if free_move is not None:
            self.turn_enabled = not free_move
        self.game_over = False
        self.turn_changed.emit(self.current_turn.name)
        self.update()

    def get_board_geometry(self) -> Tuple[float, float, float]:
        """Calculates inner board top-left (inner_x, inner_y) and square_size for current dimensions."""
        width = self.width()
        height = self.height()
        board_total_size = min(width, height)
        if board_total_size <= 0:
            return 0.0, 0.0, 0.0
        offset_x = (width - board_total_size) / 2.0
        offset_y = (height - board_total_size) / 2.0
        border_thickness = max(4.0, board_total_size * 0.035)
        inner_board_size = board_total_size - (2.0 * border_thickness)
        if inner_board_size <= 0:
            return 0.0, 0.0, 0.0
        square_size = inner_board_size / 8.0
        inner_x = offset_x + border_thickness
        inner_y = offset_y + border_thickness
        return inner_x, inner_y, square_size

    def sizeHint(self) -> QSize:
        """Returns the recommended default starting size for this widget.

        Qt layouts and windows consult sizeHint() to determine how large the widget
        would ideally like to be before user interaction or window managers resize it.
        """
        return QSize(600, 600)

    def minimumSizeHint(self) -> QSize:
        """Returns the minimum recommended size for this widget.

        Qt layouts use this value to prevent the widget from being crushed or resized
        smaller than a readable/usable threshold where chessboard squares would become
        too small to interact with.
        """
        return QSize(240, 240)

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Recalculates piece sprite dimensions to match the updated board geometry on window resize."""
        super().resizeEvent(event)
        _, _, square_size = self.get_board_geometry()
        if square_size >= 10:
            self.pieces.update_size(max(1, round(square_size)))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handles mouse clicks to select pieces and execute moves."""
        if self.game_over:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            inner_x, inner_y, square_size = self.get_board_geometry()
            if square_size <= 0:
                return
            pos = event.position()
            x, y = pos.x(), pos.y()
            if inner_x <= x < inner_x + 8 * square_size and inner_y <= y < inner_y + 8 * square_size:
                col = int((x - inner_x) // square_size)
                row = int((y - inner_y) // square_size)
                self.handle_square_clicked(row, col)
            else:
                # Clicked outside the board boundary: deselect
                self.selected_square = None
                self.valid_moves = []
                self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            # Right click cancels active selection
            self.selected_square = None
            self.valid_moves = []
            self.update()

    def handle_square_clicked(self, row: int, col: int) -> None:
        """Processes a click on square (row, col) to select, move, or switch piece."""
        if self.game_over:
            return

        if self.selected_square is None:
            # Select piece if present and belongs to current turn
            piece = self.pieces.get_piece(row, col)
            if piece is not None:
                if self.turn_enabled and piece.color != self.current_turn:
                    return
                self.selected_square = (row, col)
                if self.turn_enabled:
                    self.valid_moves = get_legal_moves(self.pieces, row, col)
                else:
                    self.valid_moves = self.pieces.get_valid_moves(row, col)
                self.update()
        else:
            sel_row, sel_col = self.selected_square
            if (row, col) in self.valid_moves:
                moving_piece = self.pieces.get_piece(sel_row, sel_col)
                if moving_piece is None:
                    return

                # Check if this move is a pawn reaching the opposite side (promotion)
                is_promotion = (
                    moving_piece.piece_type == PieceType.PAWN
                    and ((moving_piece.color == PieceColor.WHITE and row == 0) or
                         (moving_piece.color == PieceColor.BLACK and row == 7))
                )
                promoted_type: Optional[PieceType] = None
                if is_promotion:
                    promoted_type = prompt_promotion(moving_piece.color, self)

                if not self.turn_enabled:
                    # Free move mode: check if this move leads to a mate (specifically for chosen promoted piece)
                    leads_to_mate, winner = move_leads_to_mate(
                        self.pieces, sel_row, sel_col, row, col, promotion=promoted_type
                    )
                    if leads_to_mate:
                        reply = QMessageBox.question(
                            self,
                            "End game?",
                            "End game?",
                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                            QMessageBox.StandardButton.No,
                        )
                        if reply != QMessageBox.StandardButton.Yes:
                            self.selected_square = None
                            self.valid_moves = []
                            self.update()
                            return
                        else:
                            self.pieces.move_piece(sel_row, sel_col, row, col)
                            if is_promotion and promoted_type is not None:
                                self.pieces.promote_pawn(row, col, promoted_type)
                            self.selected_square = None
                            self.valid_moves = []
                            self.game_over = True
                            self.update()
                            winner_name = winner.name if winner else "WHITE"
                            QMessageBox.information(self, "Game Over", f"{winner_name} WON")
                            self.game_over_signal.emit(winner_name)
                            return

                # Execute move to valid destination square
                self.pieces.move_piece(sel_row, sel_col, row, col)
                if is_promotion and promoted_type is not None:
                    self.pieces.promote_pawn(row, col, promoted_type)

                self.selected_square = None
                self.valid_moves = []

                # In turn-based mode, check if opposite king is in check or checkmate
                opp_color = (
                    PieceColor.BLACK if moving_piece.color == PieceColor.WHITE else PieceColor.WHITE
                )
                if is_in_check(self.pieces, opp_color):
                    if is_checkmate(self.pieces, opp_color):
                        self.game_over = True
                        self.update()
                        QMessageBox.information(self, "Game Over", f"{moving_piece.color.name} WON")
                        self.game_over_signal.emit(moving_piece.color.name)
                        return

                if self.turn_enabled:
                    self.current_turn = opp_color
                    self.turn_changed.emit(self.current_turn.name)
                self.update()
            else:
                clicked_piece = self.pieces.get_piece(row, col)
                if (
                    clicked_piece is not None
                    and (row, col) != self.selected_square
                    and (not self.turn_enabled or clicked_piece.color == self.current_turn)
                ):
                    # Switch selection to newly clicked piece of current turn
                    self.selected_square = (row, col)
                    if self.turn_enabled:
                        self.valid_moves = get_legal_moves(self.pieces, row, col)
                    else:
                        self.valid_moves = self.pieces.get_valid_moves(row, col)
                    self.update()
                else:
                    # Clicked invalid empty square, opponent piece, or same square -> deselect
                    self.selected_square = None
                    self.valid_moves = []
                    self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paints the 8x8 chessboard with border, centered and preserving aspect ratio."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        width = self.width()
        height = self.height()

        # Fill overall widget background (letterbox / pillarbox areas)
        painter.fillRect(0, 0, width, height, self.background_color)

        inner_x, inner_y, square_size = self.get_board_geometry()
        if square_size <= 0:
            return

        board_total_size = min(width, height)
        offset_x = (width - board_total_size) / 2.0
        offset_y = (height - board_total_size) / 2.0

        # Draw outer brown border
        border_rect = QRectF(offset_x, offset_y, board_total_size, board_total_size)
        painter.fillRect(border_rect, self.border_color)

        # Draw the 8x8 alternating squares
        for row in range(8):
            for col in range(8):
                # Standard chess pattern: (row + col) % 2 == 0 is light square
                is_light = (row + col) % 2 == 0
                color = self.light_square_color if is_light else self.dark_square_color

                # Calculate exact square boundaries
                sq_x = inner_x + col * square_size
                sq_y = inner_y + row * square_size

                square_rect = QRectF(sq_x, sq_y, square_size, square_size)
                painter.fillRect(square_rect, color)

        # Highlight kings in check on a red square
        for color in (PieceColor.WHITE, PieceColor.BLACK):
            if is_in_check(self.pieces, color):
                k_pos = find_king(self.pieces, color)
                if k_pos is not None:
                    k_row, k_col = k_pos
                    sq_x = inner_x + k_col * square_size
                    sq_y = inner_y + k_row * square_size
                    painter.fillRect(
                        QRectF(sq_x, sq_y, square_size, square_size),
                        QColor(225, 45, 45, 220),
                    )

        # Draw highlight on selected square
        if self.selected_square is not None:
            sel_row, sel_col = self.selected_square
            sq_x = inner_x + sel_col * square_size
            sq_y = inner_y + sel_row * square_size
            painter.fillRect(QRectF(sq_x, sq_y, square_size, square_size), QColor(215, 205, 100, 110))

        # Draw pieces on top of the squares
        self.pieces.draw(painter, inner_x, inner_y, square_size)

        # Draw light gray dots and special category arrows for valid move target squares
        if self.valid_moves and self.selected_square is not None:
            sel_row, sel_col = self.selected_square
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            for m_row, m_col in self.valid_moves:
                center_x = inner_x + (m_col + 0.5) * square_size
                center_y = inner_y + (m_row + 0.5) * square_size
                category = self.pieces.get_move_category(sel_row, sel_col, m_row, m_col)

                if category in ("en_passant", "castling"):
                    # Special category moves: signified by an arrow
                    self._draw_move_arrow(
                        painter, sel_row, sel_col, m_row, m_col, center_x, center_y, square_size
                    )
                else:
                    target_piece = self.pieces.get_piece(m_row, m_col)
                    if target_piece is None:
                        # Empty square: solid light gray dot
                        dot_radius = square_size * 0.16
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(QColor(170, 170, 170, 200))
                        painter.drawEllipse(QPointF(center_x, center_y), dot_radius, dot_radius)
                    else:
                        # Capture square: light gray dot with outline and ring for high visibility over pieces
                        ring_radius = square_size * 0.42
                        pen_width = max(2.0, square_size * 0.07)
                        painter.setBrush(Qt.BrushStyle.NoBrush)
                        painter.setPen(QPen(QColor(190, 190, 190, 210), pen_width))
                        painter.drawEllipse(QPointF(center_x, center_y), ring_radius, ring_radius)

                        dot_radius = square_size * 0.18
                        painter.setPen(QPen(QColor(40, 40, 40, 160), max(1.5, square_size * 0.025)))
                        painter.setBrush(QColor(210, 210, 210, 230))
                        painter.drawEllipse(QPointF(center_x, center_y), dot_radius, dot_radius)

    def _draw_move_arrow(
        self,
        painter: QPainter,
        from_row: int,
        from_col: int,
        to_row: int,
        to_col: int,
        center_x: float,
        center_y: float,
        square_size: float,
    ) -> None:
        """Renders an arrow indicator denoting special category moves (en passant, castling)."""
        dy = (to_row - from_row) * square_size
        dx = (to_col - from_col) * square_size
        angle_deg = math.degrees(math.atan2(dy, dx))

        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(angle_deg)

        # Arrow geometry pointing along +X (towards destination)
        length = square_size * 0.44
        head_width = square_size * 0.32
        head_length = square_size * 0.22
        shaft_width = square_size * 0.13

        half_len = length / 2.0
        half_shaft = shaft_width / 2.0
        half_head = head_width / 2.0
        junction_x = half_len - head_length

        points = [
            QPointF(-half_len, -half_shaft),
            QPointF(junction_x, -half_shaft),
            QPointF(junction_x, -half_head),
            QPointF(half_len, 0.0),
            QPointF(junction_x, half_head),
            QPointF(junction_x, half_shaft),
            QPointF(-half_len, half_shaft),
        ]
        polygon = QPolygonF(points)

        # Draw anti-aliased light gray arrow with dark outline
        painter.setBrush(QColor(200, 200, 200, 230))
        painter.setPen(QPen(QColor(50, 50, 50, 180), max(1.5, square_size * 0.03)))
        painter.drawPolygon(polygon)

        painter.restore()


class ChessWindow(QMainWindow):
    """Main application window hosting the main menu and the chess board."""

    def __init__(self, free_move: bool = False, start_in_menu: Optional[bool] = None) -> None:
        super().__init__()
        self.setWindowTitle("Chess Qt")

        # Central Stacked Widget
        self.stack = QStackedWidget(self)
        self.setCentralWidget(self.stack)

        # 1. Main Menu Screen
        self.menu_widget = MainMenuWidget(self)
        self.menu_widget.turn_based_selected.connect(lambda: self.start_game(free_move=False))
        self.menu_widget.free_move_selected.connect(lambda: self.start_game(free_move=True))
        self.menu_widget.tutorial_selected.connect(self.show_tutorial)
        self.menu_widget.credits_selected.connect(self.show_credits)
        self.menu_widget.exit_selected.connect(self.close)
        self.stack.addWidget(self.menu_widget)  # Index 0

        # 2. Game Screen Container
        self.game_container = QWidget(self)
        self.game_container_layout = QVBoxLayout(self.game_container)
        self.game_container_layout.setContentsMargins(0, 0, 0, 0)
        self.game_container_layout.setSpacing(0)

        # In-game Top Bar
        self.top_bar = QFrame(self.game_container)
        self.top_bar.setFixedHeight(46)
        self.top_bar.setStyleSheet("""
            QFrame {
                background-color: #202026;
                border-bottom: 2px solid #3d3d48;
            }
            QPushButton {
                background-color: #2e2e38;
                color: #f0f0f5;
                border: 1px solid #484856;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #3f3f4c;
                border-color: #d7cd64;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #1a1a20;
            }
            QLabel {
                color: #d7cd64;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        top_bar_layout = QHBoxLayout(self.top_bar)
        top_bar_layout.setContentsMargins(14, 5, 14, 5)

        self.menu_btn = QPushButton("◀ Menu", self.top_bar)
        self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_btn.setToolTip("Return to Main Menu")
        self.menu_btn.clicked.connect(self.return_to_menu)
        top_bar_layout.addWidget(self.menu_btn)

        top_bar_layout.addStretch()

        self.status_label = QLabel(self.top_bar)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_bar_layout.addWidget(self.status_label)

        top_bar_layout.addStretch()

        self.restart_btn = QPushButton("↺ Restart", self.top_bar)
        self.restart_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.restart_btn.setToolTip("Restart match with current mode")
        self.restart_btn.clicked.connect(self.restart_current_game)
        top_bar_layout.addWidget(self.restart_btn)

        self.game_container_layout.addWidget(self.top_bar)

        # Chess Board Widget
        self.board_widget = ChessBoardWidget(self.game_container, free_move=free_move)
        self.board_widget.game_over_signal.connect(self.on_game_over)
        self.board_widget.turn_changed.connect(self.on_turn_changed)
        self.game_container_layout.addWidget(self.board_widget)

        self.stack.addWidget(self.game_container)  # Index 1

        self.is_free_move = free_move

        # Set sizing
        self.setMinimumSize(QSize(480, 540))
        self.resize(QSize(660, 700))

        if start_in_menu is None:
            start_in_menu = not free_move

        if start_in_menu:
            self.show_menu()
        else:
            self.start_game(free_move=free_move)

    def show_menu(self) -> None:
        """Switches display to the main menu screen."""
        self.stack.setCurrentWidget(self.menu_widget)

    def return_to_menu(self) -> None:
        """Returns from gameplay to the main menu."""
        self.show_menu()

    def start_game(self, free_move: bool = False) -> None:
        """Initializes a fresh game with the chosen mode and switches to board view."""
        self.is_free_move = free_move
        self.board_widget.reset_game(free_move=free_move)
        self._update_status_display()
        self.stack.setCurrentWidget(self.game_container)

    def restart_current_game(self) -> None:
        """Restarts the board with the currently active mode."""
        self.board_widget.reset_game(free_move=self.is_free_move)
        self._update_status_display()

    def on_turn_changed(self, turn_name: str) -> None:
        """Updates the status bar when turn changes."""
        self._update_status_display()

    def _update_status_display(self) -> None:
        """Updates status text in top bar."""
        if self.is_free_move:
            self.status_label.setText("⚡ Free Move Mode (Sandbox)")
        else:
            turn_str = self.board_widget.current_turn.name
            icon = "⚪" if turn_str == "WHITE" else "⚫"
            self.status_label.setText(f"⚔ Turn-Based Mode • {icon} {turn_str}'s Turn")

    def on_game_over(self, winner: str) -> None:
        """Re-opens the main menu when someone wins or loses."""
        self.show_menu()

    def show_tutorial(self) -> None:
        """Displays the how-to-play tutorial dialog."""
        dialog = TutorialDialog(self)
        dialog.exec()

    def show_credits(self) -> None:
        """Displays the credits dialog."""
        dialog = CreditsDialog(self)
        dialog.exec()


def main() -> None:
    import argparse

    # Activate signal handler so that Ctrl+C finishes the program
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    parser = argparse.ArgumentParser(description="Chess game application")
    parser.add_argument(
        "--free-move",
        action="store_true",
        help="Disable turn enforcement to allow free movement of pieces.",
    )
    args, _ = parser.parse_known_args(sys.argv[1:])

    app = QApplication.instance() or QApplication(sys.argv)
    window = ChessWindow(free_move=args.free_move, start_in_menu=not args.free_move)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
