"""Chess pieces definition, enums, board state, and rendering."""

from enum import Enum
from typing import Optional, List, Tuple
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
        self.has_moved: bool = False

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
        self.en_passant_target: Optional[Tuple[int, int]] = None
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

    def _apply_en_passant(
        self, from_row: int, from_col: int, to_row: int, to_col: int, piece: Piece
    ) -> Optional[Piece]:
        """Executes an en passant pawn capture, removing the passed enemy pawn."""
        captured = self.get_piece(from_row, to_col)
        self.set_piece(from_row, to_col, None)
        self.set_piece(to_row, to_col, piece)
        self.set_piece(from_row, from_col, None)
        return captured

    def _apply_castling(
        self, from_row: int, from_col: int, to_row: int, to_col: int, piece: Piece
    ) -> Optional[Piece]:
        """Executes castling by relocating both king and corresponding rook."""
        self.set_piece(to_row, to_col, piece)
        self.set_piece(from_row, from_col, None)
        rook_col = 7 if to_col == 6 else 0
        target_rook_col = 5 if to_col == 6 else 3
        rook = self.get_piece(from_row, rook_col)
        if rook is not None:
            rook.has_moved = True
            self.set_piece(from_row, target_rook_col, rook)
            self.set_piece(from_row, rook_col, None)
        return None

    def _apply_normal_move(
        self, from_row: int, from_col: int, to_row: int, to_col: int, piece: Piece
    ) -> Optional[Piece]:
        """Executes a standard move, capturing any piece on the target square."""
        captured = self.get_piece(to_row, to_col)
        self.set_piece(to_row, to_col, piece)
        self.set_piece(from_row, from_col, None)
        return captured

    def _update_en_passant_target(
        self, from_row: int, to_row: int, from_col: int, piece: Piece
    ) -> None:
        """Sets the skipped square on a 2-step pawn advance, or clears en passant state."""
        if piece.piece_type == PieceType.PAWN and abs(to_row - from_row) == 2:
            self.en_passant_target = ((from_row + to_row) // 2, from_col)
        else:
            self.en_passant_target = None

    def move_piece(self, from_row: int, from_col: int, to_row: int, to_col: int) -> Optional[Piece]:
        """Moves a piece from one square to another, returning any captured piece."""
        moving_piece = self.get_piece(from_row, from_col)
        if moving_piece is None:
            return None

        handlers = {
            "en_passant": self._apply_en_passant,
            "castling": self._apply_castling,
            "normal": self._apply_normal_move,
        }

        category = self.get_move_category(from_row, from_col, to_row, to_col)
        captured = handlers[category](from_row, from_col, to_row, to_col, moving_piece)

        moving_piece.has_moved = True
        self._update_en_passant_target(from_row, to_row, from_col, moving_piece)

        return captured

    def _get_en_passant_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Returns valid en passant capture target squares for a pawn at (row, col)."""
        piece = self.get_piece(row, col)
        if piece is None or piece.piece_type != PieceType.PAWN or self.en_passant_target is None:
            return []

        direction = -1 if piece.color == PieceColor.WHITE else 1
        ep_row, ep_col = self.en_passant_target
        if ep_row == row + direction and abs(ep_col - col) == 1:
            # En passant strictly captures an opponent pawn on the adjacent square (row, ep_col)
            target_pawn = self.get_piece(row, ep_col)
            if (
                target_pawn is not None
                and target_pawn.piece_type == PieceType.PAWN
                and target_pawn.color != piece.color
            ):
                return [(ep_row, ep_col)]

        return []

    def _get_castling_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Returns valid castling destination squares for a king at (row, col).

        Validates that neither king nor rook has moved, and intermediate squares are clear.
        """
        king = self.get_piece(row, col)
        if king is None or king.piece_type != PieceType.KING or king.has_moved:
            return []

        expected_row = 7 if king.color == PieceColor.WHITE else 0
        if row != expected_row or col != 4:
            return []

        moves: List[Tuple[int, int]] = []

        # Kingside castling (col 4 -> col 6, rook at col 7)
        kingside_rook = self.get_piece(row, 7)
        if (
            kingside_rook is not None
            and kingside_rook.piece_type == PieceType.ROOK
            and kingside_rook.color == king.color
            and not kingside_rook.has_moved
        ):
            if self.get_piece(row, 5) is None and self.get_piece(row, 6) is None:
                moves.append((row, 6))

        # Queenside castling (col 4 -> col 2, rook at col 0)
        queenside_rook = self.get_piece(row, 0)
        if (
            queenside_rook is not None
            and queenside_rook.piece_type == PieceType.ROOK
            and queenside_rook.color == king.color
            and not queenside_rook.has_moved
        ):
            if (
                self.get_piece(row, 1) is None
                and self.get_piece(row, 2) is None
                and self.get_piece(row, 3) is None
            ):
                moves.append((row, 2))

        return moves

    def get_move_category(self, from_row: int, from_col: int, to_row: int, to_col: int) -> str:
        """Returns the category for a move: 'en_passant', 'castling', or 'normal'."""
        piece = self.get_piece(from_row, from_col)
        if piece is None:
            return "normal"
        if (
            piece.piece_type == PieceType.PAWN
            and self.en_passant_target is not None
            and (to_row, to_col) == self.en_passant_target
        ):
            target_pawn = self.get_piece(from_row, to_col)
            if (
                target_pawn is not None
                and target_pawn.piece_type == PieceType.PAWN
                and target_pawn.color != piece.color
            ):
                return "en_passant"
        if piece.piece_type == PieceType.KING and abs(to_col - from_col) == 2:
            return "castling"
        return "normal"

    def get_valid_moves(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Returns a list of valid destination coordinates (target_row, target_col) for the piece at (row, col).

        Implements standard piece moves with blocking, captures, en passant, and castling.
        """
        piece = self.get_piece(row, col)
        if piece is None:
            return []

        moves: List[Tuple[int, int]] = []

        if piece.piece_type == PieceType.PAWN:
            direction = -1 if piece.color == PieceColor.WHITE else 1
            start_row = 6 if piece.color == PieceColor.WHITE else 1

            # 1 square forward (must be empty)
            fwd_row = row + direction
            if 0 <= fwd_row < 8 and self.get_piece(fwd_row, col) is None:
                moves.append((fwd_row, col))
                # 2 squares forward from starting rank (both 1-step and 2-step squares must be empty)
                fwd2_row = row + 2 * direction
                if row == start_row and 0 <= fwd2_row < 8 and self.get_piece(fwd2_row, col) is None:
                    moves.append((fwd2_row, col))

            # Diagonal captures (standard enemy piece)
            for dc in (-1, 1):
                cap_row = row + direction
                cap_col = col + dc
                if 0 <= cap_row < 8 and 0 <= cap_col < 8:
                    target = self.get_piece(cap_row, cap_col)
                    if target is not None and target.color != piece.color:
                        moves.append((cap_row, cap_col))

            # En passant capture (via dedicated helper function)
            moves.extend(self._get_en_passant_moves(row, col))

        elif piece.piece_type == PieceType.ROOK:
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            self._add_ray_moves(row, col, directions, piece.color, moves)

        elif piece.piece_type == PieceType.BISHOP:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            self._add_ray_moves(row, col, directions, piece.color, moves)

        elif piece.piece_type == PieceType.QUEEN:
            directions = [
                (-1, 0), (1, 0), (0, -1), (0, 1),
                (-1, -1), (-1, 1), (1, -1), (1, 1),
            ]
            self._add_ray_moves(row, col, directions, piece.color, moves)

        elif piece.piece_type == PieceType.KNIGHT:
            knight_offsets = [
                (-2, -1), (-2, 1),
                (-1, -2), (-1, 2),
                (1, -2), (1, 2),
                (2, -1), (2, 1),
            ]
            for dr, dc in knight_offsets:
                r, c = row + dr, col + dc
                if 0 <= r < 8 and 0 <= c < 8:
                    target = self.get_piece(r, c)
                    if target is None or target.color != piece.color:
                        moves.append((r, c))

        elif piece.piece_type == PieceType.KING:
            king_offsets = [
                (-1, -1), (-1, 0), (-1, 1),
                (0, -1),           (0, 1),
                (1, -1),  (1, 0),  (1, 1),
            ]
            for dr, dc in king_offsets:
                r, c = row + dr, col + dc
                if 0 <= r < 8 and 0 <= c < 8:
                    target = self.get_piece(r, c)
                    if target is None or target.color != piece.color:
                        moves.append((r, c))

            # Castling moves (via dedicated helper function)
            moves.extend(self._get_castling_moves(row, col))

        return moves

    def _add_ray_moves(
        self,
        row: int,
        col: int,
        directions: List[Tuple[int, int]],
        color: PieceColor,
        moves: List[Tuple[int, int]],
    ) -> None:
        """Slides in ray directions until hitting a board boundary or piece."""
        for dr, dc in directions:
            r, c = row + dr, col + dc
            while 0 <= r < 8 and 0 <= c < 8:
                target = self.get_piece(r, c)
                if target is None:
                    moves.append((r, c))
                else:
                    if target.color != color:
                        moves.append((r, c))
                    break
                r += dr
                c += dc

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
