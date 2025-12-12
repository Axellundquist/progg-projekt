from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List, Sequence


@dataclass
class EvaluationItem:
    ground_truth: List[str]
    predictions: List[str]


@dataclass
class EvaluationResult:
    precision: float
    recall: float
    counting_error: float


def calculate_counts(labels: Iterable[str]) -> Counter:
    return Counter(labels)


def evaluate_dataset(items: Sequence[EvaluationItem]) -> EvaluationResult:
    tp = 0
    fp = 0
    fn = 0
    counting_errors: List[int] = []

    for item in items:
        gt_counts = calculate_counts(item.ground_truth)
        pred_counts = calculate_counts(item.predictions)

        for label in pred_counts:
            tp += min(pred_counts[label], gt_counts.get(label, 0))
            fp += max(pred_counts[label] - gt_counts.get(label, 0), 0)

        for label in gt_counts:
            if gt_counts[label] > pred_counts.get(label, 0):
                fn += gt_counts[label] - pred_counts.get(label, 0)

        for label in set(gt_counts.keys()) | set(pred_counts.keys()):
            counting_errors.append(abs(gt_counts.get(label, 0) - pred_counts.get(label, 0)))

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    avg_count_error = sum(counting_errors) / len(counting_errors) if counting_errors else 0.0

    return EvaluationResult(precision=precision, recall=recall, counting_error=avg_count_error)
