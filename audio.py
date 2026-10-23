"""Tonos breves para la retroalimentación de la evaluación (sin dependencias externas)."""

from __future__ import annotations

import io
import math
import struct
import wave

SAMPLE_RATE = 44100
AMPLITUDE = 0.16

_NOTES = {
    "ok": [(659.25, 0.09), (880.00, 0.13)],
    "ko": [(329.63, 0.13), (220.00, 0.20)],
    "done": [(523.25, 0.09), (659.25, 0.09), (783.99, 0.09), (1046.50, 0.18)],
}


def _tone(freq: float, duration: float) -> bytes:
    """Genera una nota senoidal con fade de entrada y salida para evitar clics."""
    frames = int(SAMPLE_RATE * duration)
    fade = max(1, min(int(SAMPLE_RATE * 0.012), frames // 2))
    data = bytearray()
    for i in range(frames):
        envelope = min(1.0, i / fade, (frames - i) / fade)
        sample = AMPLITUDE * envelope * math.sin(2 * math.pi * freq * i / SAMPLE_RATE)
        data.extend(struct.pack("<h", int(sample * 32767)))
    return bytes(data)


def build_sound(kind: str) -> bytes:
    """Devuelve un WAV mono de 16 bits para 'ok', 'ko' o 'done'."""
    notes = _NOTES.get(kind)
    if not notes:
        raise ValueError(f"Sonido desconocido: {kind}")

    payload = bytearray()
    for freq, duration in notes:
        payload.extend(_tone(freq, duration))
        payload.extend(b"\x00\x00" * int(SAMPLE_RATE * 0.015))  # silencio breve

    out = io.BytesIO()
    with wave.open(out, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(bytes(payload))
    return out.getvalue()
