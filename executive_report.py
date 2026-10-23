"""Informe ejecutivo general de la charla (PDF de 4 páginas con Pillow)."""

from __future__ import annotations

import io
from datetime import date
from pathlib import Path

from PIL import Image, ImageDraw

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
    _vertical_gradient,
)

W, H = 1240, 1754  # A4 vertical a 150 ppp
M = 70
CW = W - 2 * M
LOGO_PATH = Path(__file__).resolve().parent / "assets" / "hgps-logo.png"

SOFT = (239, 249, 251)
GOOD = (46, 125, 50)
BAD = (179, 38, 30)
TRACK = (225, 238, 242)


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: float) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = (current + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _truncate(draw: ImageDraw.ImageDraw, text: str, font, max_width: float) -> str:
    if draw.textlength(text, font=font) <= max_width:
        return text
    suffix = "…"
    while text and draw.textlength(text + suffix, font=font) > max_width:
        text = text[:-1]
    return text.rstrip() + suffix


def _paragraph(draw, text, x, y, font, fill, max_width, line_height):
    for line in _wrap(draw, text, font, max_width):
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y


def _section(draw, title: str, y: int, kicker: str | None = None) -> int:
    if kicker:
        draw.text((M, y), kicker.upper(), font=_font(14, "semibold"), fill=CYAN_DARK)
        y += 22
    draw.text((M, y), title, font=_font(28, "bold"), fill=NAVY)
    y += 40
    draw.line([(M, y - 10), (W - M, y - 10)], fill=LINE, width=1)
    return y + 8


def _page(title: str, subtitle: str, page: int, total: int, big: bool = False):
    img = _vertical_gradient((W, H), (255, 255, 255), (243, 251, 252)).convert("RGBA")
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, W, 7], fill=NAVY)
    draw.rectangle([0, 7, W, 10], fill=CYAN)
    draw.rectangle([0, 10, W, 12], fill=LIME)

    try:
        logo = Image.open(str(LOGO_PATH)).convert("RGBA")
        height = 76 if big else 44
        logo.thumbnail((170 if big else 100, height), Image.LANCZOS)
        img.alpha_composite(logo, (M, 48 if big else 42))
        text_x = M + (176 if big else 112)
    except OSError:
        text_x = M

    draw.text(
        (text_x, 48 if big else 44),
        title,
        font=_font(38 if big else 25, "black"),
        fill=NAVY,
    )
    draw.text((text_x, 96 if big else 77), subtitle, font=_font(19 if big else 15, "regular"), fill=MUTED)

    draw.line([(M, 145 if big else 108), (W - M, 145 if big else 108)], fill=LINE, width=1)
    draw.line([(M, H - 72), (W - M, H - 72)], fill=LINE, width=1)
    draw.text(
        (M, H - 58),
        "Hospital General de la Plaza de la Salud (HGPS) · Gerencia de Farmacia",
        font=_font(13, "regular"),
        fill=MUTED,
    )
    draw.text(
        (W - M, H - 58),
        f"Página {page} de {total}",
        font=_font(13, "semibold"),
        fill=MUTED,
        anchor="ra",
    )
    return img, draw


def _kpi(draw, x, y, w, h, label, value):
    draw.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=(255, 255, 255), outline=LINE, width=2)
    draw.text((x + 18, y + 16), label.upper(), font=_font(13, "semibold"), fill=MUTED)
    draw.text((x + 18, y + 38), value, font=_font(32, "black"), fill=NAVY)


def _bullets(draw, items, x, y, font, fill, max_width, line_height=27):
    for item in items:
        lines = _wrap(draw, "• " + item, font, max_width)
        for line in lines:
            draw.text((x, y), line, font=font, fill=fill)
            y += line_height
        y += 3
    return y


def _module_table(draw, modules) -> int:
    x = M
    y = 165
    widths = [400, 100, 100, 470]
    headers = ["Módulo", "Aciertos", "Precisión", ""]
    draw.rectangle([x, y, x + sum(widths), y + 36], fill=NAVY)
    cx = x
    for width, header in zip(widths, headers):
        draw.text((cx + 12, y + 11), header, font=_font(15, "semibold"), fill=(255, 255, 255))
        cx += width
    y += 36

    for index, module in enumerate(modules):
        fill = (255, 255, 255) if index % 2 == 0 else (247, 252, 253)
        draw.rectangle([x, y, x + sum(widths), y + 39], fill=fill, outline=(232, 241, 244))
        name = _truncate(draw, module["name"], _font(16, "semibold"), widths[0] - 24)
        draw.text((x + 12, y + 10), name, font=_font(16, "semibold"), fill=NAVY)
        draw.text((x + widths[0] + 12, y + 10), f"{module['correct']}/{module['answered']}" if module["answered"] else "—", font=_font(16, "regular"), fill=TEXT)
        pct = module["accuracy"] * 100
        draw.text((x + widths[0] + widths[1] + 12, y + 10), f"{pct:.0f}%" if module["answered"] else "—", font=_font(16, "semibold"), fill=TEXT)

        bar_x = x + widths[0] + widths[1] + widths[2] + 12
        bar_w = widths[3] - 24
        draw.rounded_rectangle([bar_x, y + 15, bar_x + bar_w, y + 27], radius=6, fill=TRACK)
        if module["answered"]:
            color = CYAN if pct >= 90 else (NAVY if pct >= 70 else BAD)
            draw.rounded_rectangle([bar_x, y + 15, bar_x + max(6, bar_w * min(pct, 100) / 100), y + 27], radius=6, fill=color)
        y += 39
    return y


def _rank_table(draw, ranks, y: int) -> int:
    y = _section(draw, "Distribución por rango", y)
    if not ranks:
        draw.text((M, y), "Sin datos de rango.", font=_font(16, "regular"), fill=MUTED)
        return y + 30
    for rank in ranks:
        draw.text((M, y + 2), rank["title"], font=_font(17, "semibold"), fill=NAVY)
        draw.text((M + 430, y + 2), f"{rank['count']} participante(s) · {rank['pct'] * 100:.0f}%", font=_font(16, "regular"), fill=TEXT)
        draw.rounded_rectangle([M + 700, y + 8, W - M, y + 20], radius=6, fill=TRACK)
        draw.rounded_rectangle([M + 700, y + 8, M + 700 + max(6, (W - M - M - 700) * rank["pct"]), y + 20], radius=6, fill=CYAN)
        y += 38
    return y


def _participant_table(draw, records, y: int) -> int:
    headers = ["Participante", "Fecha", "Modo", "Puntos", "Aciertos", "Precisión", "Rango"]
    widths = [270, 120, 110, 80, 90, 90, 340]
    x = M
    draw.rectangle([x, y, x + sum(widths), y + 34], fill=NAVY)
    cx = x
    for width, header in zip(widths, headers):
        draw.text((cx + 10, y + 10), header, font=_font(14, "semibold"), fill=(255, 255, 255))
        cx += width
    y += 34

    for index, record in enumerate(records[:18]):
        fill = (255, 255, 255) if index % 2 == 0 else (247, 252, 253)
        draw.rectangle([x, y, x + sum(widths), y + 31], fill=fill, outline=(232, 241, 244))
        total = int(record.get("total") or 0)
        correct = int(record.get("correct") or 0)
        accuracy = float(record.get("accuracy") or (correct / total if total else 0))
        values = [
            _truncate(draw, str(record.get("name", "—")), _font(14, "semibold"), widths[0] - 18),
            str(record.get("created_at", ""))[:10],
            "Práctica" if record.get("training") else "Evaluación",
            str(record.get("score", 0)),
            f"{correct}/{total}",
            f"{accuracy * 100:.0f}%",
            _truncate(draw, str(record.get("rank", "—")), _font(13, "regular"), widths[6] - 18),
        ]
        cx = x
        for width, value in zip(widths, values):
            draw.text((cx + 10, y + 8), value, font=_font(14 if cx != x + sum(widths[:-1]) else 13, "regular"), fill=TEXT)
            cx += width
        y += 31
    return y


def _architecture(draw, y: int) -> int:
    y = _section(draw, "Arquitectura de la solución", y, "Cómo fluye la información")
    flow = (
        "Participante → Webapp Streamlit (app.py) → Evaluación de 36 preguntas (quiz_data.py) "
        "→ Certificado PNG + informe PDF (certificate.py y report.py). "
        "Los resultados se envían a Google Apps Script (google_apps_script.gs) y se guardan en "
        "Google Sheets (storage.py). El panel de administración lee la hoja, calcula los "
        "promedios con analytics.py y genera este informe ejecutivo."
    )
    y = _paragraph(draw, flow, M, y, _font(17, "regular"), TEXT, CW, 27)
    y += 18

    draw.rounded_rectangle([M, y, W - M, y + 88], radius=12, fill=SOFT, outline=(205, 235, 240), width=2)
    draw.rectangle([M, y, M + 5, y + 88], fill=CYAN)
    y = _paragraph(
        draw,
        "Componentes: app.py (interfaz y estado) · quiz_data.py (contenido) · certificate.py y "
        "report.py (documentos) · analytics.py (agregados) · storage.py (persistencia) · "
        "google_apps_script.gs (endpoint de Google Sheets).",
        M + 20,
        y + 16,
        _font(15, "regular"),
        TEXT,
        CW - 40,
        24,
    )
    y += 76

    y = _section(draw, "Controles de seguridad y datos", y)
    security = [
        "Acceso administrativo con contraseña, sesión de 30 minutos y bloqueo tras 5 intentos.",
        "Secretos en Streamlit Secrets; el token de Google vive en las propiedades del script.",
        "Webhook HTTPS; redirects limitados a dominios de Google.",
        "Celdas de Google Sheets protegidas contra inyección de fórmulas.",
        "Dependencias fijadas y auditadas; no se guardan datos clínicos de pacientes.",
    ]
    y = _bullets(draw, security, M, y, _font(16, "regular"), TEXT, CW, 26)
    y += 10

    y = _section(draw, "Notas y limitaciones", y)
    notes = [
        "La identificación del participante es el nombre digitado; no se valida contra un directorio.",
        "El informe refleja el filtro de modo elegido: todos, evaluación o práctica.",
        "La precisión global es ponderada: aciertos totales / preguntas respondidas.",
        "Muestras pequeñas no permiten inferencia estadística; se recomienda repetir la medición.",
        "Los nombres y respuestas son datos personales: mantén la hoja privada y define retención.",
    ]
    y = _bullets(draw, notes, M, y, _font(15, "regular"), TEXT, CW, 24)
    return y


def build_executive_pages(summary: dict, records: list[dict], levels: list[dict], mode: str, when: date | None = None) -> list[bytes]:
    """Genera las 4 páginas A4 del informe ejecutivo como PNG."""
    today = when or date.today()
    count = summary["count"]
    weighted = summary["weighted_accuracy"]
    level = "Excelente" if weighted >= 0.9 else ("Muy bueno" if weighted >= 0.8 else ("Aceptable" if weighted >= 0.7 else "Requiere refuerzo"))
    minutes, seconds = divmod(int(round(summary["avg_elapsed"])), 60)
    strong = sorted((m for m in summary["modules"] if m["answered"]), key=lambda m: m["accuracy"], reverse=True)
    weak = summary["weak_modules"]
    strong_names = ", ".join(m["name"] for m in strong[:3]) or "sin datos"
    weak_names = ", ".join(m["name"] for m in weak[:4]) or "ninguno por debajo del 70 %"

    pages = []

    # Página 1: resumen ejecutivo, KPIs y speech
    img, draw = _page(
        "INFORME EJECUTIVO",
        "Charla de Dispensación Hospitalaria · HGPS",
        1,
        4,
        big=True,
    )
    draw.text((W - M, 52), f"Fecha: {today.strftime('%d/%m/%Y')}", font=_font(17, "regular"), fill=MUTED, anchor="ra")
    draw.text((W - M, 80), f"Alcance: {mode}", font=_font(16, "semibold"), fill=CYAN_DARK, anchor="ra")
    y = 178
    y = _section(draw, "Resumen ejecutivo", y, "Lectura general")
    intro = (
        f"Se analizaron {count} registro(s): {summary['evaluations']} evaluación(es) y "
        f"{summary['practice']} práctica(s). La precisión global ponderada fue "
        f"{weighted * 100:.1f}% ({summary['total_correct']} aciertos de "
        f"{summary['total_questions']} preguntas). El {summary['pct_70'] * 100:.0f}% alcanzó "
        f"el umbral de 70% y el {summary['pct_90'] * 100:.0f}% superó el 90%."
    )
    y = _paragraph(draw, intro, M, y, _font(18, "regular"), TEXT, CW, 28)
    y += 20

    kpis = [
        ("Participantes", str(count)),
        ("Precisión ponderada", f"{weighted * 100:.0f}%"),
        ("Puntuación promedio", f"{int(round(summary['avg_score'])):,}".replace(",", ".")),
        ("Racha promedio", f"{summary['avg_streak']:.1f}"),
        ("Tiempo promedio", f"{minutes:02d}:{seconds:02d}"),
        ("Con 90% o más", f"{summary['pct_90'] * 100:.0f}%"),
    ]
    x0, y0 = M, y
    gap, card_w, card_h = 16, (CW - 32) / 3, 90
    for index, (label, value) in enumerate(kpis):
        col, row = index % 3, index // 3
        _kpi(draw, x0 + col * (card_w + gap), y0 + row * (card_h + 14), card_w, card_h, label, value)
    y = y0 + 2 * card_h + 14 + 30

    y = _section(draw, "Discurso ejecutivo", y, "Para leer en la reunión")
    speech = (
        f"La charla alcanzó un nivel general {level.lower()}. "
        f"El equipo demuestra una base sólida en {strong_names}; el principal margen de mejora "
        f"está en {weak_names}. Recomendamos reforzar esos contenidos con casos prácticos, "
        f"repetir la evaluación en una segunda cohorte y comparar los resultados por módulo "
        f"para confirmar la mejora."
    )
    speech_lines = _wrap(draw, speech, _font(17, "regular"), CW - 50)
    box_h = len(speech_lines) * 27 + 34
    draw.rounded_rectangle([M, y, W - M, y + box_h], radius=12, fill=SOFT, outline=(205, 235, 240), width=2)
    draw.rectangle([M, y, M + 5, y + box_h], fill=CYAN)
    _paragraph(draw, speech, M + 22, y + 17, _font(17, "regular"), TEXT, CW - 44, 27)
    y += box_h + 30

    y = _section(draw, "Puntos clave", y)
    points = [
        f"Cobertura: {count} participante(s); {summary['evaluations']} en evaluación y {summary['practice']} en práctica.",
        f"Resultado global: {weighted * 100:.1f}% de precisión ponderada; nivel {level}.",
        f"Fortalezas: {strong_names}.",
        f"Prioridad de refuerzo: {weak_names}.",
        "Siguiente paso: repetir la medición y comparar la evolución por módulo.",
    ]
    _bullets(draw, points, M, y, _font(16, "regular"), TEXT, CW, 26)
    pages.append(_png(img))

    # Página 2: módulos, rangos, áreas y método
    img, draw = _page("Desempeño por módulo", "Precisión ponderada y distribución de resultados", 2, 4)
    y = _module_table(draw, summary["modules"])
    y += 26
    y = _rank_table(draw, summary["ranks"], y)
    y += 22

    y = _section(draw, "Áreas de refuerzo", y)
    if weak:
        rows = [f"{module['name']}: {module['correct']}/{module['answered']} ({module['accuracy'] * 100:.0f}%)" for module in weak[:8]]
        y = _bullets(draw, rows, M, y, _font(16, "regular"), TEXT, CW, 25)
        y += 4
        y = _paragraph(
            draw,
            "Recomendación: priorizar estos módulos en la próxima sesión, con ejercicios de "
            "casos y una verificación breve de conceptos clave.",
            M,
            y,
            _font(15, "semibold"),
            CYAN_DARK,
            CW,
            24,
        )
    else:
        draw.text((M, y), "No hay módulos por debajo del 70 %.", font=_font(16, "semibold"), fill=GOOD)
        y += 28

    y += 18
    y = _section(draw, "Método de cálculo", y)
    method = (
        "Precisión global ponderada = aciertos totales / preguntas respondidas. "
        "Precisión por módulo = aciertos del módulo / respuestas del módulo. "
        "Los promedios de puntos, racha y tiempo son aritméticos sobre los registros filtrados. "
        "El filtro de modo permite analizar solo evaluación o solo práctica."
    )
    _paragraph(draw, method, M, y, _font(15, "regular"), TEXT, CW, 24)
    pages.append(_png(img))

    # Página 3: arquitectura, seguridad y notas
    img, draw = _page("Arquitectura y controles", "Del participante al informe ejecutivo", 3, 4)
    _architecture(draw, 140)
    pages.append(_png(img))

    # Página 4: anexo de participantes y notas finales
    img, draw = _page("Anexo: participantes", "Detalle de los registros incluidos en el informe", 4, 4)
    y = 140
    y = _section(draw, "Participantes incluidos", y)
    y = _participant_table(draw, records, y)
    if len(records) > 18:
        draw.text((M, y + 8), f"Mostrando 18 de {len(records)} registros.", font=_font(14, "regular"), fill=MUTED)
        y += 28
    y += 24

    y = _section(draw, "Glosario", y)
    glossary = [
        "Precisión ponderada: proporción de aciertos sobre el total de preguntas respondidas.",
        "Racha: mayor número de aciertos consecutivos alcanzado por el participante.",
        "Rango: reconocimiento calculado a partir de la precisión final.",
        "Modo práctica: permite repetir sin consumir intentos; se puede excluir del análisis.",
    ]
    y = _bullets(draw, glossary, M, y, _font(15, "regular"), TEXT, CW, 24)
    y += 10

    y = _section(draw, "Notas adicionales", y)
    notes = [
        "Este informe agrega datos de la charla; no contiene información clínica de pacientes.",
        "Los nombres y respuestas son datos personales: comparte el PDF solo con el equipo autorizado.",
        "La identidad del participante es autodeclarada; no se valida contra el directorio institucional.",
        "Para muestras pequeñas, interpreta los porcentajes como una referencia descriptiva, no inferencial.",
        "Conserva la hoja de Google privada y define una política de retención y borrado.",
    ]
    _bullets(draw, notes, M, y, _font(15, "regular"), TEXT, CW, 24)
    pages.append(_png(img))

    return pages


def _png(img: Image.Image) -> bytes:
    out = io.BytesIO()
    img.convert("RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()


def build_executive_pdf(summary: dict, records: list[dict], levels: list[dict], mode: str, when: date | None = None) -> bytes:
    pages = build_executive_pages(summary, records, levels, mode, when)
    images = [Image.open(io.BytesIO(page)).convert("RGB") for page in pages]
    out = io.BytesIO()
    images[0].save(
        out,
        format="PDF",
        resolution=150,
        save_all=True,
        append_images=images[1:],
    )
    return out.getvalue()
