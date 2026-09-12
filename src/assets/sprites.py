"""Sprite sheet coordinates, dimensions, master storage, and dynamic resizing for chess pieces."""

from pathlib import Path
from typing import Any, Tuple
from PIL import Image
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QImage, QPixmap

# Dimensions of the full sprite sheet and individual sprite cells
SHEET_WIDTH = 3840
SHEET_HEIGHT = 1280
SPRITE_WIDTH = 640
SPRITE_HEIGHT = 640

# Path to the source sprite sheet
SPRITES_IMAGE_PATH = Path(__file__).parent / "Sprites.webp"

# Sprite bounding rectangles in (x, y, width, height) format
# Row 0 (y=0): White pieces
# Row 1 (y=640): Black pieces
SPRITE_COORDINATES: dict[Tuple[str, str], Tuple[int, int, int, int]] = {
    # White pieces
    ("white", "king"):   (0, 0, SPRITE_WIDTH, SPRITE_HEIGHT),
    ("white", "queen"):  (640, 0, SPRITE_WIDTH, SPRITE_HEIGHT),
    ("white", "bishop"): (1280, 0, SPRITE_WIDTH, SPRITE_HEIGHT),
    ("white", "knight"): (1920, 0, SPRITE_WIDTH, SPRITE_HEIGHT),
    ("white", "rook"):   (2560, 0, SPRITE_WIDTH, SPRITE_HEIGHT),
    ("white", "pawn"):   (3200, 0, SPRITE_WIDTH, SPRITE_HEIGHT),

    # Black pieces
    ("black", "king"):   (0, 640, SPRITE_WIDTH, SPRITE_HEIGHT),
    ("black", "queen"):  (640, 640, SPRITE_WIDTH, SPRITE_HEIGHT),
    ("black", "bishop"): (1280, 640, SPRITE_WIDTH, SPRITE_HEIGHT),
    ("black", "knight"): (1920, 640, SPRITE_WIDTH, SPRITE_HEIGHT),
    ("black", "rook"):   (2560, 640, SPRITE_WIDTH, SPRITE_HEIGHT),
    ("black", "pawn"):   (3200, 640, SPRITE_WIDTH, SPRITE_HEIGHT),
}

# Original unscaled master sprites stored as-is at full resolution (640x640)
_master_sprites: dict[Tuple[str, str], QPixmap] = {}

# Current active resized sprites matching the window/board square size
_current_resized_sprites: dict[Tuple[str, str], QPixmap] = {}
_current_sprite_size: int = 0


def _normalize_key(color: Any, piece_type: Any) -> Tuple[str, str]:
    """Normalize color and piece_type whether passed as Enums or strings."""
    c = color.value if hasattr(color, "value") else str(color).lower()
    t = piece_type.value if hasattr(piece_type, "value") else str(piece_type).lower()
    return (c, t)


def get_sprite_rect(color: Any, piece_type: Any) -> Tuple[int, int, int, int]:
    """Returns the (x, y, width, height) of the piece sprite within the original sprite sheet."""
    key = _normalize_key(color, piece_type)
    if key not in SPRITE_COORDINATES:
        raise ValueError(f"Unknown piece combination: color={color}, piece_type={piece_type}")
    return SPRITE_COORDINATES[key]


def _ensure_master_sprites_loaded() -> None:
    """Loads the original full-resolution master image and stores each piece as-is."""
    global _master_sprites
    if _master_sprites: return
    if not SPRITES_IMAGE_PATH.exists(): raise FileNotFoundError(f"Sprite sheet not found at {SPRITES_IMAGE_PATH}")
    # Decode original WebP file using Pillow to RGBA bytes
    pil_image = Image.open(SPRITES_IMAGE_PATH).convert("RGBA")
    qimage = QImage(
        pil_image.tobytes(),
        pil_image.width,
        pil_image.height,
        pil_image.width * 4,
        QImage.Format.Format_RGBA8888,
    )
    master_sheet_pixmap = QPixmap.fromImage(qimage)

    # Store each piece's original 640x640 sprite as-is
    for key, (x, y, w, h) in SPRITE_COORDINATES.items():
        _master_sprites[key] = master_sheet_pixmap.copy(x, y, w, h)


def recalculate_scaled_sprites(target_size: int) -> None:
    """Recalculates all piece sprites directly from the original master image to the exact target_size.

    Called whenever the window or board is resized.
    Using Qt.TransformationMode.SmoothTransformation on the original unscaled image produces
    clean, anti-aliased, non-choppy curves.
    """
    global _current_resized_sprites, _current_sprite_size
    if target_size <= 0 or target_size == _current_sprite_size:
        return

    _ensure_master_sprites_loaded()

    # Re-scale each original master sprite directly to the target size
    for key, master_pixmap in _master_sprites.items():
        _current_resized_sprites[key] = master_pixmap.scaled(
            target_size,
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    _current_sprite_size = target_size


def get_piece_pixmap(color: Any, piece_type: Any) -> QPixmap:
    """Returns the current resized QPixmap for the requested piece.

    If not yet resized, loads and uses the master sprite.
    """
    key = _normalize_key(color, piece_type)
    if key in _current_resized_sprites: return _current_resized_sprites[key]

    _ensure_master_sprites_loaded()
    if key in _master_sprites: return _master_sprites[key]

    raise ValueError(f"Unknown piece combination: color={color}, piece_type={piece_type}")
