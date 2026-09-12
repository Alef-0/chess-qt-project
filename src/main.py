"""Main entry point for the Chess game application."""

import sys
from pathlib import Path

# Ensure src directory is in sys.path when run or imported from anywhere
SRC_DIR = Path(__file__).parent.resolve()
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

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
