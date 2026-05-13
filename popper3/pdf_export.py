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
    _frame(c, x, y, colors.HexColor("#1E2A37"), colors.HexColor("#F8FAFC"))
    c.setFillColor(colors.HexColor("#253246"))
    c.roundRect(x + 4 * mm, y + CARD_H - 13 * mm, CARD_W - 8 * mm, 9 * mm, 2 * mm, stroke=0, fill=1)
    _center_text(c, card.title, x + CARD_W / 2, y + CARD_H - 10 * mm, 9, colors.white, bold=True)
    _image_or_placeholder(c, card.splash_path, x + 6 * mm, y + 42 * mm, CARD_W - 12 * mm, 38 * mm)
    c.setFillColor(colors.HexColor("#FFFFFF"))
    c.roundRect(x + 6 * mm, y + 10 * mm, CARD_W - 12 * mm, 28 * mm, 2 * mm, stroke=0, fill=1)
    _wrapped_text(c, card.description, x + 9 * mm, y + 14 * mm, CARD_W - 18 * mm, 21 * mm, 7.2, colors.HexColor("#27313D"))
    c.setFillColor(colors.HexColor("#E23D28"))
    c.circle(x + CARD_W - 10 * mm, y + 9 * mm, 6 * mm, stroke=0, fill=1)
    _center_text(c, str(card.score or 0), x + CARD_W - 10 * mm, y + 7.5 * mm, 10, colors.white, bold=True)
    c.restoreState()


def draw_player_card(c: canvas.Canvas, card: Card, x: float, y: float) -> None:
    c.saveState()
    _frame(c, x, y, colors.HexColor("#272727"), colors.HexColor("#FBF7EF"))
    _image_or_placeholder(c, card.splash_path, x + 5 * mm, y + 36 * mm, CARD_W - 10 * mm, 50 * mm)
    c.setFillColor(colors.HexColor("#111827"))
    c.roundRect(x + 7 * mm, y + 27 * mm, CARD_W - 14 * mm, 10 * mm, 2 * mm, stroke=0, fill=1)
    _center_text(c, card.title, x + CARD_W / 2, y + 30.7 * mm, 9.5, colors.white, bold=True)
    c.setFillColor(colors.HexColor("#FFFFFF"))
    c.roundRect(x + 7 * mm, y + 8 * mm, CARD_W - 14 * mm, 16 * mm, 2 * mm, stroke=0, fill=1)
    _wrapped_text(c, card.description, x + 10 * mm, y + 11 * mm, CARD_W - 20 * mm, 10 * mm, 7.2, colors.HexColor("#303030"))
    c.restoreState()


def _frame(c: canvas.Canvas, x: float, y: float, border: colors.Color, fill: colors.Color) -> None:
    c.setFillColor(fill)
    c.setStrokeColor(border)
    c.setLineWidth(1.2)
    c.roundRect(x, y, CARD_W, CARD_H, 3 * mm, stroke=1, fill=1)
    c.setStrokeColor(colors.HexColor("#D1D5DB"))
    c.setLineWidth(0.35)
    c.rect(x + 2 * mm, y + 2 * mm, CARD_W - 4 * mm, CARD_H - 4 * mm, stroke=1, fill=0)


def _image_or_placeholder(c: canvas.Canvas, path: str | None, x: float, y: float, w: float, h: float) -> None:
    c.setFillColor(colors.HexColor("#D9DEE5"))
    c.roundRect(x, y, w, h, 2 * mm, stroke=0, fill=1)
    if not path or not Path(path).exists():
        _center_text(c, "Splash Art", x + w / 2, y + h / 2, 9, colors.HexColor("#667085"), bold=True)
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
    except Exception:
        _center_text(c, "Imagem invalida", x + w / 2, y + h / 2, 8, colors.HexColor("#667085"), bold=True)


def _center_text(c: canvas.Canvas, text: str, x: float, y: float, size: float, color: colors.Color, bold: bool = False) -> None:
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawCentredString(x, y, _ellipsize(text, 27))


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
