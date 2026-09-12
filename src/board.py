"""Chess board implementation using PyQt6."""

import math
import signal
import sys
from typing import List, Optional, Tuple
from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent, QPen, QPolygonF, QResizeEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from pieces import BoardPieces, PieceColor


class ChessBoardWidget(QWidget):
    """Widget responsible for rendering a resizable 8x8 chessboard while maintaining aspect ratio."""

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
        if square_size > 0:
            self.pieces.update_size(max(1, round(square_size)))

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handles mouse clicks to select pieces and execute moves."""
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
        if self.selected_square is None:
            # Select piece if present and belongs to current turn
            piece = self.pieces.get_piece(row, col)
            if piece is not None:
                if self.turn_enabled and piece.color != self.current_turn:
                    return
                self.selected_square = (row, col)
                self.valid_moves = self.pieces.get_valid_moves(row, col)
                self.update()
        else:
            sel_row, sel_col = self.selected_square
            if (row, col) in self.valid_moves:
                # Execute move to valid destination square
                self.pieces.move_piece(sel_row, sel_col, row, col)
                self.selected_square = None
                self.valid_moves = []
                if self.turn_enabled:
                    self.current_turn = (
                        PieceColor.BLACK if self.current_turn == PieceColor.WHITE else PieceColor.WHITE
                    )
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
    """Main application window hosting the chess board."""

    def __init__(self, free_move: bool = False) -> None:
        super().__init__()
        self.setWindowTitle("Chess Game")
        self.board_widget = ChessBoardWidget(self, free_move=free_move)
        self.setCentralWidget(self.board_widget)

        # Set a minimum window size respecting the widget's minimumSizeHint
        self.setMinimumSize(self.board_widget.minimumSizeHint())
        # Initial window size matching the widget's sizeHint
        self.resize(self.board_widget.sizeHint())


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

    app = QApplication(sys.argv)
    window = ChessWindow(free_move=args.free_move)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
