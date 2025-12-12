"""Maintain generic class definitions and model index mapping."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "generic_classes.json"


@dataclass(frozen=True)
class GenericClass:
    """Represents a generic packaging class shared between UI and model."""

    id: str
    label: str
    help: str


def load_classes(path: Path = DATA_PATH) -> List[GenericClass]:
    """Load generic classes from the shared JSON definition."""

    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return [GenericClass(**item) for item in raw]


def build_index_map(classes: Iterable[GenericClass]) -> Dict[str, int]:
    """Create a stable mapping from class identifier to model index."""

    return {item.id: idx for idx, item in enumerate(classes)}


GENERIC_CLASSES = load_classes()
CLASS_TO_INDEX = build_index_map(GENERIC_CLASSES)


if __name__ == "__main__":
    for cls in GENERIC_CLASSES:
        print(f"{cls.id:12s} -> {cls.label}")
    print("\nModel index map:")
    for key, idx in CLASS_TO_INDEX.items():
        print(f"  {key}: {idx}")
