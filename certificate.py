"""Genera el certificado de charla completada como PNG (sin dependencias de red)."""

from __future__ import annotations

import io
import math
import os
from datetime import date
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1600, 1130

BG_TOP = (255, 255, 255)
BG_BOTTOM = (240, 249, 251)
NAVY = (50, 71, 123)
CYAN = (0, 188, 212)
CYAN_DARK = (0, 110, 124)
LIME = (186, 191, 51)
TEXT = (48, 65, 79)
MUTED = (78, 97, 110)
LINE = (213, 227, 231)

_FONT_CANDIDATES = {
    "regular": ["segoeui.ttf", "arial.ttf", "calibri.ttf", "DejaVuSans.ttf"],
    "semibold": ["seguisb.ttf", "segoeuib.ttf", "arialbd.ttf", "calibrib.ttf", "DejaVuSans-Bold.ttf"],
    "bold": ["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf", "DejaVuSans-Bold.ttf"],
    "black": ["seguibl.ttf", "segoeuib.ttf", "ariblk.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf"],
}


@lru_cache(maxsize=64)
def _resolve_font(name: str) -> str | None:
    """Busca una fuente en Windows y en los directorios habituales de Linux/macOS."""
    roots = [
        os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
        "/usr/share/fonts/truetype",
        "/usr/local/share/fonts",
        str(Path.home() / ".fonts"),
        "/System/Library/Fonts",
        "/Library/Fonts",
    ]
    for root in roots:
        direct = os.path.join(root, name)
        if os.path.isfile(direct):
            return direct
        if os.path.isdir(root):
            for match in sorted(Path(root).rglob(name)):
                if match.is_file():
                    return str(match)
    return None


def _font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    for name in _FONT_CANDIDATES.get(weight, _FONT_CANDIDATES["regular"]):
        path = _resolve_font(name)
        if path:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # Pillow antiguo
        return ImageFont.load_default()


def _vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    base = Image.new("RGB", (1, h))
    px = base.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        px[0, y] = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
    return base.resize(size, Image.BILINEAR)


def _glow(size: tuple[int, int], center: tuple[int, int], radius: int, color: tuple[int, int, int], alpha: int) -> Image.Image:
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    cx, cy = center
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(*color, alpha))
    return layer.filter(ImageFilter.GaussianBlur(radius // 3))


def _star(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, color, inner: float = 0.42, points: int = 5):
    pts = []
    for i in range(points * 2):
        angle = -math.pi / 2 + i * math.pi / points
        rad = r if i % 2 == 0 else r * inner
        pts.append((cx + rad * math.cos(angle), cy + rad * math.sin(angle)))
    draw.polygon(pts, fill=color)


def _tracked(draw, xy, text, font, fill, tracking=0, anchor_center=True):
    """Dibuja texto con espaciado extra entre letras (estilo editorial)."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x, y = xy
    if anchor_center:
        x -= total / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += w + tracking


def _fit(draw, text, size, weight, max_width, min_size=18):
    while size > min_size:
        f = _font(size, weight)
        if draw.textlength(text, font=f) <= max_width:
            return f
        size -= 2
    return _font(min_size, weight)


def build_certificate(
    name: str,
    score: int,
    accuracy: float,
    correct: int,
    total: int,
    rank_title: str,
    streak: int,
    when: date | None = None,
) -> bytes:
    img = _vertical_gradient((W, H), BG_TOP, BG_BOTTOM).convert("RGBA")

    # Resplandores de fondo
    img.alpha_composite(_glow((W, H), (300, 180), 420, CYAN, 12))
    img.alpha_composite(_glow((W, H), (1330, 950), 460, LIME, 8))

    draw = ImageDraw.Draw(img)

    # Retícula sutil (en capa aparte para componer el alfa correctamente)
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(grid)
    for x in range(0, W, 80):
        g_draw.line([(x, 0), (x, H)], fill=(50, 71, 123, 9), width=1)
    for y in range(0, H, 80):
        g_draw.line([(0, y), (W, y)], fill=(50, 71, 123, 9), width=1)
    img.alpha_composite(grid)

    # Marco doble
    draw.rounded_rectangle([38, 38, W - 38, H - 38], radius=26, outline=(*NAVY, 255), width=5)
    draw.rounded_rectangle([58, 58, W - 58, H - 58], radius=18, outline=(*CYAN, 160), width=2)

    # Esquinas
    for cx, cy in [(58, 58), (W - 58, 58), (58, H - 58), (W - 58, H - 58)]:
        draw.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(*CYAN, 255))

    # Encabezado
    _tracked(draw, (W / 2, 78), "HOSPITAL GENERAL DE LA PLAZA DE LA SALUD",
             _font(18, "semibold"), NAVY, tracking=4)
    f_kicker = _font(26, "semibold")
    _tracked(draw, (W / 2, 112), "C E R T I F I C A D O", f_kicker, CYAN_DARK, tracking=8)

    for i in range(3):
        _star(draw, W / 2 - 38 + i * 38, 186, 13, (*LIME, 240))

    draw.text((W / 2, 216), "CHARLA COMPLETADA", font=_font(64, "black"), fill=NAVY, anchor="ma")

    draw.line([(W / 2 - 170, 306), (W / 2 + 170, 306)], fill=(*CYAN_DARK, 170), width=3)

    # Nombre
    draw.text((W / 2, 344), "SE OTORGA A", font=_font(24, "semibold"), fill=MUTED, anchor="ma")
    f_name = _fit(draw, name, 82, "black", 1240)
    draw.text((W / 2, 386), name, font=f_name, fill=NAVY, anchor="ma")

    # Descripción
    f_desc = _font(28, "regular")
    draw.text(
        (W / 2, 500),
        "por completar los 11 módulos de la CHARLA DE DISPENSACIÓN HOSPITALARIA",
        font=f_desc,
        fill=MUTED,
        anchor="ma",
    )
    draw.text(
        (W / 2, 544),
        "Procesos, Seguridad y el Valor Humano",
        font=_font(32, "semibold"),
        fill=CYAN_DARK,
        anchor="ma",
    )

    # Panel de estadísticas (capa aparte para que el alfa se componga de verdad)
    panel = [170, 616, W - 170, 796]
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(overlay)
    o_draw.rounded_rectangle(panel, radius=20, fill=(0, 188, 212, 16))
    img.alpha_composite(overlay)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(panel, radius=20, outline=(0, 188, 212, 60), width=2)

    stats = [
        (W * 0.30, "PUNTUACIÓN", f"{score:,}".replace(",", ".")),
        (W * 0.50, "PRECISIÓN", f"{accuracy * 100:.0f}%"),
        (W * 0.70, "RACHA MÁXIMA", f"{streak}"),
    ]
    for cx, label, value in stats:
        _tracked(draw, (cx, 640), label, _font(20, "semibold"), MUTED, tracking=3)
        draw.text((cx, 676), value, font=_font(58, "black"), fill=NAVY, anchor="ma")

    # Estrellas de desempeño
    star_value = 0 if accuracy < 0.5 else (1 if accuracy < 0.7 else (2 if accuracy < 0.9 else 3))
    for i in range(3):
        color = LIME if i < star_value else LINE
        _star(draw, W / 2 - 70 + i * 70, 856, 24, color)

    draw.text(
        (W / 2, 900),
        f"{correct} de {total} aciertos  ·  {rank_title}",
        font=_font(26, "semibold"),
        fill=TEXT,
        anchor="ma",
    )

    # Pie
    today = when or date.today()
    fecha = today.strftime("%d/%m/%Y")
    draw.text((300, 990), "FECHA", font=_font(18, "semibold"), fill=MUTED, anchor="ma")
    draw.text((300, 1018), fecha, font=_font(26, "semibold"), fill=TEXT, anchor="ma")

    draw.line([(W / 2 - 180, 1000), (W / 2 + 180, 1000)], fill=(*CYAN_DARK, 170), width=2)
    draw.text((W / 2, 1012), "Gerencia de Farmacia · HGPS", font=_font(20, "semibold"), fill=NAVY, anchor="ma")
    draw.text((W / 2, 1046), "Dispensación segura", font=_font(17, "regular"), fill=MUTED, anchor="ma")

    draw.text(
        (W - 300, 990),
        "MÓDULOS",
        font=_font(18, "semibold"),
        fill=MUTED,
        anchor="ma",
    )
    draw.text((W - 300, 1018), "11 / 11", font=_font(26, "semibold"), fill=TEXT, anchor="ma")

    out = io.BytesIO()
    img.convert("RGB").save(out, format="PNG", optimize=True)
    return out.getvalue()
