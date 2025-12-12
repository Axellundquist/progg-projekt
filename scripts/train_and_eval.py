"""Train and evaluate a small YOLO model with lightweight augmentations.

This script uses the Ultralytics YOLO API to fine-tune a small detection
model with GPU acceleration (when available), logs training metrics to the
standard Ultralytics run directory, and performs a counting-accuracy
assessment with latency measurements on the validation split.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Dict, Iterable, List

import yaml
from ultralytics import YOLO
from ultralytics.utils.checks import check_yaml


def _load_data_config(data_path: str | Path) -> Dict:
    """Load a YOLO data YAML file.

    The configuration is expected to include train/val/test split entries. The
    path is resolved relative to the working directory.
    """

    resolved_path = Path(check_yaml(data_path))

    with resolved_path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _list_images(split_path: Path) -> List[Path]:
    """Collect image files from a split directory or a text file listing images."""

    if split_path.is_dir():
        return sorted(
            p
            for p in split_path.rglob("*")
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}
        )

    if split_path.is_file() and split_path.suffix.lower() == ".txt":
        with split_path.open("r", encoding="utf-8") as handle:
            return [Path(line.strip()) for line in handle if line.strip()]

    raise ValueError(f"Unsupported split path: {split_path}")


def _label_path_for_image(image_path: Path) -> Path:
    """Infer the YOLO label file path for a given image."""

    if "images" not in image_path.parts:
        # Assume labels live next to the image if we cannot swap directories.
        return image_path.with_suffix(".txt")

    parts = list(image_path.parts)
    images_index = parts.index("images")
    parts[images_index] = "labels"
    return Path(*parts).with_suffix(".txt")


def _count_labels(label_path: Path) -> int:
    """Count the number of objects annotated in a label file."""

    if not label_path.exists():
        return 0

    with label_path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def evaluate_counting_accuracy(
    model: YOLO,
    val_images: Iterable[Path],
    imgsz: int,
    device: str,
    limit: int,
) -> Dict:
    """Evaluate counting accuracy and latency on a subset of validation images."""

    latencies: List[float] = []
    relative_errors: List[float] = []

    for idx, image_path in enumerate(val_images):
        if limit and idx >= limit:
            break

        start = time.perf_counter()
        results = model.predict(
            source=str(image_path),
            imgsz=imgsz,
            device=device,
            verbose=False,
        )
        latencies.append(time.perf_counter() - start)

        pred_count = sum(len(r.boxes) for r in results)
        true_count = _count_labels(_label_path_for_image(image_path))
        denom = max(true_count, 1)
        relative_errors.append(abs(pred_count - true_count) / denom)

    if not latencies:
        raise RuntimeError("No validation images found for counting evaluation.")

    mean_latency = sum(latencies) / len(latencies)
    mean_relative_error = sum(relative_errors) / len(relative_errors)
    counting_accuracy = 1.0 - mean_relative_error

    return {
        "mean_latency_sec": mean_latency,
        "counting_accuracy": counting_accuracy,
        "evaluated_images": min(len(val_images), limit or len(val_images)),
    }


def run_training(args: argparse.Namespace) -> Path:
    """Train a YOLO model with light augmentations and return the run directory."""

    model = YOLO(args.model)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.run_name,
        save=True,
        save_period=args.save_period,
        lr0=args.lr0,
        degrees=5.0,
        fliplr=0.5,
        flipud=0.1,
        hsv_v=0.2,
        translate=0.1,
        scale=0.5,
    )

    if getattr(model, "trainer", None) and getattr(model.trainer, "save_dir", None):
        return Path(model.trainer.save_dir)

    # Fallback to the default project/name layout if the trainer is unavailable.
    return Path(args.project) / args.run_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data",
        type=str,
        default="coco128.yaml",
        help="Path to the YOLO data YAML file.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n.pt",
        help="Base model checkpoint to fine-tune.",
    )
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs.")
    parser.add_argument("--batch", type=int, default=16, help="Batch size for training.")
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Image size for training and evaluation.",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="0",
        help="Compute device (e.g., '0' for first GPU or 'cpu').",
    )
    parser.add_argument(
        "--project",
        type=str,
        default="runs",
        help="Directory to store training runs and checkpoints.",
    )
    parser.add_argument(
        "--run-name",
        type=str,
        default="yolo-small",
        help="Name of the training run directory.",
    )
    parser.add_argument(
        "--save-period",
        type=int,
        default=1,
        help="Checkpoint saving interval in epochs.",
    )
    parser.add_argument(
        "--lr0",
        type=float,
        default=0.01,
        help="Initial learning rate.",
    )
    parser.add_argument(
        "--eval-limit",
        type=int,
        default=50,
        help="Limit on the number of validation images for counting evaluation (0 for all).",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = run_training(args)

    best_checkpoint = run_dir / "weights" / "best.pt"
    best_model = YOLO(str(best_checkpoint)) if best_checkpoint.exists() else YOLO(args.model)

    val_results = best_model.val(data=args.data, imgsz=args.imgsz, device=args.device, split="val")
    metrics = getattr(val_results, "results_dict", {}) or {}

    data_cfg = _load_data_config(args.data)
    dataset_root = Path(data_cfg.get("path", "")) if data_cfg.get("path") else None

    val_split = Path(data_cfg.get("val"))
    if dataset_root and not val_split.is_absolute():
        val_split = dataset_root / val_split

    val_images = _list_images(val_split)

    counting = evaluate_counting_accuracy(
        model=best_model,
        val_images=val_images,
        imgsz=args.imgsz,
        device=args.device,
        limit=args.eval_limit,
    )

    report = {
        "training_run": str(run_dir),
        "val_metrics": metrics,
        "counting": counting,
    }

    report_path = Path(run_dir) / "evaluation_metrics.json"
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)

    print(f"Saved metrics to {report_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
