# Chess Qt

A chess game built from scratch using Python and PyQt6.

## Features
- **Custom Board Rendering**: Scalable 8x8 chessboard with brown boundary border.
- **Aspect-Ratio Preservation**: Centered square board with letterbox/pillarbox margins upon non-square window resizing.
- **Bounded Brightness**: Colors clamped between 50 and 225 to avoid eye strain and display clipping.
- **Anti-Aliased Sprites**: Original high-resolution master piece sprites stored unscaled and dynamically resampled on resize to eliminate choppiness.
- **Typed Piece Architecture**: `PieceColor` and `PieceType` enums with standard chess setup.

## Project Structure

```
chess_project/
├── src/
│   ├── assets/
│   │   ├── Sprites.webp       # Chess pieces master sprite sheet (3840x1280)
│   │   └── sprites.py         # Sprite coordinates & smooth resize manager
│   ├── board.py               # ChessBoardWidget & ChessWindow
│   ├── pieces.py              # Piece enums, Piece class & BoardPieces state
│   └── main.py                # Core application entry point
├── main.py                    # Root entry point launcher
├── .gitignore
├── pyproject.toml
└── README.md
```

## Requirements
- Python 3.10+
- PyQt6
- Pillow

## Running the Application

```bash
python3 src/main.py
# or
python3 main.py

# Free move mode (disables turn enforcement):
python3 main.py --free-move
```
