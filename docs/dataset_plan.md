# Shelf Dataset Collection Plan

This plan outlines how to gather ~200–500 shelf images, label target items, export labels in YOLO/COCO format, and store a versioned dataset split into train/val/test.

## 1. Target definition
- **Scenes:** Grocery or retail shelves with varied lighting, clutter, occlusion, distance, camera height, and angles.
- **Objects to detect:** Define 3–6 classes (e.g., cereal_box, soda_can, snack_bag, bottle, cleaning_spray). Keep class list stable once labeling begins.
- **Image resolution:** Prefer ≥1080p photos; avoid heavy compression.

## 2. Collection guidelines (200–500 images)
- Capture both **real photos** and **publicly available images** (license-permitting). Aim for at least 30% from each source.
- Vary conditions:
  - Lighting: daylight, fluorescent, shadowed, backlit.
  - Shelf fullness: sparse, normal, overstocked, front-facing vs. misaligned items.
  - Distance/angle: close-ups, mid-range aisle shots, tilted/oblique angles.
  - Obstructions: partial occlusion by hands/other items.
- Avoid near-duplicates: take 2–3 shots per scene with noticeable changes.
- Store raw photos at `data/raw/<source>/<collection_date>/` to preserve originals.

## 3. Consent and metadata
- Capture only shelves/products—no people or private info.
- Record metadata (CSV or JSON): `image_path, source, location_type, lighting, distance, angle, notes, photographer`. Keep alongside raw images in `data/raw/metadata.csv`.

## 4. Labeling workflow
1. **Tool:** Use Label Studio or CVAT with bounding-box tasks.
2. **Class map:** Maintain `dataset/classes.txt` (YOLO order) and `dataset/classes.json` (for COCO name/id mapping).
3. **Labeling rules:**
   - Box tight to item edges; include full visible extent even if occluded.
   - For occluded items, box the visible portion only.
   - Skip items below 20px height/width.
   - Mark partially visible items normally (no separate flag needed for YOLO/COCO).
4. **Quality checks:**
   - Run a peer review on 10% of labels.
   - Spot-check class confusion after the first 50 images and adjust guidelines if necessary.

## 5. Export formats
- **YOLOv5/YOLOv8:** Export as `dataset/yolo/` with structure:
  - `images/{train,val,test}/...`
  - `labels/{train,val,test}/...` (each label file mirrors the image stem).
- **COCO:** Export `dataset/coco/annotations/{train,val,test}.json` with images in `dataset/coco/images/{split}/`.
- Keep a `dataset/data.yaml` describing YOLO classes and paths for training.

## 6. Splitting strategy
- Target split: **70% train / 20% val / 10% test**, stratified by class presence where possible.
- Keep all images from the same scene together to avoid leakage.
- Use `scripts/split_dataset.py` (see below) on YOLO-format folders to create the split lists; export COCO using the same split indices.

## 7. Versioned storage layout (repo/bucket)
```
├── data
│   ├── raw/                   # immutable originals + metadata
│   └── dataset-
│       ├── v0.1/              # first labeled drop
│       ├── v0.2/              # subsequent iterations
│       └── latest -> v0.2     # convenience symlink
```
- Each version folder contains `yolo/`, `coco/`, and `classes` files.
- Track checksum manifest (`manifest.sha256`) for integrity.
- Sync to object storage (e.g., `s3://<bucket>/shelves-dataset/`) using version folders. Keep repo copy small by storing sample or symlink pointers if full dataset is large.

## 8. Automation checklist
- [ ] Collect 200–500 images following section 2.
- [ ] Fill metadata CSV/JSON.
- [ ] Label with CVAT/Label Studio; export YOLO + COCO.
- [ ] Run `scripts/split_dataset.py` to create split directories.
- [ ] Generate `data.yaml` and `manifest.sha256`.
- [ ] Upload to versioned bucket folder and update `latest` symlink.

## 9. Next steps
- After the first labeling round, run a small training experiment to validate label quality and adjust class definitions if needed.
