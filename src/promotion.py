"""Pawn promotion floating selection dialog."""

from typing import Optional
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget
from pieces import PieceColor, PieceType
from assets.sprites import get_piece_pixmap


class PromotionDialog(QDialog):
    """Floating dialog allowing the player to select a piece for pawn promotion."""

    def __init__(self, color: PieceColor, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.color = color
        self.selected_piece_type: PieceType = PieceType.QUEEN

        self.setWindowTitle("Pawn Promotion")
        self.setModal(True)
        # Floating dialog styling
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.CustomizeWindowHint)

        self.setStyleSheet("""
            QDialog {
                background-color: #2b2b2b;
                border: 2px solid #734628;
                border-radius: 8px;
            }
            QLabel {
                color: #e1e1e1;
                font-size: 14px;
                font-weight: bold;
                padding: 4px;
            }
            QPushButton {
                background-color: #383838;
                border: 2px solid #505050;
                border-radius: 6px;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
                border: 2px solid #d7cd64;
            }
            QPushButton:pressed {
                background-color: #282828;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(10)

        title_label = QLabel("Select piece to transform:", self)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        promotion_types = [
            PieceType.QUEEN,
            PieceType.ROOK,
            PieceType.BISHOP,
            PieceType.KNIGHT,
        ]

        button_size = 64
        for p_type in promotion_types:
            btn = QPushButton(self)
            btn.setFixedSize(button_size, button_size)
            btn.setToolTip(p_type.name.capitalize())

            # Load high-res piece pixmap and set as button icon
            pixmap = get_piece_pixmap(self.color, p_type)
            btn.setIcon(QIcon(pixmap))
            btn.setIconSize(QSize(button_size - 12, button_size - 12))

            # Connect button click
            btn.clicked.connect(lambda checked, t=p_type: self._on_piece_selected(t))
            button_layout.addWidget(btn)

        layout.addLayout(button_layout)
        self.adjustSize()

    def _on_piece_selected(self, piece_type: PieceType) -> None:
        """Stores the chosen piece type and accepts the dialog."""
        self.selected_piece_type = piece_type
        self.accept()


def prompt_promotion(color: PieceColor, parent: Optional[QWidget] = None) -> PieceType:
    """Displays the promotion selection dialog and returns the chosen PieceType (defaults to QUEEN)."""
    dialog = PromotionDialog(color, parent)
    dialog.exec()
    return dialog.selected_piece_type
