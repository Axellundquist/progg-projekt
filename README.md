# progg-projekt

Workflow guide for collecting and managing a shelf-object detection dataset.

## Quickstart
1. Read `docs/dataset_plan.md` for collection, labeling, and storage standards.
2. Keep raw photos under `data/raw/<source>/<date>/` with accompanying metadata.
3. After labeling in CVAT/Label Studio, export YOLO-format data to `dataset/yolo/`.
4. Run the splitter to create train/val/test folders:
   ```bash
   python scripts/split_dataset.py --input dataset/yolo --output data/dataset-v0.1 --train 0.7 --val 0.2 --seed 42
   ```
5. Export COCO annotations using the same split indices and upload each dataset version to your bucket or `data/dataset-v*/` folder.

## Repository layout (proposed)
- `docs/` – Planning and operational docs.
- `scripts/` – Automation helpers (e.g., dataset splitting).
- `data/` – Raw captures and versioned datasets (add to .gitignore or store samples only if the full set is large).
