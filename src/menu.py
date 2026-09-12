"""Menu system with procedural graphics, mode selection, tutorial, and credits for Chess Qt."""

from typing import Any, Callable, List, Optional, Tuple
from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QMouseEvent,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
    QPixmap,
    QPolygonF,
    QRadialGradient,
    QResizeEvent,
)
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from assets.sprites import get_master_piece_pixmap, get_piece_pixmap
from pieces import PieceColor, PieceType


class ChessCrestWidget(QWidget):
    """Custom procedural vector graphics widget rendering an elegant heraldic chess crest."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.scale: float = 1.0
        self.setFixedHeight(170)
        self.setMinimumWidth(360)

    def update_scale(self, scale: float) -> None:
        """Updates scaling factor and dimensions for dynamic window resizing."""
        self.scale = max(0.5, scale)
        self.setFixedHeight(max(90, int(170 * self.scale)))
        self.setMinimumWidth(max(200, int(360 * self.scale)))
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paints the royal chess crest, crown, decorative shield, and flanked pieces."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        scale = self.scale
        cx = self.width() / 2.0
        cy = self.height() / 2.0 - 10.0 * scale

        # 1. Outer decorative shield / crest background
        shield_width = 240.0 * scale
        shield_height = 140.0 * scale
        shield_rect = QRectF(cx - shield_width / 2.0, cy - shield_height / 2.0 + 8.0 * scale, shield_width, shield_height)

        # Shield gradient
        shield_grad = QLinearGradient(cx, shield_rect.top(), cx, shield_rect.bottom())
        shield_grad.setColorAt(0.0, QColor(42, 42, 48, 230))
        shield_grad.setColorAt(1.0, QColor(22, 22, 26, 240))

        # Build shield path
        shield_path = QPainterPath()
        top = shield_rect.top()
        left = shield_rect.left()
        right = shield_rect.right()
        bottom = shield_rect.bottom()

        c_offset = 20.0 * scale
        t_dip = 10.0 * scale
        s_radius = 40.0 * scale
        b_dip = 30.0 * scale
        b_tip = 12.0 * scale

        shield_path.moveTo(left + c_offset, top)
        shield_path.quadTo(cx, top - t_dip, right - c_offset, top)
        shield_path.quadTo(right, top + t_dip, right, top + s_radius)
        shield_path.quadTo(right, bottom - b_dip, cx, bottom + b_tip)
        shield_path.quadTo(left, bottom - b_dip, left, top + s_radius)
        shield_path.quadTo(left, top + t_dip, left + c_offset, top)
        shield_path.closeSubpath()

        painter.fillPath(shield_path, QBrush(shield_grad))

        # Golden border on shield
        gold_pen = QPen(QColor(215, 205, 100), max(1.5, 2.5 * scale))
        painter.setPen(gold_pen)
        painter.drawPath(shield_path)

        # Inner subtle shield border
        inner_pen = QPen(QColor(180, 150, 60, 100), max(1.0, 1.2 * scale))
        painter.setPen(inner_pen)
        painter.drawPath(shield_path)

        # 2. Flanking pieces (using original master spritesheet for crisp high-res rendering)
        sprite_size = max(24, int(54 * scale))
        try:
            knight_pix = get_master_piece_pixmap(PieceColor.WHITE, PieceType.KNIGHT).scaled(
                sprite_size, sprite_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            queen_pix = get_master_piece_pixmap(PieceColor.BLACK, PieceType.QUEEN).scaled(
                sprite_size, sprite_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            # Draw White Knight on left flank
            painter.drawPixmap(int(cx - 108 * scale), int(cy - 20 * scale), knight_pix)
            # Draw Black Queen on right flank
            painter.drawPixmap(int(cx + 54 * scale), int(cy - 20 * scale), queen_pix)
        except Exception:
            pass

        # 3. Procedural Golden Crown in Center
        crown_width = 64.0 * scale
        crown_height = 42.0 * scale
        crown_left = cx - crown_width / 2.0
        crown_top = cy - 26.0 * scale

        crown_path = QPainterPath()
        crown_path.moveTo(crown_left, crown_top + crown_height)
        crown_path.lineTo(crown_left + crown_width, crown_top + crown_height)
        crown_path.lineTo(crown_left + crown_width - 4 * scale, crown_top + 10 * scale)
        crown_path.lineTo(crown_left + crown_width * 0.72, crown_top + 20 * scale)
        crown_path.lineTo(cx, crown_top)
        crown_path.lineTo(crown_left + crown_width * 0.28, crown_top + 20 * scale)
        crown_path.lineTo(crown_left + 4 * scale, crown_top + 10 * scale)
        crown_path.closeSubpath()

        # Crown gold gradient
        crown_grad = QLinearGradient(cx, crown_top, cx, crown_top + crown_height)
        crown_grad.setColorAt(0.0, QColor(255, 235, 120))
        crown_grad.setColorAt(0.5, QColor(215, 185, 60))
        crown_grad.setColorAt(1.0, QColor(160, 120, 30))

        painter.fillPath(crown_path, QBrush(crown_grad))
        painter.setPen(QPen(QColor(80, 50, 10), max(1.0, 1.5 * scale)))
        painter.drawPath(crown_path)

        # Crown jewels (5 glowing gems)
        jewel_coords = [
            (crown_left + 4 * scale, crown_top + 10 * scale, QColor(220, 60, 60)),     # Ruby
            (crown_left + crown_width * 0.28, crown_top + 20 * scale, QColor(60, 160, 240)),  # Sapphire
            (cx, crown_top, QColor(255, 255, 255)),                     # Diamond
            (crown_left + crown_width * 0.72, crown_top + 20 * scale, QColor(60, 160, 240)),  # Sapphire
            (crown_left + crown_width - 4 * scale, crown_top + 10 * scale, QColor(220, 60, 60)),     # Ruby
        ]
        gem_r = max(1.5, 3.0 * scale)
        for jx, jy, jcolor in jewel_coords:
            painter.setPen(QPen(QColor(40, 20, 10), max(0.8, 1.0 * scale)))
            painter.setBrush(QBrush(jcolor))
            painter.drawEllipse(QPointF(jx, jy), gem_r, gem_r)

        # Crown base rim
        rim_rect = QRectF(crown_left + 2 * scale, crown_top + crown_height - 6 * scale, crown_width - 4 * scale, 6 * scale)
        painter.setBrush(QBrush(QColor(230, 200, 80)))
        painter.setPen(QPen(QColor(70, 45, 10), max(0.8, 1.0 * scale)))
        painter.drawRoundedRect(rim_rect, max(1.0, 2.0 * scale), max(1.0, 2.0 * scale))

        # 4. Golden Banner Ribbon at bottom
        banner_w = 180.0 * scale
        banner_h = 32.0 * scale
        banner_x = cx - banner_w / 2.0
        banner_y = cy + 34.0 * scale

        banner_path = QPainterPath()
        banner_path.addRoundedRect(QRectF(banner_x, banner_y, banner_w, banner_h), 5.0 * scale, 5.0 * scale)

        banner_grad = QLinearGradient(cx, banner_y, cx, banner_y + banner_h)
        banner_grad.setColorAt(0.0, QColor(135, 80, 45))
        banner_grad.setColorAt(0.5, QColor(95, 55, 30))
        banner_grad.setColorAt(1.0, QColor(65, 35, 15))

        painter.fillPath(banner_path, QBrush(banner_grad))
        painter.setPen(QPen(QColor(215, 185, 75), max(1.2, 1.8 * scale)))
        painter.drawPath(banner_path)

        # Banner Title Text
        painter.setPen(QColor(245, 240, 220))
        title_font = QFont("DejaVu Sans", max(8, int(14 * scale)), QFont.Weight.Bold)
        title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, max(1.5, 4.0 * scale))
        painter.setFont(title_font)
        painter.drawText(
            QRectF(banner_x, banner_y + 1 * scale, banner_w, banner_h),
            Qt.AlignmentFlag.AlignCenter,
            "CHESS QT",
        )


class MenuOptionButton(QPushButton):
    """Custom-styled interactive button card with title, description, and procedural icon."""

    def __init__(
        self,
        title: str,
        description: str,
        icon_symbol: str = "♟",
        accent_color: str = "#d7cd64",
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.title_text = title
        self.desc_text = description
        self.icon_symbol = icon_symbol
        self.accent_color = accent_color
        self.scale: float = 1.0
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.update_scale(1.0)

    def update_scale(self, scale: float) -> None:
        """Updates scaling factor and button stylesheet for dynamic window resizing."""
        self.scale = max(0.5, scale)
        self.setFixedHeight(max(42, int(68 * self.scale)))
        self.setMinimumWidth(max(200, int(360 * self.scale)))

        b_radius = max(6, int(10 * self.scale))
        b_pad = int(65 * self.scale)
        b_width = max(1.5, 2.0 * self.scale)

        self.setStyleSheet(f"""
            MenuOptionButton {{
                background-color: #2b2b30;
                border: {b_width:.1f}px solid #44444c;
                border-radius: {b_radius}px;
                text-align: left;
                padding-left: {b_pad}px;
            }}
            MenuOptionButton:hover {{
                background-color: #383842;
                border: {b_width:.1f}px solid {self.accent_color};
            }}
            MenuOptionButton:pressed {{
                background-color: #202024;
                border: {b_width:.1f}px solid #a89f38;
            }}
        """)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Paints button background using stylesheet and draws icon badge, title, and description."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        scale = self.scale
        h = self.height()

        # 1. Draw decorative left icon badge
        badge_size = max(26.0, 42.0 * scale)
        badge_x = 14.0 * scale
        badge_y = (h - badge_size) / 2.0
        badge_rect = QRectF(badge_x, badge_y, badge_size, badge_size)

        painter.setBrush(QBrush(QColor(42, 42, 50)))
        painter.setPen(QPen(QColor(self.accent_color), max(1.0, 1.5 * scale)))
        painter.drawRoundedRect(badge_rect, max(4.0, 8.0 * scale), max(4.0, 8.0 * scale))

        # Draw icon symbol in badge
        painter.setPen(QColor(self.accent_color))
        icon_font = QFont("DejaVu Sans", max(10, int(17 * scale)), QFont.Weight.Bold)
        painter.setFont(icon_font)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, self.icon_symbol)

        # 2. Draw Title Text
        text_x = int(68.0 * scale)
        painter.setPen(QColor(235, 235, 235))
        title_font = QFont("DejaVu Sans", max(8, int(12 * scale)), QFont.Weight.Bold)
        painter.setFont(title_font)
        title_y = int(28.0 * scale)
        painter.drawText(text_x, title_y, self.title_text)

        # 3. Draw Description Text
        painter.setPen(QColor(160, 160, 170))
        desc_font = QFont("DejaVu Sans", max(7, int(9 * scale)))
        painter.setFont(desc_font)
        desc_y = int(48.0 * scale)
        painter.drawText(text_x, desc_y, self.desc_text)


class GenericMenuWidget(QWidget):
    """Modular, reusable generic menu container with customizable header, items, and footer."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.background_color = QColor(24, 24, 28)
        self.grid_square_size = 48
        self.current_scale: float = 1.0

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(14)

        # Container card for menu content
        self.card = QFrame(self)
        self.card.setFixedWidth(500)

        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(24, 20, 24, 20)
        self.card_layout.setSpacing(12)
        self.card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Header area
        self.header_area = QVBoxLayout()
        self.header_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_layout.addLayout(self.header_area)

        # Items area
        self.items_area = QVBoxLayout()
        self.items_area.setSpacing(10)
        self.card_layout.addLayout(self.items_area)

        # Footer area
        self.footer_label = QLabel(self.card)
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.card_layout.addWidget(self.footer_label)

        self.main_layout.addWidget(self.card)
        self._apply_scaling()

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Dynamically scales card, fonts, buttons, and graphics when widget is resized."""
        super().resizeEvent(event)
        self._apply_scaling()

    def _apply_scaling(self) -> None:
        """Calculates scale factor based on dimensions and updates all sub-elements."""
        w = self.width()
        h = self.height()

        # If widget is embedded in a parent/window and hasn't been laid out yet:
        if w <= 100 or h <= 100:
            win = self.window()
            if win and win is not self and win.width() > 100 and win.height() > 100:
                w = win.width()
                h = win.height()

        if w <= 0:
            w = 680
        if h <= 0:
            h = 720

        # Scale relative to baseline 680x720 window
        scale = min(w / 680.0, h / 720.0)
        self.current_scale = max(0.65, min(scale, 2.2))
        s = self.current_scale

        # Scale card
        card_w = max(380, int(min(w * 0.92, 500 * max(0.85, s))))
        self.card.setFixedWidth(card_w)

        card_radius = max(8, int(14 * s))
        card_border = max(1.5, 2.0 * s)
        self.card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(30, 30, 36, 0.94);
                border: {card_border:.1f}px solid #554433;
                border-radius: {card_radius}px;
            }}
        """)

        # Scale padding and spacing
        m_lr = max(12, int(24 * s))
        m_tb = max(10, int(20 * s))
        self.card_layout.setContentsMargins(m_lr, m_tb, m_lr, m_tb)
        self.card_layout.setSpacing(max(6, int(12 * s)))
        self.items_area.setSpacing(max(5, int(10 * s)))

        # Scale footer
        footer_size = max(8, int(11 * s))
        self.footer_label.setStyleSheet(f"color: #777788; font-size: {footer_size}px; font-style: italic;")

        # Scale checkered background
        self.grid_square_size = max(24, int(48 * s))

        # Scale header widget if it supports scaling
        for i in range(self.header_area.count()):
            item = self.header_area.itemAt(i)
            widget = item.widget()
            if widget and hasattr(widget, "update_scale"):
                widget.update_scale(s)

        # Scale all menu items in items_area
        for i in range(self.items_area.count()):
            item = self.items_area.itemAt(i)
            btn = item.widget()
            if btn and hasattr(btn, "update_scale"):
                btn.update_scale(s)

        self.update()

    def set_header_widget(self, widget: QWidget) -> None:
        """Sets or replaces the header widget in the menu card."""
        while self.header_area.count():
            item = self.header_area.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.header_area.addWidget(widget)
        if hasattr(widget, "update_scale"):
            widget.update_scale(self.current_scale)

    def add_menu_item(
        self,
        title: str,
        description: str,
        on_click: Callable[[], None],
        icon_symbol: str = "♟",
        accent_color: str = "#d7cd64",
    ) -> MenuOptionButton:
        """Adds a new option button card to the menu items list."""
        btn = MenuOptionButton(title, description, icon_symbol, accent_color, self.card)
        btn.clicked.connect(on_click)
        btn.update_scale(self.current_scale)
        self.items_area.addWidget(btn)
        return btn

    def set_footer_text(self, text: str) -> None:
        """Sets footer text at the bottom of the menu."""
        self.footer_label.setText(text)

    def paintEvent(self, event: QPaintEvent) -> None:
        """Renders subtle dark checkered background pattern with radial vignette."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        w = self.width()
        h = self.height()

        # Fill base background
        painter.fillRect(0, 0, w, h, self.background_color)

        # Subtle checkered grid pattern
        sq = self.grid_square_size
        cols = (w // sq) + 2
        rows = (h // sq) + 2
        c_alt = QColor(32, 32, 38)
        for r in range(rows):
            for c in range(cols):
                if (r + c) % 2 == 0:
                    painter.fillRect(c * sq, r * sq, sq, sq, c_alt)

        # Soft radial gradient vignette overlay
        vignette = QRadialGradient(w / 2.0, h / 2.0, max(w, h) * 0.7)
        vignette.setColorAt(0.0, QColor(0, 0, 0, 40))
        vignette.setColorAt(0.7, QColor(0, 0, 0, 160))
        vignette.setColorAt(1.0, QColor(0, 0, 0, 220))
        painter.fillRect(0, 0, w, h, vignette)


class MainMenuWidget(GenericMenuWidget):
    """Main Menu screen with game mode selection, tutorial, credits, and exit options."""

    # Signals emitted when user chooses an action
    turn_based_selected = pyqtSignal()
    free_move_selected = pyqtSignal()
    tutorial_selected = pyqtSignal()
    credits_selected = pyqtSignal()
    exit_selected = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        # Add heraldic procedural chess crest header
        self.crest = ChessCrestWidget(self.card)
        self.set_header_widget(self.crest)

        # Add menu items
        self.add_menu_item(
            title="Turn-Based Mode",
            description="Classic chess rules, check & checkmate",
            on_click=self.turn_based_selected.emit,
            icon_symbol="⚔",
            accent_color="#d7cd64",
        )

        self.add_menu_item(
            title="Free Move Mode",
            description="Sandbox mode: move any piece freely anytime",
            on_click=self.free_move_selected.emit,
            icon_symbol="⚡",
            accent_color="#5cbbf6",
        )

        self.add_menu_item(
            title="How to Play",
            description="Rules, piece moves, special tactics & controls",
            on_click=self.tutorial_selected.emit,
            icon_symbol="♟",
            accent_color="#63e6be",
        )

        self.add_menu_item(
            title="Credits",
            description="Alef-0, Gemini AI, PyQt6 framework & assets",
            on_click=self.credits_selected.emit,
            icon_symbol="★",
            accent_color="#f08c00",
        )

        self.set_footer_text("Chess Qt v0.1.0 • Built with Python & Qt")


class TutorialDialog(QDialog):
    """Comprehensive multi-tab tutorial dialog explaining rules, piece movements, and game modes."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Chess Tutorial - How to Play")
        self.resize(700, 580)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog {
                background-color: #222226;
                color: #e6e6e6;
            }
            QTabWidget::pane {
                border: 2px solid #44444c;
                background-color: #28282e;
                border-radius: 8px;
                padding: 12px;
            }
            QTabBar::tab {
                background-color: #1e1e22;
                color: #b0b0b8;
                border: 1px solid #3c3c44;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                font-size: 12px;
                margin-right: 4px;
            }
            QTabBar::tab:selected {
                background-color: #28282e;
                color: #d7cd64;
                border-color: #44444c;
            }
            QLabel {
                color: #e0e0e8;
                font-size: 12px;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QPushButton {
                background-color: #383842;
                color: #f0f0f0;
                border: 1px solid #555560;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4c4c58;
                border-color: #d7cd64;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # Dialog Title Header
        title_label = QLabel("CHESS GUIDE & TUTORIAL")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #d7cd64; letter-spacing: 2px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Tab Widget
        tabs = QTabWidget(self)
        tabs.addTab(self._create_pieces_tab(), "♟ Piece Moves")
        tabs.addTab(self._create_special_moves_tab(), "⚡ Special Rules")
        tabs.addTab(self._create_modes_tab(), "⚔ Game Modes")
        tabs.addTab(self._create_controls_tab(), "✦ Controls")
        layout.addWidget(tabs)

        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Got It, Let's Play!")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _create_pieces_tab(self) -> QWidget:
        """Builds the tab showing each chess piece, sprite, and movement mechanics."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setSpacing(12)

        pieces_info = [
            (
                PieceType.KING,
                "King",
                "Moves 1 square in any direction (horizontal, vertical, or diagonal). "
                "Must never move into check or remain in check.",
            ),
            (
                PieceType.QUEEN,
                "Queen",
                "Moves any number of unoccupied squares in any direction: horizontally, vertically, or diagonally.",
            ),
            (
                PieceType.ROOK,
                "Rook",
                "Moves any number of unoccupied squares horizontally or vertically along ranks and files.",
            ),
            (
                PieceType.BISHOP,
                "Bishop",
                "Moves any number of unoccupied squares diagonally. Always stays on squares of its starting color.",
            ),
            (
                PieceType.KNIGHT,
                "Knight",
                "Moves in an 'L-shape' (2 squares in one cardinal direction, then 1 square perpendicular). "
                "The only piece that can jump over other pieces!",
            ),
            (
                PieceType.PAWN,
                "Pawn",
                "Moves forward 1 square (or 2 squares on its very first move). Captures diagonally forward 1 square. "
                "Subject to en passant capture and pawn promotion upon reaching the opposing back rank.",
            ),
        ]

        for p_type, name, desc in pieces_info:
            card = QFrame()
            card.setStyleSheet("background-color: #303038; border-radius: 8px; padding: 6px;")
            h_card = QHBoxLayout(card)
            h_card.setContentsMargins(8, 6, 8, 6)

            # Piece sprite
            sprite_label = QLabel()
            sprite_label.setFixedSize(50, 50)
            try:
                pix = get_master_piece_pixmap(PieceColor.WHITE, p_type).scaled(
                    46, 46, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
                sprite_label.setPixmap(pix)
            except Exception:
                sprite_label.setText(name[0])
            h_card.addWidget(sprite_label)

            # Piece text
            t_vbox = QVBoxLayout()
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #d7cd64;")
            desc_lbl = QLabel(desc)
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet("color: #d0d0d8; font-size: 11px;")
            t_vbox.addWidget(name_lbl)
            t_vbox.addWidget(desc_lbl)
            h_card.addLayout(t_vbox)

            vbox.addWidget(card)

        scroll.setWidget(container)
        return scroll

    def _create_special_moves_tab(self) -> QWidget:
        """Builds tab explaining Castling, En Passant, and Promotion."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setSpacing(14)

        rules = [
            (
                "🏰 Castling (Kingside & Queenside)",
                "A special move involving King and Rook:\n"
                "• The King moves 2 squares towards a Rook, and that Rook jumps to the square the King just crossed.\n"
                "• Requirements: Neither King nor Rook has moved yet; no pieces between them; King is not in check "
                "and does not pass through or land on an attacked square.\n"
                "• Visual indicator: Denoted on the board with an anti-aliased directional arrow!",
            ),
            (
                "⚔ En Passant ('In Passing')",
                "A unique pawn capture rule:\n"
                "• If an opponent's pawn moves 2 squares forward from its starting position and lands directly "
                "adjacent to your pawn, your pawn can capture it diagonally on the very next turn as if it had only moved 1 square.\n"
                "• Visual indicator: Denoted on the board with an anti-aliased directional arrow!",
            ),
            (
                "👑 Pawn Promotion",
                "When a pawn successfully marches across the board to the opposing 8th rank:\n"
                "• An interactive popup instantly lets you transform the pawn into a Queen, Rook, Bishop, or Knight.\n"
                "• In Turn-Based mode, Queen is selected by default unless chosen otherwise.\n"
                "• In Free Move mode, promotion choice is directly evaluated against mate conditions!",
            ),
        ]

        for title, text in rules:
            card = QFrame()
            card.setStyleSheet("background-color: #303038; border-radius: 8px; padding: 10px;")
            c_vbox = QVBoxLayout(card)
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #63e6be;")
            txt_lbl = QLabel(text)
            txt_lbl.setWordWrap(True)
            txt_lbl.setStyleSheet("color: #d8d8e0; font-size: 12px; line-height: 1.4;")
            c_vbox.addWidget(t_lbl)
            c_vbox.addWidget(txt_lbl)
            vbox.addWidget(card)

        scroll.setWidget(container)
        return scroll

    def _create_modes_tab(self) -> QWidget:
        """Builds tab explaining Turn-Based vs Free Move mode."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setSpacing(14)

        modes = [
            (
                "⚔ Turn-Based Mode (Standard Rules)",
                "• White moves first, then Black, strictly alternating turns.\n"
                "• Pieces can only make fully legal chess moves: you cannot make a move that leaves your King in check.\n"
                "• If a King is attacked, it is in Check and highlighted in luminous red on the board.\n"
                "• If a player has no legal moves to escape check, it is CHECKMATE! The winning player is declared "
                "and the main menu automatically re-opens.",
                "#d7cd64",
            ),
            (
                "⚡ Free Move Mode (Sandbox / Analysis)",
                "• Full freedom: turn enforcement is disabled!\n"
                "• Move any White or Black piece at any time according to standard piece mechanics.\n"
                "• Great for practicing openings, setting up tactics, teaching endgame scenarios, or exploring board puzzles.\n"
                "• If a move produces a mate condition, an interactive confirmation dialog asks if you want to end the game, "
                "declaring the victor and re-opening the menu.",
                "#5cbbf6",
            ),
        ]

        for title, text, color in modes:
            card = QFrame()
            card.setStyleSheet("background-color: #303038; border-radius: 8px; padding: 10px;")
            c_vbox = QVBoxLayout(card)
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
            txt_lbl = QLabel(text)
            txt_lbl.setWordWrap(True)
            txt_lbl.setStyleSheet("color: #d8d8e0; font-size: 12px; line-height: 1.4;")
            c_vbox.addWidget(t_lbl)
            c_vbox.addWidget(txt_lbl)
            vbox.addWidget(card)

        scroll.setWidget(container)
        return scroll

    def _create_controls_tab(self) -> QWidget:
        """Builds tab explaining mouse controls and board visual indicators."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setSpacing(14)

        controls = [
            ("Left Click", "Select a piece of your turn, or select a valid destination square to execute a move."),
            ("Right Click / Click Outside", "Cancel piece selection and clear highlighted move indicators."),
            ("Solid Gray Dots", "Indicate an empty square reachable by the currently selected piece."),
            ("Target Ring with Dot", "Indicates an enemy piece that can be captured on that square."),
            ("Directional Arrows", "Denotes special multi-piece moves (Castling or En Passant)."),
            ("Red Highlighted Square", "Alerts that the King residing on that square is in Check!"),
            ("Top Bar Menu Button", "Click 'Menu' at any time during a match to pause and return to the main menu."),
        ]

        for key, desc in controls:
            card = QFrame()
            card.setStyleSheet("background-color: #303038; border-radius: 8px; padding: 8px;")
            h_card = QHBoxLayout(card)
            k_lbl = QLabel(key)
            k_lbl.setFixedWidth(180)
            k_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #63e6be;")
            d_lbl = QLabel(desc)
            d_lbl.setWordWrap(True)
            d_lbl.setStyleSheet("color: #d8d8e0; font-size: 11px;")
            h_card.addWidget(k_lbl)
            h_card.addWidget(d_lbl)
            vbox.addWidget(card)

        scroll.setWidget(container)
        return scroll


class CreditsDialog(QDialog):
    """Credits dialog highlighting Alef-0, Google Gemini AI, PyQt6, and technology stack."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About & Credits - Chess Qt")
        self.resize(480, 420)
        self.setModal(True)

        self.setStyleSheet("""
            QDialog {
                background-color: #222226;
                color: #e6e6e6;
            }
            QLabel {
                color: #e0e0e8;
            }
            QPushButton {
                background-color: #383842;
                color: #f0f0f0;
                border: 1px solid #555560;
                border-radius: 6px;
                padding: 8px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4c4c58;
                border-color: #d7cd64;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Mini Crest
        crest = ChessCrestWidget(self)
        crest.setFixedHeight(120)
        layout.addWidget(crest)

        # Credits Card Frame
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #2a2a30;
                border: 2px solid #554433;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(10)

        items = [
            ("Created By", "Alef-0"),
            ("AI Pair Programmer", "Google Gemini"),
            ("GUI Framework", "PyQt6 (Qt 6) & Python 3"),
            ("Graphics & Sprites", "High-Res Spritesheet & Procedural QPainter Vector Art"),
            ("Architecture", "Event-driven Qt with Complete Chess Rule Engine"),
        ]

        for role, val in items:
            row = QHBoxLayout()
            r_lbl = QLabel(role + ":")
            r_lbl.setStyleSheet("font-weight: bold; color: #d7cd64; font-size: 12px;")
            r_lbl.setFixedWidth(160)
            v_lbl = QLabel(val)
            v_lbl.setStyleSheet("color: #f0f0f5; font-size: 12px;")
            row.addWidget(r_lbl)
            row.addWidget(v_lbl)
            card_layout.addLayout(row)

        layout.addWidget(card)

        note_lbl = QLabel("Thank you for playing Chess Qt!")
        note_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note_lbl.setStyleSheet("color: #9999aa; font-style: italic; font-size: 11px;")
        layout.addWidget(note_lbl)

        # Close Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
