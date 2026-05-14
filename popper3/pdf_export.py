from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

from popper3.db import Card, Deck


CARD_W = 69 * mm
CARD_H = 96 * mm
PRINT_COLS = 2
PRINT_ROWS = 4
CARDS_PER_PAGE = PRINT_COLS * PRINT_ROWS
DARK = colors.HexColor("#06101F")
DARK_2 = colors.HexColor("#0B1830")
GOLD = colors.HexColor("#D99A3A")
GOLD_LIGHT = colors.HexColor("#F4C46A")
CYAN = colors.HexColor("#4BC7F2")
RED = colors.HexColor("#D84B42")
TEXT = colors.HexColor("#F7EBC8")


def export_cards_pdf(deck: Deck, cards: list[Card], path: str | Path) -> None:
    c = canvas.Canvas(str(path), pagesize=A4)
    page_w, page_h = A4
    slot_w = CARD_H
    slot_h = CARD_W
    margin_x = (page_w - (PRINT_COLS * slot_w)) / 2
    margin_y = (page_h - (PRINT_ROWS * slot_h)) / 2
    positions = []
    for row in range(PRINT_ROWS):
        for col in range(PRINT_COLS):
            x = margin_x + col * slot_w
            y = page_h - margin_y - (row + 1) * slot_h
            positions.append((x, y))

    for index, card in enumerate(cards):
        if index and index % CARDS_PER_PAGE == 0:
            c.showPage()
        x, y = positions[index % CARDS_PER_PAGE]
        c.saveState()
        c.translate(x + CARD_H, y)
        c.rotate(90)
        if card.card_type == "game":
            draw_game_card(c, card, 0, 0)
        else:
            draw_player_card(c, card, 0, 0)
        c.restoreState()
    c.save()


def export_report_pdf(deck: Deck, cards: list[Card], path: str | Path) -> None:
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=18 * mm, leftMargin=18 * mm)
    story = [Paragraph(f"Relatorio de cartas - {deck.name}", styles["Title"]), Spacer(1, 8 * mm)]
    data = [["Titulo", "Pontuacao", "Veracidade"]]
    for card in cards:
        if card.card_type == "game":
            data.append([card.title, str(card.score or 0), "Verdadeira" if card.truth else "Falsa"])
    table = Table(data, colWidths=[110 * mm, 30 * mm, 34 * mm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#253246")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#AAB2BD")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F4F6F8")]),
            ]
        )
    )
    story.append(table)
    doc.build(story)


def draw_game_card(c: canvas.Canvas, card: Card, x: float, y: float) -> None:
    c.saveState()
    _frame(c, x, y)
    _panel(c, x + 4 * mm, y + CARD_H - 15 * mm, CARD_W - 8 * mm, 10 * mm)
    _center_text(c, card.title, x + CARD_W / 2, y + CARD_H - 11.3 * mm, 8.7, TEXT, bold=True, limit=28)
    _image_or_placeholder(c, card.splash_path, x + 6 * mm, y + 43 * mm, CARD_W - 12 * mm, 36 * mm)
    _panel(c, x + 6 * mm, y + 12 * mm, CARD_W - 12 * mm, 27 * mm)
    _wrapped_text(c, card.description, x + 9 * mm, y + 15 * mm, CARD_W - 20 * mm, 20 * mm, 6.9, TEXT)
    _score_medallion(c, x + CARD_W - 10 * mm, y + 9.2 * mm, str(card.score or 0))
    c.restoreState()


def draw_player_card(c: canvas.Canvas, card: Card, x: float, y: float) -> None:
    c.saveState()
    _frame(c, x, y)
    _image_or_placeholder(c, card.splash_path, x + 6 * mm, y + 38 * mm, CARD_W - 12 * mm, 47 * mm)
    _panel(c, x + 7 * mm, y + 26 * mm, CARD_W - 14 * mm, 10 * mm)
    _center_text(c, card.title, x + CARD_W / 2, y + 29.7 * mm, 9.3, TEXT, bold=True, limit=27)
    _panel(c, x + 7 * mm, y + 8 * mm, CARD_W - 14 * mm, 15 * mm)
    _wrapped_text(c, card.description, x + 10 * mm, y + 10.5 * mm, CARD_W - 20 * mm, 10 * mm, 6.9, TEXT)
    c.restoreState()


def _frame(c: canvas.Canvas, x: float, y: float) -> None:
    c.setFillColor(DARK)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.1)
    c.roundRect(x, y, CARD_W, CARD_H, 3 * mm, stroke=1, fill=1)
    c.setFillColor(DARK_2)
    c.roundRect(x + 2 * mm, y + 2 * mm, CARD_W - 4 * mm, CARD_H - 4 * mm, 2 * mm, stroke=0, fill=1)
    c.setStrokeColor(GOLD_LIGHT)
    c.setLineWidth(0.45)
    c.rect(x + 2.6 * mm, y + 2.6 * mm, CARD_W - 5.2 * mm, CARD_H - 5.2 * mm, stroke=1, fill=0)
    c.setStrokeColor(colors.HexColor("#6D411A"))
    c.setLineWidth(0.25)
    c.rect(x + 3.8 * mm, y + 3.8 * mm, CARD_W - 7.6 * mm, CARD_H - 7.6 * mm, stroke=1, fill=0)
    _corner(c, x + 3.6 * mm, y + CARD_H - 3.6 * mm, 1, -1)
    _corner(c, x + CARD_W - 3.6 * mm, y + CARD_H - 3.6 * mm, -1, -1)
    _corner(c, x + 3.6 * mm, y + 3.6 * mm, 1, 1)
    _corner(c, x + CARD_W - 3.6 * mm, y + 3.6 * mm, -1, 1)
    _stars(c, x, y)


def _corner(c: canvas.Canvas, x: float, y: float, sx: int, sy: int) -> None:
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.7)
    c.line(x, y, x + sx * 6 * mm, y)
    c.line(x, y, x, y + sy * 6 * mm)
    c.setLineWidth(0.45)
    c.line(x + sx * 2 * mm, y + sy * 2 * mm, x + sx * 5 * mm, y + sy * 2 * mm)
    c.line(x + sx * 2 * mm, y + sy * 2 * mm, x + sx * 2 * mm, y + sy * 5 * mm)


def _stars(c: canvas.Canvas, x: float, y: float) -> None:
    c.setFillColor(colors.HexColor("#B7742C"))
    for px, py, size in [
        (0.20, 0.18, 0.55),
        (0.76, 0.21, 0.45),
        (0.32, 0.35, 0.35),
        (0.86, 0.42, 0.55),
        (0.15, 0.61, 0.45),
        (0.70, 0.70, 0.35),
        (0.25, 0.84, 0.35),
        (0.80, 0.88, 0.5),
    ]:
        c.rect(x + CARD_W * px, y + CARD_H * py, size * mm, size * mm, stroke=0, fill=1)


def _panel(c: canvas.Canvas, x: float, y: float, w: float, h: float) -> None:
    c.setFillColor(colors.HexColor("#071326"))
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.5)
    c.roundRect(x, y, w, h, 1.7 * mm, stroke=1, fill=1)
    c.setStrokeColor(colors.HexColor("#4F3217"))
    c.setLineWidth(0.25)
    c.roundRect(x + 1 * mm, y + 1 * mm, w - 2 * mm, h - 2 * mm, 1 * mm, stroke=1, fill=0)


def _score_medallion(c: canvas.Canvas, x: float, y: float, text: str) -> None:
    c.setFillColor(RED)
    c.setStrokeColor(GOLD_LIGHT)
    c.setLineWidth(0.75)
    c.circle(x, y, 5.8 * mm, stroke=1, fill=1)
    c.setStrokeColor(colors.HexColor("#7C1F20"))
    c.setLineWidth(0.35)
    c.circle(x, y, 4.5 * mm, stroke=1, fill=0)
    _center_text(c, text, x, y - 1.7 * mm, 9.8, colors.white, bold=True, limit=4)


def _image_or_placeholder(c: canvas.Canvas, path: str | None, x: float, y: float, w: float, h: float) -> None:
    c.setFillColor(colors.HexColor("#09172B"))
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.55)
    c.roundRect(x, y, w, h, 2 * mm, stroke=1, fill=1)
    if not path or not Path(path).exists():
        _center_text(c, "Splash Art", x + w / 2, y + h / 2, 9, colors.HexColor("#8FA6BD"), bold=True)
        return
    try:
        if Path(path).suffix.lower() == ".svg":
            from svglib.svglib import svg2rlg
            from reportlab.graphics import renderPDF

            drawing = svg2rlg(path)
            scale = min(w / drawing.width, h / drawing.height)
            c.saveState()
            c.translate(x + (w - drawing.width * scale) / 2, y + (h - drawing.height * scale) / 2)
            c.scale(scale, scale)
            renderPDF.draw(drawing, c, 0, 0)
            c.restoreState()
        else:
            img = ImageReader(path)
            iw, ih = img.getSize()
            scale = min(w / iw, h / ih)
            draw_w, draw_h = iw * scale, ih * scale
            c.drawImage(img, x + (w - draw_w) / 2, y + (h - draw_h) / 2, draw_w, draw_h, mask="auto")
        c.setStrokeColor(GOLD_LIGHT)
        c.setLineWidth(0.35)
        c.roundRect(x + 0.8 * mm, y + 0.8 * mm, w - 1.6 * mm, h - 1.6 * mm, 1.3 * mm, stroke=1, fill=0)
    except Exception:
        _center_text(c, "Imagem invalida", x + w / 2, y + h / 2, 8, colors.HexColor("#8FA6BD"), bold=True)


def _center_text(
    c: canvas.Canvas,
    text: str,
    x: float,
    y: float,
    size: float,
    color: colors.Color,
    bold: bool = False,
    limit: int = 27,
) -> None:
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawCentredString(x, y, _ellipsize(text, limit))


def _wrapped_text(c: canvas.Canvas, text: str, x: float, y: float, w: float, h: float, size: float, color: colors.Color) -> None:
    c.setFillColor(color)
    c.setFont("Helvetica", size)
    words = text.split()
    lines: list[str] = []
    line = ""
    for word in words:
        probe = f"{line} {word}".strip()
        if c.stringWidth(probe, "Helvetica", size) <= w:
            line = probe
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    max_lines = max(1, int(h / (size + 2)))
    for i, line in enumerate(lines[:max_lines]):
        if i == max_lines - 1 and len(lines) > max_lines:
            line = _ellipsize(line, 42)
        c.drawString(x, y + h - (i + 1) * (size + 2), line)


def _ellipsize(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "..."
