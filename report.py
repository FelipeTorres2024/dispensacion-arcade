"""Página de seguimiento (2.ª página del PDF) con métricas, mapa y áreas de mejora."""

from __future__ import annotations

import io
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from certificate import (
    CYAN,
    CYAN_DARK,
    LIME,
    LINE,
    MUTED,
    NAVY,
    TEXT,
    _fit,
    _font,
    _star,
    _vertical_gradient,
)

W, H = 1600, 1130

GOOD_BG = (237, 247, 238)
GOOD_LINE = (183, 223, 192)
MID_BG = (247, 248, 227)
MID_LINE = (226, 227, 184)
BAD_BG = (253, 241, 240)
BAD_LINE = (240, 199, 195)


def _truncate(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: float) -> str:
    if draw.textlength(text, font=font) <= max_width:
        return text
    suffix = "…"
    while text and draw.textlength(text + suffix, font=font) > max_width:
        text = text[:-1]
    return text.rstrip() + suffix


def _rounded_panel(draw: ImageDraw.ImageDraw, box, fill, outline, radius=14, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def build_followup_report(
    name: str,
    score: int,
    accuracy: float,
    correct: int,
    total: int,
    rank_title: str,
    streak: int,
    elapsed: int,
    answers: list[dict],
    levels: list[dict],
    training: bool = False,
    when: date | None = None,
) -> bytes:
    img = _vertical_gradient((W, H), (255, 255, 255), (240, 249, 251)).convert("RGBA")
    draw = ImageDraw.Draw(img)

    # Filete superior institucional
    draw.rectangle([0, 0, W, 6], fill=NAVY)
    draw.rectangle([0, 6, W, 9], fill=CYAN)
    draw.rectangle([0, 9, W, 11], fill=LIME)

    # Logo HGPS (si está disponible)
    logo_path = Path(__file__).resolve().parent / "assets" / "hgps-logo.png"
    if logo_path.is_file():
        try:
            logo = Image.open(logo_path).convert("RGBA")
            logo.thumbnail((150, 76), Image.LANCZOS)
            img.alpha_composite(logo, (80, 48))
        except OSError:
            pass

    # Encabezado
    draw.text((230, 58), "INFORME DE SEGUIMIENTO", font=_font(36, "black"), fill=NAVY)
    draw.text(
        (230, 104),
        "Charla de Dispensación Hospitalaria · Gerencia de Farmacia",
        font=_font(21, "regular"),
        fill=MUTED,
    )
    today = when or date.today()
    draw.text((W - 80, 66), f"Fecha: {today.strftime('%d/%m/%Y')}", font=_font(19, "regular"), fill=MUTED, anchor="ra")
    mode = "Modo práctica" if training else "Evaluación"
    draw.text((W - 80, 96), mode, font=_font(18, "semibold"), fill=CYAN_DARK, anchor="ra")

    draw.line([(80, 156), (W - 80, 156)], fill=LINE, width=2)

    # Participante y rango
    draw.text((80, 180), "PARTICIPANTE", font=_font(16, "semibold"), fill=MUTED)
    draw.text((80, 202), name, font=_fit(draw, name, 34, "black", 900), fill=NAVY)
    draw.text((W - 80, 180), "RANGO", font=_font(16, "semibold"), fill=MUTED, anchor="ra")
    draw.text((W - 80, 202), rank_title, font=_fit(draw, rank_title, 27, "bold", 620), fill=CYAN_DARK, anchor="ra")

    # Panel de métricas
    panel_top, panel_bottom = 264, 378
    _rounded_panel(draw, [80, panel_top, W - 80, panel_bottom], (255, 255, 255), LINE, radius=16, width=2)
    minutes, seconds = divmod(max(elapsed, 0), 60)
    metrics = [
        ("PUNTOS", f"{score:,}".replace(",", ".")),
        ("ACIERTOS", f"{correct} / {total}"),
        ("PRECISIÓN", f"{accuracy * 100:.0f}%"),
        ("MEJOR RACHA", f"{streak}"),
        ("TIEMPO", f"{minutes:02d}:{seconds:02d}"),
    ]
    step = (W - 160) / len(metrics)
    for i, (label, value) in enumerate(metrics):
        cx = 80 + step * i + step / 2
        draw.text((cx, 286), label, font=_font(16, "semibold"), fill=MUTED, anchor="ma")
        draw.text((cx, 312), value, font=_font(36, "black"), fill=NAVY, anchor="ma")

    # Mapa de módulos
    draw.text((80, 418), "Mapa de módulos", font=_font(26, "bold"), fill=NAVY)
    draw.text(
        (W - 80, 428),
        "Verde: dominio · Ámbar: parcial · Rojo: a reforzar",
        font=_font(16, "regular"),
        fill=MUTED,
        anchor="ra",
    )

    by_level: dict[int, list[dict]] = {}
    for answer in answers:
        by_level.setdefault(answer["level"], []).append(answer)

    cols, gap, card_h = 4, 16, 104
    card_w = (W - 160 - gap * (cols - 1)) / cols
    start_y = 462
    for index, level in enumerate(levels):
        row, col = divmod(index, cols)
        x = 80 + col * (card_w + gap)
        y = start_y + row * (card_h + gap)
        level_answers = by_level.get(level["id"], [])
        got = sum(1 for answer in level_answers if answer["ok"])
        level_total = len(level["questions"])
        ratio = got / level_total if level_total else 0
        if ratio == 1:
            fill, border = GOOD_BG, GOOD_LINE
        elif ratio >= 0.5:
            fill, border = MID_BG, MID_LINE
        else:
            fill, border = BAD_BG, BAD_LINE

        _rounded_panel(draw, [x, y, x + card_w, y + card_h], fill, border, radius=10, width=2)
        title = _truncate(draw, level["name"], _font(19, "bold"), card_w - 32)
        draw.text((x + 16, y + 12), title, font=_font(19, "bold"), fill=NAVY)
        stars = 3 if ratio == 1 else (2 if ratio >= 0.5 else 1)
        for i in range(3):
            _star(draw, x + 25 + i * 24, y + 51, 9, LIME if i < stars else LINE)
        draw.text(
            (x + 16, y + 70),
            f"{got} de {level_total} aciertos · {ratio * 100:.0f}%",
            font=_font(15, "regular"),
            fill=TEXT,
        )

    # Aspectos a reforzar
    draw.text((80, 842), "Aspectos a reforzar", font=_font(26, "bold"), fill=NAVY)
    draw.line([(80, 878), (W - 80, 878)], fill=LINE, width=1)

    weak = sorted(
        (
            (level, by_level.get(level["id"], []))
            for level in levels
            if len(level["questions"]) > 0
            and sum(1 for answer in by_level.get(level["id"], []) if answer["ok"]) < len(level["questions"])
        ),
        key=lambda item: (
            sum(1 for answer in item[1] if answer["ok"]) / len(item[0]["questions"])
            if item[0]["questions"]
            else 0
        ),
    )

    draw.text((80, 894), "Módulos con menor desempeño", font=_font(18, "semibold"), fill=CYAN_DARK)
    if weak:
        for i, (level, level_answers) in enumerate(weak[:5]):
            got = sum(1 for answer in level_answers if answer["ok"])
            level_total = len(level["questions"])
            line = f"• {_truncate(draw, level['name'], _font(17, 'regular'), 420)} — {got} de {level_total}"
            draw.text((80, 924 + i * 28), line, font=_font(17, "regular"), fill=TEXT)
    else:
        draw.text((80, 924), "• Todos los módulos completados al 100 %.", font=_font(17, "semibold"), fill=(46, 125, 50))

    draw.text((820, 894), "Preguntas para repasar", font=_font(18, "semibold"), fill=CYAN_DARK)
    wrong = [answer for answer in answers if not answer["ok"]]
    if wrong:
        for i, answer in enumerate(wrong[:3]):
            y = 918 + i * 40
            question = _truncate(draw, answer["q"], _font(16, "regular"), 610)
            draw.text((820, y), f"• {question}", font=_font(16, "regular"), fill=TEXT)
            correct_option = answer["options"][answer["answer"]]
            correct_text = _truncate(draw, correct_option, _font(15, "regular"), 540)
            draw.text((838, y + 19), f"Correcta: {correct_text}", font=_font(15, "regular"), fill=MUTED)
        if len(wrong) > 3:
            draw.text(
                (820, 918 + 3 * 40),
                f"y {len(wrong) - 3} pregunta(s) más en la app.",
                font=_font(15, "semibold"),
                fill=MUTED,
            )
    else:
        draw.text((820, 924), "• Sin respuestas incorrectas.", font=_font(17, "semibold"), fill=(46, 125, 50))

    # Pie
    draw.line([(80, 1082), (W - 80, 1082)], fill=LINE, width=1)
    draw.text(
        (W / 2, 1094),
        "Hospital General de la Plaza de la Salud (HGPS) · Gerencia de Farmacia",
        font=_font(15, "regular"),
        fill=MUTED,
        anchor="ma",
    )

    out = io.BytesIO()
    img.convert("RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()


def build_report_pdf(certificate_png: bytes, report_png: bytes) -> bytes:
    """Combina el certificado y el seguimiento en un PDF de dos páginas landscape."""
    first = Image.open(io.BytesIO(certificate_png)).convert("RGB")
    second = Image.open(io.BytesIO(report_png)).convert("RGB")
    out = io.BytesIO()
    first.save(
        out,
        format="PDF",
        resolution=150,
        save_all=True,
        append_images=[second],
    )
    return out.getvalue()
