from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass
class EvaluationResult:
    precision: float
    recall: float
    counting_error: int
    per_class: Dict[str, Tuple[float, float]]


def _count_occurrences(labels: Iterable[str]) -> Counter[str]:
    return Counter(labels)


def evaluate_dataset(dataset: List[Dict[str, List[str]]]) -> EvaluationResult:
    total_tp = total_fp = total_fn = 0
    per_class_totals: Dict[str, Dict[str, int]] = {}
    counting_error = 0

    for sample in dataset:
        truth_counts = _count_occurrences(sample["ground_truth"])
        pred_counts = _count_occurrences(sample["predictions"])
        counting_error += sum((pred_counts - truth_counts).values()) - sum((truth_counts - pred_counts).values())
        all_labels = set(truth_counts) | set(pred_counts)
        for label in all_labels:
            tp = min(truth_counts.get(label, 0), pred_counts.get(label, 0))
            fp = max(pred_counts.get(label, 0) - truth_counts.get(label, 0), 0)
            fn = max(truth_counts.get(label, 0) - pred_counts.get(label, 0), 0)
            total_tp += tp
            total_fp += fp
            total_fn += fn
            totals = per_class_totals.setdefault(label, {"tp": 0, "fp": 0, "fn": 0})
            totals["tp"] += tp
            totals["fp"] += fp
            totals["fn"] += fn

    precision = total_tp / (total_tp + total_fp) if total_tp + total_fp else 0.0
    recall = total_tp / (total_tp + total_fn) if total_tp + total_fn else 0.0

    per_class_metrics: Dict[str, Tuple[float, float]] = {}
    for label, totals in per_class_totals.items():
        precision_val = totals["tp"] / (totals["tp"] + totals["fp"]) if totals["tp"] + totals["fp"] else 0.0
        recall_val = totals["tp"] / (totals["tp"] + totals["fn"]) if totals["tp"] + totals["fn"] else 0.0
        per_class_metrics[label] = (precision_val, recall_val)

    return EvaluationResult(
        precision=precision,
        recall=recall,
        counting_error=counting_error,
        per_class=per_class_metrics,
    )
