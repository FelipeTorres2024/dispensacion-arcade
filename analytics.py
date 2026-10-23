"""Agregados del panel de administración (promedios ponderados, módulos y rangos)."""

from __future__ import annotations

import json

from quiz_data import rank_for


def _answers(record: dict) -> list[dict]:
    value = record.get("answers") or []
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return []
    return value if isinstance(value, list) else []


def summarize_records(records: list[dict], levels: list[dict]) -> dict:
    """Calcula métricas agregadas ponderadas por preguntas respondidas."""
    count = len(records)
    if count == 0:
        return {
            "count": 0,
            "evaluations": 0,
            "practice": 0,
            "total_questions": 0,
            "total_correct": 0,
            "weighted_accuracy": 0.0,
            "avg_score": 0.0,
            "avg_streak": 0.0,
            "avg_elapsed": 0.0,
            "pct_70": 0.0,
            "pct_90": 0.0,
            "pct_95": 0.0,
            "modules": [],
            "ranks": [],
            "weak_modules": [],
        }

    total_questions = 0
    total_correct = 0
    scores = []
    streaks = []
    elapsed = []
    accuracies = []

    for record in records:
        record_total = int(record.get("total") or 0)
        record_correct = int(record.get("correct") or 0)
        if not record_total:
            record_total = len(_answers(record))
        if not record_correct:
            record_correct = sum(1 for answer in _answers(record) if answer.get("ok"))
        total_questions += max(record_total, 0)
        total_correct += max(record_correct, 0)
        scores.append(int(record.get("score") or 0))
        streaks.append(int(record.get("best_streak") or 0))
        elapsed.append(max(int(record.get("elapsed") or 0), 0))
        accuracy = float(record.get("accuracy") or (record_correct / record_total if record_total else 0))
        accuracies.append(accuracy)

    modules = []
    for level in levels:
        answered = 0
        correct = 0
        for record in records:
            for answer in _answers(record):
                if answer.get("level") == level["id"]:
                    answered += 1
                    if answer.get("ok"):
                        correct += 1
        modules.append(
            {
                "id": level["id"],
                "name": level["name"],
                "answered": answered,
                "correct": correct,
                "accuracy": correct / answered if answered else 0.0,
            }
        )

    rank_counts: dict[str, int] = {}
    for record, accuracy in zip(records, accuracies):
        title = str(record.get("rank") or "") or rank_for(accuracy)[0]
        rank_counts[title] = rank_counts.get(title, 0) + 1

    ranks = [
        {"title": title, "count": amount, "pct": amount / count}
        for title, amount in sorted(rank_counts.items(), key=lambda item: item[1], reverse=True)
    ]
    weak = sorted(
        (module for module in modules if module["answered"] and module["accuracy"] < 0.7),
        key=lambda module: module["accuracy"],
    )

    return {
        "count": count,
        "evaluations": sum(1 for record in records if not record.get("training")),
        "practice": sum(1 for record in records if record.get("training")),
        "total_questions": total_questions,
        "total_correct": total_correct,
        "weighted_accuracy": total_correct / total_questions if total_questions else 0.0,
        "avg_score": sum(scores) / count,
        "avg_streak": sum(streaks) / count,
        "avg_elapsed": sum(elapsed) / count,
        "pct_70": sum(1 for accuracy in accuracies if accuracy >= 0.70) / count,
        "pct_90": sum(1 for accuracy in accuracies if accuracy >= 0.90) / count,
        "pct_95": sum(1 for accuracy in accuracies if accuracy >= 0.95) / count,
        "modules": modules,
        "ranks": ranks,
        "weak_modules": weak,
    }
