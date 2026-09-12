"""Chess pieces definition, enums, board state, and rendering."""

from enum import Enum
from typing import Optional, List
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPainter
from assets.sprites import get_piece_pixmap, recalculate_scaled_sprites, QPixmap


class PieceColor(Enum):
    """Color of a chess piece."""
    WHITE = "white"
    BLACK = "black"


class PieceType(Enum):
    """Type of a chess piece."""
    KING = "king"
    QUEEN = "queen"
    BISHOP = "bishop"
    KNIGHT = "knight"
    ROOK = "rook"
    PAWN = "pawn"


class Piece:
    """Represents an individual chess piece with a color and type."""

    def __init__(self, color: PieceColor, piece_type: PieceType) -> None:
        self.color = color
        self.piece_type = piece_type

    @property
    def pixmap(self) -> QPixmap:
        """Returns the QPixmap for this piece from the sprite cache."""
        return get_piece_pixmap(self.color, self.piece_type)

    @property
    def symbol(self) -> str:
        """Returns the standard single-character notation for this piece.

        Uppercase for white (K, Q, B, N, R, P) and lowercase for black (k, q, b, n, r, p).
        """
        type_to_char = {
            PieceType.KING: "k",
            PieceType.QUEEN: "q",
            PieceType.BISHOP: "b",
            PieceType.KNIGHT: "n",
            PieceType.ROOK: "r",
            PieceType.PAWN: "p",
        }
        char = type_to_char[self.piece_type]
        return char.upper() if self.color == PieceColor.WHITE else char

    def __repr__(self) -> str:
        return f"Piece({self.color.name}, {self.piece_type.name})"


class BoardPieces:
    """Manages the 8x8 placement of pieces and handles drawing them onto the board."""

    def __init__(self) -> None:
        # 8x8 grid initialized to None
        self.grid: List[List[Optional[Piece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.current_square_size: int = 0
        self.setup_initial_position()

    def update_size(self, square_size: int) -> None:
        """Recalculates scaled piece sprites to match the new square size."""
        if square_size > 0 and square_size != self.current_square_size:
            self.current_square_size = square_size
            recalculate_scaled_sprites(square_size)

    def setup_initial_position(self) -> None:
        """Sets up standard chess starting position."""
        back_rank_types = [
            PieceType.ROOK,
            PieceType.KNIGHT,
            PieceType.BISHOP,
            PieceType.QUEEN,
            PieceType.KING,
            PieceType.BISHOP,
            PieceType.KNIGHT,
            PieceType.ROOK,
        ]

        # Row 0 (Rank 8): Black major/minor pieces
        for col, p_type in enumerate(back_rank_types):
            self.grid[0][col] = Piece(PieceColor.BLACK, p_type)

        # Row 1 (Rank 7): Black pawns
        for col in range(8):
            self.grid[1][col] = Piece(PieceColor.BLACK, PieceType.PAWN)

        # Rows 2 to 5 (Ranks 6 to 3): Empty squares
        for row in range(2, 6):
            for col in range(8):
                self.grid[row][col] = None

        # Row 6 (Rank 2): White pawns
        for col in range(8):
            self.grid[6][col] = Piece(PieceColor.WHITE, PieceType.PAWN)

        # Row 7 (Rank 1): White major/minor pieces
        for col, p_type in enumerate(back_rank_types):
            self.grid[7][col] = Piece(PieceColor.WHITE, p_type)

    def get_piece(self, row: int, col: int) -> Optional[Piece]:
        """Returns the piece at the given (row, col), or None if empty or out of bounds."""
        if 0 <= row < 8 and 0 <= col < 8:
            return self.grid[row][col]
        return None

    def set_piece(self, row: int, col: int, piece: Optional[Piece]) -> None:
        """Places a piece (or None) at the given (row, col)."""
        if 0 <= row < 8 and 0 <= col < 8:
            self.grid[row][col] = piece

    def move_piece(self, from_row: int, from_col: int, to_row: int, to_col: int) -> Optional[Piece]:
        """Moves a piece from one square to another, returning any captured piece."""
        moving_piece = self.get_piece(from_row, from_col)
        if moving_piece is None:
            return None
        captured = self.get_piece(to_row, to_col)
        self.set_piece(to_row, to_col, moving_piece)
        self.set_piece(from_row, from_col, None)
        return captured

    def draw(self, painter: QPainter, inner_x: float, inner_y: float, square_size: float) -> None:
        """Draws all active pieces onto the board using smoothly scaled pixmaps."""
        target_size = max(1, round(square_size))
        if self.current_square_size != target_size:
            self.update_size(target_size)

        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        for row in range(8):
            for col in range(8):
                piece = self.grid[row][col]
                if piece is not None:
                    sq_x = inner_x + col * square_size
                    sq_y = inner_y + row * square_size
                    target_rect = QRectF(sq_x, sq_y, square_size, square_size)
                    painter.drawPixmap(target_rect, piece.pixmap, QRectF(piece.pixmap.rect()))
