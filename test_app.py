"""Prueba funcional de la evaluación con streamlit.testing (AppTest).

Recorre la evaluación completa: inicio -> 11 módulos -> certificado, y comprueba
también el camino de error, la pérdida de intentos y el reinicio.
"""

from __future__ import annotations

import os
import sys

from streamlit.testing.v1 import AppTest

from analytics import summarize_records
from audio import build_sound
from certificate import build_certificate
from quiz_data import LEVELS, TOTAL_QUESTIONS, rank_for
from report import build_followup_report, build_report_pdf
from storage import load_results, save_result

# Evita escribir resultados de prueba en data/results.json
import tempfile
os.environ["HGPS_RESULTS_FILE"] = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name

ok_count = 0
failures: list[str] = []


def check(condition: bool, message: str) -> None:
    global ok_count
    if condition:
        ok_count += 1
    else:
        failures.append(message)


def button_by_label(at: AppTest, needle: str):
    for b in at.button:
        if needle in b.label:
            return b
    raise AssertionError(f"Botón no encontrado: {needle}. Hay: {[b.label for b in at.button]}")


def next_button(at: AppTest):
    for b in at.button:
        if "CONTINUAR" in b.label or "RESULTADO FINAL" in b.label:
            return b
    raise AssertionError(f"Botón de avance no encontrado. Hay: {[b.label for b in at.button]}")


def text_of(at: AppTest) -> str:
    return "\n".join(m.value for m in at.markdown)


def play_full_miss(at: AppTest, name: str = "Lucía Pérez", training: bool = True) -> None:
    at.text_input(key="player_name").set_value(name)
    at.checkbox[0].set_value(training)
    at.run()
    button_by_label(at, "INICIAR EVALUACIÓN").click().run()

    for level in LEVELS:
        check("Ideas clave del módulo" in text_of(at), f"No se mostró el resumen del módulo {level['id']}")
        check(level["name"] in text_of(at), f"Falta el nombre del módulo {level['id']} en el resumen")
        button_by_label(at, "ENTRAR AL MÓDULO").click().run()

        for q_index, question in enumerate(level["questions"]):
            check("Elige la respuesta correcta" in text_of(at),
                  f"No se mostró la pregunta {q_index + 1} del módulo {level['id']}")
            check(len(at.button) >= 4, f"Se esperaban 4 opciones en el módulo {level['id']}")

            at.button[question["answer"]].click().run()
            check("Por qué" in text_of(at), "No se mostró la explicación tras responder")
            next_button(at).click().run()

    check("EVALUACIÓN COMPLETADA" in text_of(at), "No apareció la pantalla final de la evaluación")
    check(len(at.get("download_button")) >= 2, "No se ofrecieron el certificado PNG y el informe PDF")
    check(name in text_of(at), "El nombre del participante no aparece en el final")


def test_happy_path() -> None:
    at = AppTest.from_file("app.py", default_timeout=120)
    at.run()
    check("DISPENSACIÓN" in text_of(at), "La pantalla de inicio no muestra el título")
    check(any("INICIAR EVALUACIÓN" in b.label for b in at.button), "Falta el botón de inicio")

    at.text_input(key="player_name").set_value("")
    at.run()
    button_by_label(at, "INICIAR EVALUACIÓN").click().run()
    check("Necesitamos tu nombre" in text_of(at), "No se validó el nombre vacío")

    play_full_miss(at, name="Lucía Pérez", training=True)
    check(at.session_state["correct"] == TOTAL_QUESTIONS, "Puntuación de aciertos incorrecta en partida perfecta")
    check(at.session_state["score"] > 0, "La puntuación final quedó en cero")

    button_by_label(at, "REPETIR EVALUACIÓN").click().run()
    check(any("INICIAR EVALUACIÓN" in b.label for b in at.button), "El botón de reinicio no volvió al inicio")


def test_lives_and_gameover() -> None:
    at = AppTest.from_file("app.py", default_timeout=120)
    at.run()
    at.text_input(key="player_name").set_value("Carlos Núñez")
    at.checkbox[0].set_value(False)  # sin modo entrenamiento
    at.run()
    button_by_label(at, "INICIAR EVALUACIÓN").click().run()

    for _ in range(3):
        if at.session_state["phase"] == "briefing":
            button_by_label(at, "ENTRAR AL MÓDULO").click().run()
        level = LEVELS[at.session_state["level"]]
        question = level["questions"][at.session_state["q"]]
        bad_idx = (question["answer"] + 1) % len(question["options"])
        at.button[bad_idx].click().run()
        check("INCORRECTO" in text_of(at), "No se marcó como incorrecto")
        next_button(at).click().run()
        if at.session_state["phase"] == "gameover":
            break

    check("SIN INTENTOS" in text_of(at), "No se llegó a la pantalla de fin de la evaluación")
    check(at.session_state["lives"] == 0, "Los intentos no llegaron a cero")
    check(len(at.expander) >= 1, "No se mostró el repaso de errores")

    button_by_label(at, "REINTENTAR EVALUACIÓN").click().run()
    check(any("INICIAR EVALUACIÓN" in b.label for b in at.button), "El reintento no volvió al inicio")


def test_training_mode_never_ends() -> None:
    at = AppTest.from_file("app.py", default_timeout=120)
    at.run()
    at.text_input(key="player_name").set_value("Ana")
    at.checkbox[0].set_value(True)
    at.run()
    button_by_label(at, "INICIAR EVALUACIÓN").click().run()
    button_by_label(at, "ENTRAR AL MÓDULO").click().run()

    level = LEVELS[0]
    for _ in range(3):
        question = level["questions"][min(at.session_state["q"], len(level["questions"]) - 1)]
        bad_idx = (question["answer"] + 1) % 4
        at.button[bad_idx].click().run()
        next_button(at).click().run()
        if at.session_state["phase"] == "gameover":
            break
    check(at.session_state["phase"] != "gameover", "El modo entrenamiento terminó la partida")
    check(at.session_state["lives"] == 3, "Los intentos cambiaron en modo práctica")


def test_content_integrity() -> None:
    check(TOTAL_QUESTIONS == 36, f"Se esperaban 36 preguntas, hay {TOTAL_QUESTIONS}")
    check(len(LEVELS) == 11, f"Se esperaban 11 módulos, hay {len(LEVELS)}")
    for level in LEVELS:
        check(bool(level["briefing"]), f"El módulo {level['id']} no tiene briefing")
        for q in level["questions"]:
            check(0 <= q["answer"] < len(q["options"]), f"Índice de respuesta inválido en «{q['q'][:30]}»")
            check(len(q["options"]) == 4, f"La pregunta «{q['q'][:30]}» no tiene 4 opciones")
            check(len(set(q["options"])) == 4, f"Opciones duplicadas en «{q['q'][:30]}»")
            check(bool(q["why"]) and bool(q["source"]), f"Falta explicación o fuente en «{q['q'][:30]}»")


def test_report_and_audio() -> None:
    answers = []
    for level in LEVELS:
        for question in level["questions"]:
            answers.append(
                {
                    "level": level["id"],
                    "level_name": level["name"],
                    "icon": level["icon"],
                    "q": question["q"],
                    "options": question["options"],
                    "chosen": question["answer"],
                    "answer": question["answer"],
                    "ok": True,
                    "why": question["why"],
                    "source": question["source"],
                }
            )
    title, _, _ = rank_for(1.0)
    cert = build_certificate(
        name="María Núñez",
        score=4320,
        accuracy=1.0,
        correct=TOTAL_QUESTIONS,
        total=TOTAL_QUESTIONS,
        rank_title=title,
        streak=TOTAL_QUESTIONS,
    )
    report = build_followup_report(
        name="María Núñez",
        score=4320,
        accuracy=1.0,
        correct=TOTAL_QUESTIONS,
        total=TOTAL_QUESTIONS,
        rank_title=title,
        streak=TOTAL_QUESTIONS,
        elapsed=754,
        answers=answers,
        levels=LEVELS,
    )
    pdf = build_report_pdf(cert, report)
    check(cert.startswith(b"\x89PNG"), "El certificado no es un PNG válido")
    check(report.startswith(b"\x89PNG"), "La página de seguimiento no es un PNG válido")
    check(pdf.startswith(b"%PDF"), "El informe combinado no es un PDF válido")
    check(pdf.count(b"/MediaBox") >= 2, "El PDF no contiene las dos páginas esperadas")
    for kind in ("ok", "ko", "done"):
        wav = build_sound(kind)
        check(wav.startswith(b"RIFF") and b"WAVE" in wav[:16], f"El sonido {kind} no es un WAV válido")


def test_storage_roundtrip() -> None:
    record = {
        "id": "test-record-1",
        "created_at": "2026-10-22T10:00:00",
        "name": "Participante de prueba",
        "training": False,
        "score": 100,
        "correct": 1,
        "total": TOTAL_QUESTIONS,
        "accuracy": 1 / TOTAL_QUESTIONS,
        "best_streak": 1,
        "elapsed": 10,
        "rank": "APRENDIZ COMPROMETIDO",
        "answers": [],
    }
    check(save_result(record), "No se pudo guardar el resultado local de prueba")
    records, error = load_results()
    check(not error, f"Error al leer resultados locales: {error}")
    check(any(r.get("id") == "test-record-1" for r in records), "El resultado guardado no se recuperó")

    os.environ["RESULTS_WEBHOOK"] = "http://example.com/no-https"
    try:
        check(not save_result({**record, "id": "http-test"}), "Se aceptó un webhook sin HTTPS")
    finally:
        os.environ.pop("RESULTS_WEBHOOK", None)


def test_analytics_summary() -> None:
    answers_a = [
        {"level": 1, "ok": True},
        {"level": 1, "ok": False},
    ]
    answers_b = [
        {"level": 1, "ok": True},
        {"level": 1, "ok": True},
    ]
    records = [
        {
            "name": "A", "training": False, "score": 800, "correct": 8, "total": 10,
            "accuracy": 0.8, "best_streak": 3, "elapsed": 100, "rank": "RANGO A",
            "answers": answers_a,
        },
        {
            "name": "B", "training": True, "score": 1000, "correct": 10, "total": 20,
            "accuracy": 0.5, "best_streak": 5, "elapsed": 200, "rank": "RANGO B",
            "answers": answers_b,
        },
    ]
    summary = summarize_records(records, LEVELS)
    check(summary["count"] == 2, "El resumen no contó los participantes")
    check(summary["evaluations"] == 1 and summary["practice"] == 1, "El resumen no separó evaluación/práctica")
    check(abs(summary["weighted_accuracy"] - 0.6) < 1e-9, "La precisión ponderada es incorrecta")
    check(abs(summary["avg_score"] - 900) < 1e-9, "El promedio de puntos es incorrecto")
    module = next(item for item in summary["modules"] if item["id"] == 1)
    check(module["answered"] == 4 and module["correct"] == 3, "Los aciertos por módulo son incorrectos")
    check(abs(module["accuracy"] - 0.75) < 1e-9, "La precisión por módulo es incorrecta")
    check(abs(summary["pct_70"] - 0.5) < 1e-9, "El porcentaje ≥70 % es incorrecto")
    check(summary["ranks"], "El resumen no incluyó la distribución por rango")
    empty = summarize_records([], LEVELS)
    check(empty["count"] == 0 and empty["weighted_accuracy"] == 0, "El resumen vacío no es seguro")


def run_all() -> int:
    test_content_integrity()
    test_report_and_audio()
    test_storage_roundtrip()
    test_analytics_summary()
    test_happy_path()
    test_lives_and_gameover()
    test_training_mode_never_ends()
    print(f"\n{ok_count} comprobaciones OK, {len(failures)} fallos", flush=True)
    for f in failures:
        print("  X", f, flush=True)
    return 0 if not failures else 1


if __name__ == "__main__":
    code = run_all()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)  # evita el cleanup de tempfiles que el sandbox bloquea
