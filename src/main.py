"""Main entry point for the Chess game application."""

import argparse
import signal
import sys
from pathlib import Path

# Ensure src directory is in sys.path when run or imported from anywhere
SRC_DIR = Path(__file__).parent.resolve()
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from PyQt6.QtWidgets import QApplication
from board import ChessWindow


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(description="Chess game application")
    parser.add_argument(
        "--free-move",
        action="store_true",
        help="Disable turn enforcement to allow free movement of pieces.",
    )
    parsed_args, _ = parser.parse_known_args(args)
    return parsed_args


def main(argv: list[str] | None = None) -> None:
    """Initializes and runs the Chess application."""
    # Activate signal handler so that Ctrl+C finishes the program
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    args = parse_args(argv if argv is not None else sys.argv[1:])

    app = QApplication.instance() or QApplication(sys.argv)
    window = ChessWindow(free_move=args.free_move)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
