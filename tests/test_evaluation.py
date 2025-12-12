import json
from pathlib import Path

from service.evaluation import evaluate_dataset


def test_evaluation_metrics_cover_precision_recall_and_counting_error():
    dataset_path = Path(__file__).parent / "data" / "dataset.json"
    dataset = json.loads(dataset_path.read_text())

    result = evaluate_dataset(dataset)

    assert 0 < result.precision <= 1
    assert 0 < result.recall <= 1
    # counting error should reflect over/under counts
    assert result.counting_error == 0
    # ensure per-class metrics present
    assert set(result.per_class.keys()) == {"red", "blue", "green"}
    red_precision, red_recall = result.per_class["red"]
    assert red_precision == 1.0
    assert red_recall == 1.0
