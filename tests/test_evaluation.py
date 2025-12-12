import json
from pathlib import Path

from app.evaluation import EvaluationItem, evaluate_dataset


def test_evaluation_metrics_compute_precision_recall_and_counting_error():
    data_path = Path(__file__).parent / "testsdata" / "eval.json"
    raw_items = json.loads(data_path.read_text())
    items = [EvaluationItem(**item) for item in raw_items]

    result = evaluate_dataset(items)

    assert round(result.precision, 2) == 0.8
    assert round(result.recall, 2) == 0.8
    assert round(result.counting_error, 2) == 0.5
