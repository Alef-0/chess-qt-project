"""Tests for Menu, procedural graphics, tutorial, credits, and navigation flow."""

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPaintEvent, QRegion
from PyQt6.QtWidgets import QMessageBox

from board import ChessBoardWidget, ChessWindow
from menu import (
    ChessCrestWidget,
    CreditsDialog,
    GenericMenuWidget,
    MainMenuWidget,
    MenuOptionButton,
    TutorialDialog,
)
from pieces import PieceColor, PieceType


class TestMenuWidgets:
    """Test individual menu components and custom graphics."""

    def test_chess_crest_widget(self, qapp):
        """Verify the procedural chess crest widget renders without errors."""
        crest = ChessCrestWidget()
        assert crest.height() == 170
        assert crest.minimumWidth() == 360
        # Trigger paint event
        event = QPaintEvent(QRegion(0, 0, crest.width(), crest.height()))
        crest.paintEvent(event)

    def test_menu_option_button(self, qapp):
        """Verify custom menu option button structure and rendering."""
        clicked = []
        btn = MenuOptionButton(
            title="Test Mode",
            description="Test description text",
            icon_symbol="⚡",
            accent_color="#5cbbf6",
        )
        btn.clicked.connect(lambda: clicked.append(True))
        btn.click()
        assert clicked == [True]

        # Trigger paint event
        event = QPaintEvent(QRegion(0, 0, btn.width(), btn.height()))
        btn.paintEvent(event)

    def test_generic_menu_widget(self, qapp):
        """Verify generic menu container can add items, headers, and footers."""
        menu = GenericMenuWidget()
        actions = []
        btn = menu.add_menu_item("Action 1", "Does action 1", lambda: actions.append(1))
        menu.set_footer_text("Test Footer")
        assert menu.footer_label.text() == "Test Footer"

        btn.click()
        assert actions == [1]

        # Trigger paint event (checkered background + vignette)
        menu.resize(600, 600)
        event = QPaintEvent(QRegion(0, 0, 600, 600))
        menu.paintEvent(event)

    def test_main_menu_widget_signals(self, qapp):
        """Verify MainMenuWidget emits proper signals on option selections."""
        main_menu = MainMenuWidget()

        signals_received = []
        main_menu.turn_based_selected.connect(lambda: signals_received.append("turn_based"))
        main_menu.free_move_selected.connect(lambda: signals_received.append("free_move"))
        main_menu.tutorial_selected.connect(lambda: signals_received.append("tutorial"))
        main_menu.credits_selected.connect(lambda: signals_received.append("credits"))

        # Find buttons in main menu items_area
        buttons = [
            main_menu.items_area.itemAt(i).widget()
            for i in range(main_menu.items_area.count())
            if isinstance(main_menu.items_area.itemAt(i).widget(), MenuOptionButton)
        ]
        assert len(buttons) == 4

        # Click Turn-Based button
        buttons[0].click()
        assert signals_received[-1] == "turn_based"

        # Click Free Move button
        buttons[1].click()
        assert signals_received[-1] == "free_move"

        # Click Tutorial button
        buttons[2].click()
        assert signals_received[-1] == "tutorial"

        # Click Credits button
        buttons[3].click()
        assert signals_received[-1] == "credits"


class TestTutorialAndCredits:
    """Test tutorial and credits dialogs."""

    def test_tutorial_dialog_tabs(self, qapp):
        """Verify tutorial dialog loads all instructional tabs and piece cards."""
        dialog = TutorialDialog()
        assert dialog.windowTitle() == "Chess Tutorial - How to Play"
        # Find QTabWidget
        from PyQt6.QtWidgets import QTabWidget

        tabs = dialog.findChild(QTabWidget)
        assert tabs is not None
        assert tabs.count() == 4
        assert "Piece Moves" in tabs.tabText(0)
        assert "Special Rules" in tabs.tabText(1)
        assert "Game Modes" in tabs.tabText(2)
        assert "Controls" in tabs.tabText(3)

    def test_credits_dialog(self, qapp):
        """Verify credits dialog mentions Alef-0, Gemini, and PyQt6."""
        dialog = CreditsDialog()
        assert dialog.windowTitle() == "About & Credits - Chess Qt"
        # Find all labels to verify credits text
        from PyQt6.QtWidgets import QLabel

        labels = dialog.findChildren(QLabel)
        texts = " ".join(lbl.text() for lbl in labels)
        assert "Alef-0" in texts
        assert "Gemini" in texts
        assert "PyQt6" in texts or "Qt" in texts


class TestChessWindowNavigation:
    """Test screen switching, in-game controls, and game over menu loop."""

    def test_default_start_in_menu(self, qapp):
        """Verify ChessWindow starts in menu screen by default."""
        window = ChessWindow(free_move=False, start_in_menu=True)
        assert window.stack.currentWidget() == window.menu_widget

    def test_start_turn_based_game(self, qapp):
        """Verify selecting turn-based mode transitions to board with turn rules active."""
        window = ChessWindow(start_in_menu=True)
        window.start_game(free_move=False)

        assert window.stack.currentWidget() == window.game_container
        assert window.board_widget.turn_enabled is True
        assert window.board_widget.current_turn == PieceColor.WHITE
        assert "Turn-Based Mode" in window.status_label.text()

    def test_start_free_move_game(self, qapp):
        """Verify selecting free-move mode transitions to board with free movement active."""
        window = ChessWindow(start_in_menu=True)
        window.start_game(free_move=True)

        assert window.stack.currentWidget() == window.game_container
        assert window.board_widget.turn_enabled is False
        assert "Free Move Mode" in window.status_label.text()

    def test_menu_button_returns_to_menu(self, qapp):
        """Verify clicking the in-game Menu button returns to main menu."""
        window = ChessWindow(start_in_menu=True)
        window.start_game(free_move=False)
        assert window.stack.currentWidget() == window.game_container

        window.menu_btn.click()
        assert window.stack.currentWidget() == window.menu_widget

    def test_restart_game(self, qapp):
        """Verify in-game restart button resets pieces and active turn."""
        window = ChessWindow(start_in_menu=True)
        window.start_game(free_move=False)

        # Move e2 to e4
        window.board_widget.handle_square_clicked(6, 4)  # e2
        window.board_widget.handle_square_clicked(4, 4)  # e4
        assert window.board_widget.current_turn == PieceColor.BLACK

        # Click restart
        window.restart_btn.click()
        assert window.board_widget.current_turn == PieceColor.WHITE
        assert window.board_widget.pieces.get_piece(6, 4) is not None

    def test_game_over_reopens_menu(self, qapp):
        """Verify when game_over_signal is emitted, the main menu is reopened."""
        window = ChessWindow(start_in_menu=True)
        window.start_game(free_move=False)
        assert window.stack.currentWidget() == window.game_container

        # Simulate game over event
        window.board_widget.game_over_signal.emit("WHITE")
        # Should switch back to menu screen
        assert window.stack.currentWidget() == window.menu_widget

    def test_board_widget_reset_game(self, qapp):
        """Verify ChessBoardWidget.reset_game resets state properly."""
        widget = ChessBoardWidget(free_move=False)
        widget.handle_square_clicked(6, 4)
        widget.handle_square_clicked(4, 4)
        assert widget.current_turn == PieceColor.BLACK

        widget.reset_game(free_move=True)
        assert widget.current_turn == PieceColor.WHITE
        assert widget.turn_enabled is False
        assert widget.selected_square is None
        assert widget.valid_moves == []
        assert widget.game_over is False

    def test_menu_screen_and_fonts_scale_with_window_size(self, qapp):
        """Verify menu card, buttons, crest, and fonts dynamically scale with window resizing."""
        window = ChessWindow(start_in_menu=True)
        window.show()
        qapp.processEvents()

        # 1. Baseline medium size
        window.resize(680, 720)
        qapp.processEvents()
        scale_medium = window.menu_widget.current_scale
        card_w_medium = window.menu_widget.card.width()
        crest_h_medium = window.menu_widget.crest.height()
        btn = window.menu_widget.items_area.itemAt(0).widget()
        btn_h_medium = btn.height()
        assert scale_medium == pytest.approx(1.0, 0.05)

        # 2. Large window size
        window.resize(1020, 1080)
        qapp.processEvents()
        scale_large = window.menu_widget.current_scale
        assert scale_large > scale_medium
        assert window.menu_widget.card.width() > card_w_medium
        assert window.menu_widget.crest.height() > crest_h_medium
        assert btn.height() > btn_h_medium

        # 3. Small window size
        window.resize(500, 520)
        qapp.processEvents()
        scale_small = window.menu_widget.current_scale
        assert scale_small < scale_medium
        assert window.menu_widget.card.width() < card_w_medium
        assert window.menu_widget.crest.height() < crest_h_medium
        assert btn.height() < btn_h_medium

