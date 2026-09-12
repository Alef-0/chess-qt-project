"""Main entry point for the Chess game application."""

import sys
from PyQt6.QtWidgets import QApplication
from board import ChessWindow


def main() -> None:
    """Initializes and runs the Chess application."""
    app = QApplication(sys.argv)
    window = ChessWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
