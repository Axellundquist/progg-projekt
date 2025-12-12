#!/usr/bin/env python3
"""Split a YOLO-format dataset into train/val/test folders.

Usage:
    python scripts/split_dataset.py --input dataset/yolo --output data/dataset-v0.1 --train 0.7 --val 0.2 --seed 42

Notes:
- Preserves scene grouping if images share a prefix before the first underscore (e.g., scene1_0001.jpg).
- Works on existing YOLO layout `images/` + `labels/`.
- Copying is avoided; files are symlinked to keep storage small. Use `--copy` to duplicate instead.
"""

from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split YOLO dataset into train/val/test")
    parser.add_argument("--input", required=True, type=Path, help="Path with images/ and labels/")
    parser.add_argument("--output", required=True, type=Path, help="Destination root for split dataset")
    parser.add_argument("--train", type=float, default=0.7, help="Train proportion")
    parser.add_argument("--val", type=float, default=0.2, help="Validation proportion")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--copy", action="store_true", help="Copy instead of symlink")
    return parser.parse_args()


def group_images(images: list[Path]) -> list[list[Path]]:
    scenes: dict[str, list[Path]] = {}
    for img in images:
        key = img.stem.split("_")[0] if "_" in img.stem else img.stem
        scenes.setdefault(key, []).append(img)
    return list(scenes.values())


def choose_split(groups: list[list[Path]], train_p: float, val_p: float) -> dict[str, list[Path]]:
    random.shuffle(groups)
    total = sum(len(g) for g in groups)
    train_target = int(total * train_p)
    val_target = int(total * val_p)

    splits = {"train": [], "val": [], "test": []}
    counts = {"train": 0, "val": 0, "test": 0}

    for group in groups:
        # Greedy assignment trying to hit targets without splitting scenes
        if counts["train"] < train_target:
            dest = "train"
        elif counts["val"] < val_target:
            dest = "val"
        else:
            dest = "test"
        splits[dest].extend(group)
        counts[dest] += len(group)

    return splits


def ensure_dirs(output: Path) -> None:
    for split in ("train", "val", "test"):
        (output / "images" / split).mkdir(parents=True, exist_ok=True)
        (output / "labels" / split).mkdir(parents=True, exist_ok=True)


def link_or_copy(src: Path, dst: Path, copy: bool) -> None:
    if dst.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if copy:
        shutil.copy2(src, dst)
    else:
        dst.symlink_to(src.resolve())


def split_dataset(input_root: Path, output_root: Path, train_p: float, val_p: float, seed: int, copy: bool) -> None:
    random.seed(seed)
    images = sorted((input_root / "images").rglob("*.jpg")) + sorted((input_root / "images").rglob("*.png"))
    if not images:
        raise SystemExit(f"No images found in {input_root / 'images'}")

    groups = group_images(images)
    splits = choose_split(groups, train_p, val_p)
    ensure_dirs(output_root)

    for split, imgs in splits.items():
        for img in imgs:
            rel_img = img.relative_to(input_root / "images")
            label = (input_root / "labels" / rel_img).with_suffix(".txt")
            if not label.exists():
                raise SystemExit(f"Missing label for {img}")

            link_or_copy(img, output_root / "images" / split / rel_img, copy)
            link_or_copy(label, output_root / "labels" / split / rel_img.with_suffix(".txt"), copy)

    print(f"Split complete: train={len(splits['train'])}, val={len(splits['val'])}, test={len(splits['test'])}")


def main() -> None:
    args = parse_args()
    if args.train + args.val >= 1.0:
        raise SystemExit("Train + val must be < 1.0 to leave room for test")
    split_dataset(args.input, args.output, args.train, args.val, args.seed, args.copy)


if __name__ == "__main__":
    main()
