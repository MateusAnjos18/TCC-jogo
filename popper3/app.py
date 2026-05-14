from __future__ import annotations

import sys
import uuid
from pathlib import Path

from PySide6.QtCore import Qt, QPointF, QRectF, QSize
from PIL import Image, ImageOps
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from popper3.db import Card, DATA_DIR, Database, Deck
from popper3.excel_io import create_template, read_game_cards
from popper3.pdf_export import export_cards_pdf, export_report_pdf


IMAGE_FILTER = "Imagens (*.png *.jpg *.jpeg *.svg)"
LOGO_RELATIVE_PATH = Path("popper3") / "assets" / "popper3_logo.png"
ICON_RELATIVE_PATH = Path("popper3") / "assets" / "popper3.ico"
MAX_TITLE_CHARS = 32
MAX_GAME_DESCRIPTION_CHARS = 180
MAX_PLAYER_DESCRIPTION_CHARS = 120
RECOMMENDED_SPLASH_SIZE = QSize(1000, 1000)
SPLASH_DIR = DATA_DIR / "splash_art"


def resource_path(relative_path: Path) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / relative_path


def image_pixmap(path: str | None, size: QSize) -> QPixmap:
    if not path or not Path(path).exists():
        return QPixmap()
    if Path(path).suffix.lower() == ".svg":
        renderer = QSvgRenderer(path)
        if not renderer.isValid():
            return QPixmap()
        image = QImage(size, QImage.Format_ARGB32)
        image.fill(Qt.transparent)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        return QPixmap.fromImage(image)
    pixmap = QPixmap(path)
    if pixmap.isNull():
        return pixmap
    return pixmap.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)


def deck_cover_icon(deck: Deck, size: QSize) -> QIcon:
    pixmap = image_pixmap(deck.cover_path, size)
    canvas = QPixmap(size)
    canvas.fill(Qt.transparent)
    painter = QPainter(canvas)
    painter.setRenderHint(QPainter.Antialiasing)
    rect = QRectF(0, 0, size.width(), size.height())
    painter.setPen(Qt.NoPen)
    if pixmap.isNull():
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor("#F9D44A"))
        gradient.setColorAt(0.52, QColor("#44BBA4"))
        gradient.setColorAt(1, QColor("#2F80ED"))
        painter.setBrush(gradient)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 14, 14)
        painter.setBrush(QColor(255, 255, 255, 205))
        painter.drawEllipse(QRectF(size.width() * 0.16, size.height() * 0.16, 44, 44))
        painter.drawRoundedRect(QRectF(size.width() * 0.35, size.height() * 0.55, 82, 16), 8, 8)
        painter.setPen(QColor("#17324D"))
        font = QFont("Segoe UI Variable", 20)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, deck.name[:2].upper())
    else:
        scaled = pixmap.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        x = (size.width() - scaled.width()) / 2
        y = (size.height() - scaled.height()) / 2
        painter.setClipRect(rect.adjusted(1, 1, -1, -1))
        painter.drawPixmap(int(x), int(y), scaled)
        painter.setClipping(False)
        shade = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        shade.setColorAt(0, QColor(0, 0, 0, 20))
        shade.setColorAt(1, QColor(0, 0, 0, 95))
        painter.setBrush(shade)
        painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 14, 14)
    painter.setPen(QColor("#FFFFFF"))
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 14, 14)
    painter.end()
    return QIcon(canvas)


def normalized_splash_path(path: str) -> str:
    image_path = Path(path)
    if image_path.suffix.lower() == ".svg":
        return path
    if not image_path.exists():
        raise ValueError("A imagem selecionada nao foi encontrada.")

    with Image.open(image_path) as image:
        image = ImageOps.exif_transpose(image)
        if image.size == (RECOMMENDED_SPLASH_SIZE.width(), RECOMMENDED_SPLASH_SIZE.height()):
            return path

        image = image.convert("RGBA")
        fitted = ImageOps.contain(
            image,
            (RECOMMENDED_SPLASH_SIZE.width(), RECOMMENDED_SPLASH_SIZE.height()),
            Image.Resampling.LANCZOS,
        )
        canvas = Image.new(
            "RGBA",
            (RECOMMENDED_SPLASH_SIZE.width(), RECOMMENDED_SPLASH_SIZE.height()),
            (255, 255, 255, 0),
        )
        x = (canvas.width - fitted.width) // 2
        y = (canvas.height - fitted.height) // 2
        canvas.alpha_composite(fitted, (x, y))

        SPLASH_DIR.mkdir(parents=True, exist_ok=True)
        safe_stem = image_path.stem[:48] or "splash"
        output_path = SPLASH_DIR / f"{safe_stem}-{uuid.uuid4().hex[:8]}.png"
        canvas.save(output_path, "PNG")
        return str(output_path)


class EduPage(QWidget):
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0, QColor("#1F1738"))
        gradient.setColorAt(0.46, QColor("#17365A"))
        gradient.setColorAt(1, QColor("#0F2947"))
        painter.fillRect(self.rect(), gradient)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(62, 210, 245, 44))
        painter.drawEllipse(QRectF(self.width() - 300, 52, 210, 210))
        painter.setBrush(QColor(247, 197, 75, 44))
        painter.drawEllipse(QRectF(40, self.height() - 188, 168, 168))
        painter.setBrush(QColor(142, 86, 255, 38))
        painter.drawRoundedRect(QRectF(self.width() * 0.58, self.height() - 104, 310, 58), 18, 18)
        logo = QPixmap(str(resource_path(LOGO_RELATIVE_PATH)))
        if not logo.isNull():
            scaled = logo.scaled(QSize(300, 300), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            painter.setOpacity(0.13)
            painter.drawPixmap(self.width() - scaled.width() - 28, self.height() - scaled.height() - 22, scaled)
            painter.setOpacity(1.0)


class BrandHeader(QWidget):
    def __init__(self, title: str, subtitle: str | None = None, compact: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        logo = QLabel()
        logo.setObjectName("BrandLogo")
        logo_size = QSize(78, 78) if not compact else QSize(48, 48)
        pixmap = QPixmap(str(resource_path(LOGO_RELATIVE_PATH)))
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaled(logo_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setFixedSize(logo_size)
        title_label = QLabel(title)
        title_label.setObjectName("PageTitle")
        text = QVBoxLayout()
        text.setContentsMargins(0, 0, 0, 0)
        text.setSpacing(1)
        text.addWidget(title_label)
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("Subtitle")
            text.addWidget(subtitle_label)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(14)
        row.addWidget(logo)
        row.addLayout(text)
        row.addStretch()


class StatCard(QFrame):
    def __init__(self, label: str, accent: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("StatCard")
        self.value_label = QLabel("0")
        self.value_label.setObjectName("StatValue")
        self.label = QLabel(label)
        self.label.setObjectName("StatLabel")
        self.accent = QFrame()
        self.accent.setFixedWidth(5)
        self.accent.setStyleSheet(f"background: {accent}; border-radius: 2px;")
        text = QVBoxLayout()
        text.setContentsMargins(10, 8, 10, 8)
        text.setSpacing(0)
        text.addWidget(self.value_label)
        text.addWidget(self.label)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.accent)
        layout.addLayout(text)

    def set_value(self, value: int) -> None:
        self.value_label.setText(str(value))


class CardPreview(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.card_type = "game"
        self.title = "Titulo da carta"
        self.description = "Descricao da carta"
        self.score = 0
        self.splash_path: str | None = None
        self.setMinimumSize(230, 320)

    def set_data(
        self,
        card_type: str,
        title: str,
        description: str,
        score: int | None,
        splash_path: str | None,
    ) -> None:
        self.card_type = card_type
        self.title = title or "Titulo da carta"
        self.description = description or "Descricao da carta"
        self.score = score or 0
        self.splash_path = splash_path
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(8, 8, self.width() - 16, self.height() - 16)
        if self.card_type == "game":
            self._paint_game(painter, rect)
        else:
            self._paint_player(painter, rect)

    def _paint_game(self, painter: QPainter, rect: QRectF) -> None:
        self._frame(painter, rect)
        title_rect = QRectF(rect.left() + 14, rect.top() + 14, rect.width() - 28, 32)
        self._panel(painter, title_rect)
        self._text(painter, title_rect.adjusted(6, 0, -6, 0), self.title, 11, QColor("#F7EBC8"), True, Qt.AlignCenter)
        art_rect = QRectF(rect.left() + 18, rect.top() + 58, rect.width() - 36, rect.height() * 0.42)
        self._art(painter, art_rect)
        desc_rect = QRectF(rect.left() + 18, rect.bottom() - 118, rect.width() - 36, 86)
        self._panel(painter, desc_rect)
        self._text(painter, desc_rect.adjusted(10, 8, -10, -8), self.description, 9, QColor("#F7EBC8"), False, Qt.AlignTop | Qt.TextWordWrap)
        score_rect = QRectF(rect.right() - 50, rect.bottom() - 48, 36, 36)
        painter.setPen(QPen(QColor("#F4C46A"), 2))
        painter.setBrush(QColor("#E23D28"))
        painter.drawEllipse(score_rect)
        painter.setPen(QPen(QColor("#7C1F20"), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(score_rect.adjusted(5, 5, -5, -5))
        self._text(painter, score_rect, str(self.score), 13, QColor("white"), True, Qt.AlignCenter)

    def _paint_player(self, painter: QPainter, rect: QRectF) -> None:
        self._frame(painter, rect)
        art_rect = QRectF(rect.left() + 16, rect.top() + 22, rect.width() - 32, rect.height() * 0.56)
        self._art(painter, art_rect)
        title_rect = QRectF(rect.left() + 24, art_rect.bottom() + 10, rect.width() - 48, 34)
        self._panel(painter, title_rect)
        self._text(painter, title_rect.adjusted(6, 0, -6, 0), self.title, 12, QColor("#F7EBC8"), True, Qt.AlignCenter)
        desc_rect = QRectF(rect.left() + 24, title_rect.bottom() + 12, rect.width() - 48, 58)
        self._panel(painter, desc_rect)
        self._text(painter, desc_rect.adjusted(10, 8, -10, -8), self.description, 9, QColor("#F7EBC8"), False, Qt.AlignTop | Qt.TextWordWrap)

    def _frame(self, painter: QPainter, rect: QRectF) -> None:
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0, QColor("#06101F"))
        gradient.setColorAt(0.58, QColor("#0B1830"))
        gradient.setColorAt(1, QColor("#071326"))
        painter.setBrush(gradient)
        painter.setPen(QPen(QColor("#D99A3A"), 2))
        painter.drawRoundedRect(rect, 12, 12)
        painter.setPen(QPen(QColor("#F4C46A"), 1))
        painter.drawRect(rect.adjusted(8, 8, -8, -8))
        painter.setPen(QPen(QColor("#6D411A"), 1))
        painter.drawRect(rect.adjusted(14, 14, -14, -14))
        self._corner(painter, rect.topLeft() + QPointF(14, 14), 1, 1)
        self._corner(painter, rect.topRight() + QPointF(-14, 14), -1, 1)
        self._corner(painter, rect.bottomLeft() + QPointF(14, -14), 1, -1)
        self._corner(painter, rect.bottomRight() + QPointF(-14, -14), -1, -1)
        self._stars(painter, rect)

    def _corner(self, painter: QPainter, point, sx: int, sy: int) -> None:
        painter.setPen(QPen(QColor("#D99A3A"), 2))
        painter.drawLine(point, point + QPointF(sx * 24, 0))
        painter.drawLine(point, point + QPointF(0, sy * 24))
        painter.setPen(QPen(QColor("#F4C46A"), 1))
        inner = point + QPointF(sx * 8, sy * 8)
        painter.drawLine(inner, inner + QPointF(sx * 14, 0))
        painter.drawLine(inner, inner + QPointF(0, sy * 14))

    def _stars(self, painter: QPainter, rect: QRectF) -> None:
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#B7742C"))
        for px, py, size in [
            (0.20, 0.18, 3),
            (0.76, 0.21, 2),
            (0.32, 0.35, 2),
            (0.86, 0.42, 3),
            (0.15, 0.61, 2),
            (0.70, 0.70, 2),
            (0.25, 0.84, 2),
            (0.80, 0.88, 3),
        ]:
            painter.drawRect(QRectF(rect.left() + rect.width() * px, rect.top() + rect.height() * py, size, size))

    def _panel(self, painter: QPainter, rect: QRectF) -> None:
        painter.setBrush(QColor("#071326"))
        painter.setPen(QPen(QColor("#D99A3A"), 1))
        painter.drawRoundedRect(rect, 8, 8)
        painter.setPen(QPen(QColor("#4F3217"), 1))
        painter.drawRoundedRect(rect.adjusted(4, 4, -4, -4), 5, 5)

    def _art(self, painter: QPainter, rect: QRectF) -> None:
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#09172B"))
        painter.drawRoundedRect(rect, 8, 8)
        painter.setPen(QPen(QColor("#D99A3A"), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, 8, 8)
        if self.splash_path and Path(self.splash_path).exists():
            pixmap = image_pixmap(self.splash_path, rect.size().toSize())
            if not pixmap.isNull():
                scaled = pixmap.scaled(rect.size().toSize(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                x = rect.left() + (rect.width() - scaled.width()) / 2
                y = rect.top() + (rect.height() - scaled.height()) / 2
                painter.drawPixmap(int(x), int(y), scaled)
                painter.setPen(QPen(QColor("#F4C46A"), 1))
                painter.drawRoundedRect(rect.adjusted(4, 4, -4, -4), 6, 6)
                return
        self._text(painter, rect, "Splash Art", 11, QColor("#8FA6BD"), True, Qt.AlignCenter)

    def _text(self, painter: QPainter, rect: QRectF, text: str, size: int, color: QColor, bold: bool, flags: Qt.AlignmentFlag) -> None:
        font = QFont("Segoe UI", size)
        font.setBold(bold)
        painter.setFont(font)
        painter.setPen(color)
        painter.drawText(rect, flags, text)


class DeckDialog(QDialog):
    def __init__(self, parent: QWidget, deck: Deck | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Baralho")
        self.cover_path = deck.cover_path if deck else None
        self.name_input = QLineEdit(deck.name if deck else "")
        self.cover_label = QLabel(self.cover_path or "Sem capa")
        cover_btn = QPushButton("Escolher capa")
        cover_btn.clicked.connect(self.choose_cover)
        save_btn = QPushButton("Salvar")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)

        form = QFormLayout()
        form.addRow("Nome", self.name_input)
        form.addRow("Capa", self.cover_label)
        form.addRow("", cover_btn)
        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(cancel_btn)
        actions.addWidget(save_btn)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(actions)

    def choose_cover(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Escolher capa", "", IMAGE_FILTER)
        if path:
            self.cover_path = path
            self.cover_label.setText(path)

    def values(self) -> tuple[str, str | None]:
        return self.name_input.text().strip(), self.cover_path


class CardDialog(QDialog):
    def __init__(self, parent: QWidget, card: Card | None = None, default_type: str = "game") -> None:
        super().__init__(parent)
        self.setWindowTitle("Carta")
        self.splash_path = card.splash_path if card else None
        self.type_input = QComboBox()
        self.type_input.addItem("Carta de jogo", "game")
        self.type_input.addItem("Carta de jogador", "player")
        self.type_input.setCurrentIndex(0 if (card.card_type if card else default_type) == "game" else 1)
        self.title_input = QLineEdit(card.title if card else "")
        self.title_input.setMaxLength(MAX_TITLE_CHARS)
        self.description_input = QTextEdit(card.description if card else "")
        self.score_input = QSpinBox()
        self.score_input.setRange(-999, 999)
        self.score_input.setValue(card.score or 0 if card else 0)
        self.truth_input = QCheckBox("Carta verdadeira")
        self.truth_input.setChecked(bool(card.truth) if card else True)
        self.splash_label = QLabel(self.splash_path or "Sem splash art")
        self.title_counter = QLabel()
        self.title_counter.setObjectName("LimitHint")
        self.description_counter = QLabel()
        self.description_counter.setObjectName("LimitHint")
        self.splash_hint = QLabel("Splash art recomendada: 1000 x 1000 px")
        self.splash_hint.setObjectName("LimitHint")
        self.preview = CardPreview()
        choose_btn = QPushButton("Escolher splash art")
        choose_btn.clicked.connect(self.choose_splash)
        save_btn = QPushButton("Salvar")
        save_btn.clicked.connect(self.validate_and_accept)
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)

        form = QFormLayout()
        form.addRow("Tipo", self.type_input)
        form.addRow("Titulo", self.title_input)
        form.addRow("", self.title_counter)
        form.addRow("Descricao", self.description_input)
        form.addRow("", self.description_counter)
        form.addRow("Pontuacao", self.score_input)
        form.addRow("", self.truth_input)
        form.addRow("Splash art", self.splash_label)
        form.addRow("", self.splash_hint)
        form.addRow("", choose_btn)

        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(cancel_btn)
        actions.addWidget(save_btn)

        left = QVBoxLayout()
        left.addLayout(form)
        left.addLayout(actions)
        root = QHBoxLayout(self)
        root.addLayout(left, 2)
        root.addWidget(self.preview, 1)

        self.title_input.textChanged.connect(lambda: self.refresh_preview())
        self.description_input.textChanged.connect(lambda: self.refresh_preview())
        self.score_input.valueChanged.connect(lambda: self.refresh_preview())
        self.truth_input.stateChanged.connect(lambda: self.refresh_preview())
        self.type_input.currentIndexChanged.connect(self.update_fields)
        self.update_fields()
        self.refresh_preview()

    def update_fields(self) -> None:
        is_game = self.type_input.currentData() == "game"
        self.score_input.setEnabled(is_game)
        self.truth_input.setEnabled(is_game)
        self.refresh_preview()

    def choose_splash(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Escolher splash art", "", IMAGE_FILTER)
        if path:
            try:
                adjusted_path = normalized_splash_path(path)
            except Exception as exc:
                QMessageBox.warning(self, "Splash art", f"Nao foi possivel ajustar a imagem:\n{exc}")
                return
            self.splash_path = adjusted_path
            self.splash_label.setText(adjusted_path)
            if adjusted_path != path:
                QMessageBox.information(
                    self,
                    "Splash art",
                    "A imagem foi ajustada para 1000 x 1000 px e salva na pasta local do Popper 3.",
                )
            self.refresh_preview()

    def refresh_preview(self) -> None:
        title_len = len(self.title_input.text())
        desc_len = len(self.description_input.toPlainText())
        max_desc = self.max_description_chars()
        self.title_counter.setText(f"{title_len}/{MAX_TITLE_CHARS} caracteres")
        self.description_counter.setText(f"{desc_len}/{max_desc} caracteres")
        self.description_counter.setProperty("invalid", desc_len > max_desc)
        self.description_counter.style().unpolish(self.description_counter)
        self.description_counter.style().polish(self.description_counter)
        self.preview.set_data(
            self.type_input.currentData(),
            self.title_input.text(),
            self.description_input.toPlainText(),
            self.score_input.value(),
            self.splash_path,
        )

    def max_description_chars(self) -> int:
        if self.type_input.currentData() == "game":
            return MAX_GAME_DESCRIPTION_CHARS
        return MAX_PLAYER_DESCRIPTION_CHARS

    def validation_error(self) -> str | None:
        title = self.title_input.text().strip()
        description = self.description_input.toPlainText().strip()
        if not title:
            return "Informe o titulo da carta."
        if len(title) > MAX_TITLE_CHARS:
            return f"O titulo deve ter no maximo {MAX_TITLE_CHARS} caracteres."
        max_desc = self.max_description_chars()
        if len(description) > max_desc:
            return f"A descricao deve ter no maximo {max_desc} caracteres para este tipo de carta."
        return None

    def validate_and_accept(self) -> None:
        error = self.validation_error()
        if error:
            QMessageBox.warning(self, "Limites da carta", error)
            return
        self.accept()

    def values(self) -> tuple[str, str, str, int | None, int | None, str | None]:
        card_type = self.type_input.currentData()
        score = self.score_input.value() if card_type == "game" else None
        truth = 1 if self.truth_input.isChecked() else 0
        if card_type != "game":
            truth = None
        return (
            card_type,
            self.title_input.text().strip(),
            self.description_input.toPlainText().strip(),
            score,
            truth,
            self.splash_path,
        )


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.db = Database()
        self.current_deck_id: int | None = None
        self.setWindowTitle("Popper 3")
        self.setWindowIcon(QIcon(str(resource_path(ICON_RELATIVE_PATH))))
        self.resize(1180, 760)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.deck_page = EduPage()
        self.cards_page = EduPage()
        self.stack.addWidget(self.deck_page)
        self.stack.addWidget(self.cards_page)
        self._build_deck_page()
        self._build_cards_page()
        self._style()
        self.refresh_decks()

    def _build_deck_page(self) -> None:
        header = BrandHeader("Popper 3", "Baralhos salvos no banco local")
        new_btn = QPushButton("Novo baralho")
        new_btn.clicked.connect(self.new_deck)
        self.deck_list = QListWidget()
        self.deck_list.setObjectName("DeckList")
        self.deck_list.setViewMode(QListWidget.IconMode)
        self.deck_list.setMovement(QListWidget.Static)
        self.deck_list.setResizeMode(QListWidget.Adjust)
        self.deck_list.setWrapping(True)
        self.deck_list.setSpacing(18)
        self.deck_list.setIconSize(QSize(220, 142))
        self.deck_list.setGridSize(QSize(250, 218))
        self.deck_list.setUniformItemSizes(True)
        self.deck_list.itemDoubleClicked.connect(self.open_selected_deck)
        edit_btn = QPushButton("Editar")
        edit_btn.clicked.connect(self.edit_deck)
        delete_btn = QPushButton("Excluir")
        delete_btn.clicked.connect(self.delete_deck)
        open_btn = QPushButton("Abrir")
        open_btn.clicked.connect(self.open_selected_deck)

        actions = QHBoxLayout()
        actions.addWidget(new_btn)
        actions.addStretch()
        actions.addWidget(edit_btn)
        actions.addWidget(delete_btn)
        actions.addWidget(open_btn)
        layout = QVBoxLayout(self.deck_page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)
        layout.addWidget(header)
        layout.addLayout(actions)
        layout.addWidget(self.deck_list)

    def _build_cards_page(self) -> None:
        self.deck_title = QLabel("")
        self.deck_title.setObjectName("PageTitle")
        back_btn = QPushButton("Voltar")
        back_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.deck_page))
        add_game = QPushButton("Nova carta de jogo")
        add_game.clicked.connect(lambda: self.new_card("game"))
        add_player = QPushButton("Nova carta de jogador")
        add_player.clicked.connect(lambda: self.new_card("player"))
        export_cards = QPushButton("PDF para impressao")
        export_cards.clicked.connect(self.export_cards)
        export_report = QPushButton("Relatorio PDF")
        export_report.clicked.connect(self.export_report)
        template_btn = QPushButton("Modelo Excel")
        template_btn.clicked.connect(self.create_excel_template)
        import_btn = QPushButton("Importar Excel")
        import_btn.clicked.connect(self.import_excel)
        self.cards_list = QListWidget()
        self.cards_list.itemDoubleClicked.connect(self.edit_card)
        edit_btn = QPushButton("Editar carta")
        edit_btn.clicked.connect(self.edit_card)
        delete_btn = QPushButton("Excluir carta")
        delete_btn.clicked.connect(self.delete_card)

        top = QHBoxLayout()
        top.addWidget(back_btn)
        top.addStretch()
        top.addWidget(template_btn)
        top.addWidget(import_btn)
        top.addWidget(export_report)
        top.addWidget(export_cards)
        create = QHBoxLayout()
        create.addWidget(add_game)
        create.addWidget(add_player)
        create.addStretch()
        create.addWidget(edit_btn)
        create.addWidget(delete_btn)
        self.game_count = StatCard("Cartas de jogo", "#2F80ED")
        self.player_count = StatCard("Cartas de jogador", "#44BBA4")
        self.true_count = StatCard("Verdadeiras", "#27AE60")
        self.false_count = StatCard("Falsas", "#E23D28")
        stats = QHBoxLayout()
        stats.setSpacing(12)
        stats.addWidget(self.game_count)
        stats.addWidget(self.player_count)
        stats.addWidget(self.true_count)
        stats.addWidget(self.false_count)
        stats.addStretch()
        layout = QVBoxLayout(self.cards_page)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(12)
        layout.addLayout(top)
        deck_header = QHBoxLayout()
        small_logo = QLabel()
        small_logo.setFixedSize(44, 44)
        logo_pixmap = QPixmap(str(resource_path(LOGO_RELATIVE_PATH)))
        if not logo_pixmap.isNull():
            small_logo.setPixmap(logo_pixmap.scaled(QSize(44, 44), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        deck_header.addWidget(small_logo)
        deck_header.addWidget(self.deck_title)
        deck_header.addStretch()
        layout.addLayout(deck_header)
        layout.addLayout(stats)
        layout.addLayout(create)
        layout.addWidget(self.cards_list)

    def _style(self) -> None:
        self.setStyleSheet(
            """
            QWidget { font-family: "Segoe UI Variable", "Segoe UI"; font-size: 10.5pt; color: #F7FBFF; }
            QMainWindow, QStackedWidget { background: #151D35; }
            #PageTitle {
                color: #FFF5C7;
                font-size: 28pt;
                font-weight: 800;
                padding: 2px 0 0 0;
            }
            #Subtitle {
                color: #BCEEFF;
                font-size: 11.5pt;
                padding-bottom: 4px;
            }
            #BrandLogo {
                border-radius: 12px;
            }
            #StatCard {
                background: rgba(20, 29, 58, 215);
                border: 1px solid rgba(110, 220, 255, 95);
                border-radius: 10px;
                min-width: 150px;
                max-width: 190px;
            }
            #StatValue {
                color: #FFF5C7;
                font-size: 20pt;
                font-weight: 800;
            }
            #StatLabel {
                color: #BCEEFF;
                font-size: 9.5pt;
                font-weight: 650;
            }
            #LimitHint {
                color: #6D7E91;
                font-size: 8.8pt;
            }
            #LimitHint[invalid="true"] {
                color: #E23D28;
                font-weight: 700;
            }
            QPushButton {
                background: #2A5BDB; color: white; border: 1px solid rgba(188, 238, 255, 80); border-radius: 8px;
                padding: 9px 14px;
                font-weight: 650;
            }
            QPushButton:hover { background: #3478FF; }
            QPushButton:pressed { background: #1B46AD; }
            QListWidget {
                background: rgba(12, 20, 42, 190);
                border: 1px solid rgba(110, 220, 255, 95);
                border-radius: 14px;
                padding: 12px;
                outline: 0;
                selection-background-color: #F7C54B;
                selection-color: #1B1738;
            }
            #DeckList::item {
                background: rgba(255, 255, 255, 238);
                color: #1B1738;
                border: 1px solid rgba(188, 238, 255, 130);
                border-radius: 14px;
                padding: 12px;
                margin: 2px;
                font-size: 11pt;
                font-weight: 700;
            }
            #DeckList::item:hover {
                border: 2px solid #5CE8FF;
                background: #F4FBFF;
            }
            #DeckList::item:selected {
                color: #1B1738;
                background: #FFF1A8;
                border: 2px solid #F7C54B;
            }
            QListWidget::item {
                color: #F7FBFF;
                padding: 10px;
                border-bottom: 1px solid rgba(188, 238, 255, 65);
            }
            QListWidget::item:selected {
                color: #1B1738;
                background: #FFF1A8;
            }
            QLineEdit, QTextEdit, QSpinBox, QComboBox {
                background: white; color: #1B1738; border: 1px solid #7DCDF2; border-radius: 8px; padding: 7px;
            }
            """
        )

    def refresh_decks(self) -> None:
        self.deck_list.clear()
        for deck in self.db.decks():
            item = QListWidgetItem(deck.name)
            item.setIcon(deck_cover_icon(deck, QSize(220, 142)))
            item.setSizeHint(QSize(250, 218))
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
            item.setData(Qt.UserRole, deck.id)
            if deck.cover_path:
                item.setToolTip(deck.cover_path)
            self.deck_list.addItem(item)

    def refresh_cards(self) -> None:
        if self.current_deck_id is None:
            return
        deck = self.db.deck(self.current_deck_id)
        if not deck:
            return
        self.deck_title.setText(deck.name)
        self.cards_list.clear()
        cards = self.db.cards(deck.id)
        game_total = sum(1 for card in cards if card.card_type == "game")
        player_total = sum(1 for card in cards if card.card_type == "player")
        true_total = sum(1 for card in cards if card.card_type == "game" and card.truth)
        false_total = sum(1 for card in cards if card.card_type == "game" and not card.truth)
        self.game_count.set_value(game_total)
        self.player_count.set_value(player_total)
        self.true_count.set_value(true_total)
        self.false_count.set_value(false_total)
        for card in cards:
            kind = "Jogo" if card.card_type == "game" else "Jogador"
            score = f" | {card.score} pts" if card.card_type == "game" else ""
            truth = " | verdadeira" if card.truth else " | falsa" if card.card_type == "game" else ""
            item = QListWidgetItem(f"{kind}: {card.title}{score}{truth}")
            item.setData(Qt.UserRole, card.id)
            if card.splash_path:
                item.setToolTip(card.splash_path)
            self.cards_list.addItem(item)

    def selected_deck_id(self) -> int | None:
        item = self.deck_list.currentItem()
        return int(item.data(Qt.UserRole)) if item else None

    def selected_card_id(self) -> int | None:
        item = self.cards_list.currentItem()
        return int(item.data(Qt.UserRole)) if item else None

    def new_deck(self) -> None:
        dialog = DeckDialog(self)
        if dialog.exec() == QDialog.Accepted:
            name, cover = dialog.values()
            if not name:
                self.warn("Informe o nome do baralho.")
                return
            self.db.create_deck(name, cover)
            self.refresh_decks()

    def edit_deck(self) -> None:
        deck_id = self.selected_deck_id()
        if deck_id is None:
            return
        deck = self.db.deck(deck_id)
        if not deck:
            return
        dialog = DeckDialog(self, deck)
        if dialog.exec() == QDialog.Accepted:
            name, cover = dialog.values()
            if not name:
                self.warn("Informe o nome do baralho.")
                return
            self.db.update_deck(deck.id, name, cover)
            self.refresh_decks()

    def delete_deck(self) -> None:
        deck_id = self.selected_deck_id()
        if deck_id is None:
            return
        if QMessageBox.question(self, "Excluir", "Excluir este baralho e suas cartas?") == QMessageBox.Yes:
            self.db.delete_deck(deck_id)
            self.refresh_decks()

    def open_selected_deck(self) -> None:
        deck_id = self.selected_deck_id()
        if deck_id is None:
            return
        self.current_deck_id = deck_id
        self.refresh_cards()
        self.stack.setCurrentWidget(self.cards_page)

    def new_card(self, default_type: str) -> None:
        if self.current_deck_id is None:
            return
        dialog = CardDialog(self, default_type=default_type)
        if dialog.exec() == QDialog.Accepted:
            card_type, title, description, score, truth, splash = dialog.values()
            if not title:
                self.warn("Informe o titulo da carta.")
                return
            self.db.create_card(self.current_deck_id, card_type, title, description, score, truth, splash)
            self.refresh_cards()

    def edit_card(self) -> None:
        card_id = self.selected_card_id()
        if card_id is None:
            return
        card = self.db.card(card_id)
        if not card:
            return
        dialog = CardDialog(self, card)
        if dialog.exec() == QDialog.Accepted:
            card_type, title, description, score, truth, splash = dialog.values()
            if not title:
                self.warn("Informe o titulo da carta.")
                return
            self.db.update_card(card.id, card_type, title, description, score, truth, splash)
            self.refresh_cards()

    def delete_card(self) -> None:
        card_id = self.selected_card_id()
        if card_id is None:
            return
        if QMessageBox.question(self, "Excluir", "Excluir esta carta?") == QMessageBox.Yes:
            self.db.delete_card(card_id)
            self.refresh_cards()

    def export_cards(self) -> None:
        deck, cards = self.current_deck_and_cards()
        if not deck:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar PDF", f"{deck.name} - cartas.pdf", "PDF (*.pdf)")
        if path:
            export_cards_pdf(deck, cards, path)
            self.info("PDF de impressao gerado.")

    def export_report(self) -> None:
        deck, cards = self.current_deck_and_cards()
        if not deck:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Salvar relatorio", f"{deck.name} - relatorio.pdf", "PDF (*.pdf)")
        if path:
            export_report_pdf(deck, cards, path)
            self.info("Relatorio PDF gerado.")

    def create_excel_template(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Salvar modelo", "modelo-importacao-popper3.xlsx", "Excel (*.xlsx)")
        if path:
            create_template(path)
            self.info("Modelo Excel gerado.")

    def import_excel(self) -> None:
        if self.current_deck_id is None:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Importar Excel", "", "Excel (*.xlsx)")
        if not path:
            return
        try:
            cards = read_game_cards(path)
            count = self.db.import_game_cards(self.current_deck_id, cards)
        except Exception as exc:
            self.warn(str(exc))
            return
        self.refresh_cards()
        self.info(f"{count} cartas de jogo importadas.")

    def current_deck_and_cards(self) -> tuple[Deck | None, list[Card]]:
        if self.current_deck_id is None:
            return None, []
        deck = self.db.deck(self.current_deck_id)
        return deck, self.db.cards(self.current_deck_id)

    def info(self, message: str) -> None:
        QMessageBox.information(self, "Popper 3", message)

    def warn(self, message: str) -> None:
        QMessageBox.warning(self, "Popper 3", message)

    def closeEvent(self, event) -> None:  # noqa: N802
        self.db.close()
        super().closeEvent(event)


def main() -> None:
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(resource_path(ICON_RELATIVE_PATH))))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
