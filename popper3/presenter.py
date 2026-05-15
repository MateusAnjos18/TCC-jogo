from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QAbstractItemView,
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from popper3.app import CardPreview, ICON_RELATIVE_PATH, resource_path
from popper3.db import Card, Database


MAX_SELECTED_CARDS = 8


class FullscreenCardsDialog(QDialog):
    def __init__(self, cards: list[Card], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Cartas selecionadas")
        self.setWindowIcon(QIcon(str(resource_path(ICON_RELATIVE_PATH))))
        self.setStyleSheet("background: #030914;")

        grid = QGridLayout()
        grid.setContentsMargins(28, 28, 28, 28)
        grid.setSpacing(18)

        for index, card in enumerate(cards):
            preview = CardPreview()
            preview.setMinimumSize(220, 310)
            preview.set_data(card.card_type, card.title, card.description, card.score, card.splash_path)
            row = index // 4
            col = index % 4
            grid.addWidget(preview, row, col)

        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.close)

        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(close_btn)

        layout = QVBoxLayout(self)
        layout.addLayout(grid, 1)
        layout.addLayout(actions)

    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key_Escape:
            self.close()
            return
        super().keyPressEvent(event)


class PresenterWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.db = Database()
        self.cards_by_id: dict[int, Card] = {}
        self.setWindowTitle("Popper 3 - Apresentador")
        self.setWindowIcon(QIcon(str(resource_path(ICON_RELATIVE_PATH))))
        self.resize(980, 680)

        self.deck_input = QComboBox()
        self.deck_input.currentIndexChanged.connect(self.refresh_cards)

        self.cards_list = QListWidget()
        self.cards_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.cards_list.itemSelectionChanged.connect(self.limit_selection)

        self.counter_label = QLabel(f"0/{MAX_SELECTED_CARDS} cartas selecionadas")
        self.counter_label.setObjectName("Counter")

        show_btn = QPushButton("Abrir em tela cheia")
        show_btn.clicked.connect(self.open_fullscreen)

        top = QHBoxLayout()
        top.addWidget(QLabel("Baralho"))
        top.addWidget(self.deck_input, 1)

        actions = QHBoxLayout()
        actions.addWidget(self.counter_label)
        actions.addStretch()
        actions.addWidget(show_btn)

        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addLayout(top)
        layout.addWidget(QLabel("Selecione ate 8 cartas"))
        layout.addWidget(self.cards_list, 1)
        layout.addLayout(actions)
        self.setCentralWidget(root)
        self._style()
        self.refresh_decks()

    def _style(self) -> None:
        self.setStyleSheet(
            """
            QWidget { font-family: "Segoe UI Variable", "Segoe UI"; font-size: 11pt; color: #F7EBC8; }
            QMainWindow, QWidget { background: #06101F; }
            QLabel#Counter { color: #F4C46A; font-weight: 700; }
            QComboBox {
                background: #071326; color: #F7EBC8; border: 1px solid #D99A3A; border-radius: 8px; padding: 8px;
            }
            QListWidget {
                background: #071326; color: #F7EBC8; border: 1px solid #D99A3A; border-radius: 10px;
                padding: 8px; outline: 0;
            }
            QListWidget::item { padding: 10px; border-bottom: 1px solid rgba(217, 154, 58, 80); }
            QListWidget::item:selected { color: #06101F; background: #F4C46A; }
            QPushButton {
                background: #2A5BDB; color: white; border: 1px solid rgba(244, 196, 106, 120); border-radius: 8px;
                padding: 10px 16px; font-weight: 700;
            }
            QPushButton:hover { background: #3478FF; }
            """
        )

    def refresh_decks(self) -> None:
        self.deck_input.clear()
        for deck in self.db.decks():
            self.deck_input.addItem(deck.name, deck.id)
        self.refresh_cards()

    def refresh_cards(self) -> None:
        self.cards_list.clear()
        self.cards_by_id.clear()
        deck_id = self.deck_input.currentData()
        if deck_id is None:
            self.update_counter()
            return
        for card in self.db.cards(int(deck_id)):
            kind = "Jogo" if card.card_type == "game" else "Jogador"
            score = f" | {card.score} pts" if card.card_type == "game" else ""
            truth = " | verdadeira" if card.truth else " | falsa" if card.card_type == "game" else ""
            item = QListWidgetItem(f"{kind}: {card.title}{score}{truth}")
            item.setData(Qt.UserRole, card.id)
            self.cards_by_id[card.id] = card
            self.cards_list.addItem(item)
        self.update_counter()

    def selected_cards(self) -> list[Card]:
        cards: list[Card] = []
        for item in self.cards_list.selectedItems():
            card_id = int(item.data(Qt.UserRole))
            card = self.cards_by_id.get(card_id)
            if card:
                cards.append(card)
        return cards

    def limit_selection(self) -> None:
        selected = self.cards_list.selectedItems()
        if len(selected) > MAX_SELECTED_CARDS:
            selected[-1].setSelected(False)
            QMessageBox.warning(self, "Limite de cartas", "Selecione no maximo 8 cartas.")
        self.update_counter()

    def update_counter(self) -> None:
        self.counter_label.setText(f"{len(self.cards_list.selectedItems())}/{MAX_SELECTED_CARDS} cartas selecionadas")

    def open_fullscreen(self) -> None:
        cards = self.selected_cards()
        if not cards:
            QMessageBox.warning(self, "Cartas", "Selecione ao menos uma carta.")
            return
        dialog = FullscreenCardsDialog(cards, self)
        dialog.showFullScreen()
        dialog.exec()

    def closeEvent(self, event) -> None:  # noqa: N802
        self.db.close()
        super().closeEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(resource_path(ICON_RELATIVE_PATH))))
    window = PresenterWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
