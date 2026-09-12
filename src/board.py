"""Chess board implementation using PyQt6."""

import sys
from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QResizeEvent
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
from pieces import BoardPieces


class ChessBoardWidget(QWidget):
    """Widget responsible for rendering a resizable 8x8 chessboard while maintaining aspect ratio."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        # Colors configured within [50, 225] range to avoid display strain
        self.dark_square_color = QColor(50, 50, 50)       # Minimum brightness bound
        self.light_square_color = QColor(225, 225, 225)   # Maximum brightness bound
        self.border_color = QColor(115, 70, 40)           # Natural brown border
        self.background_color = QColor(30, 30, 30)        # Letterbox background

        # Pieces placement and state
        self.pieces = BoardPieces()

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
        width = self.width()
        height = self.height()
        board_total_size = min(width, height)
        if board_total_size > 0:
            border_thickness = max(4.0, board_total_size * 0.035)
            inner_board_size = board_total_size - (2.0 * border_thickness)
            if inner_board_size > 0:
                square_size = inner_board_size / 8.0
                self.pieces.update_size(max(1, round(square_size)))

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paints the 8x8 chessboard with border, centered and preserving aspect ratio."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        width = self.width()
        height = self.height()

        # Fill overall widget background (letterbox / pillarbox areas)
        painter.fillRect(0, 0, width, height, self.background_color)

        # Determine largest square board that fits within the current widget dimensions
        board_total_size = min(width, height)
        if board_total_size <= 0:
            return

        # Calculate offsets to center the square chessboard in the widget
        offset_x = (width - board_total_size) / 2.0
        offset_y = (height - board_total_size) / 2.0

        # Border thickness is proportional to board size (e.g. ~3.5% of total size)
        border_thickness = max(4.0, board_total_size * 0.035)

        # Draw outer brown border
        border_rect = QRectF(offset_x, offset_y, board_total_size, board_total_size)
        painter.fillRect(border_rect, self.border_color)

        # Dimensions of the inner 8x8 chessboard
        inner_x = offset_x + border_thickness
        inner_y = offset_y + border_thickness
        inner_board_size = board_total_size - (2.0 * border_thickness)

        if inner_board_size <= 0:
            return

        square_size = inner_board_size / 8.0

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

        # Draw pieces on top of the squares
        self.pieces.draw(painter, inner_x, inner_y, square_size)


class ChessWindow(QMainWindow):
    """Main application window hosting the chess board."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Chess Game")
        self.board_widget = ChessBoardWidget(self)
        self.setCentralWidget(self.board_widget)

        # Set a minimum window size respecting the widget's minimumSizeHint
        self.setMinimumSize(self.board_widget.minimumSizeHint())
        # Initial window size matching the widget's sizeHint
        self.resize(self.board_widget.sizeHint())


def main() -> None:
    app = QApplication(sys.argv)
    window = ChessWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
