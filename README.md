# progg-projekt

This repository provides a small YOLO training pipeline tailored for quick GPU fine-tuning with light augmentations (random flip, brightness jitter, and slight rotation).

## Prerequisites
- Python 3.10+
- CUDA-enabled GPU recommended (set `--device 0` to force GPU)
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

## Training and evaluation
The `scripts/train_and_eval.py` script trains a small YOLO model and runs validation with counting accuracy and latency measurements. By default it uses the lightweight `coco128.yaml` dataset definition from Ultralytics.

```bash
python scripts/train_and_eval.py \
  --data coco128.yaml \
  --model yolov8n.pt \
  --epochs 20 \
  --batch 32 \
  --imgsz 640 \
  --device 0 \
  --run-name yolo-small
```

Key behaviors:
- **Augmentations:** random horizontal/vertical flips, brightness jitter (`hsv_v`), and slight rotation (`degrees=5`).
- **Logging:** metrics, tensorboard-ready CSVs, and checkpoints are saved under `runs/<run-name>/` (Ultralytics default layout).
- **Checkpoints:** the best and last weights are stored automatically; set `--save-period` to keep intermediate epochs.
- **Counting metrics:** after training, the script evaluates the validation split, computing object counting accuracy (1 - mean relative error) and mean per-image latency. Results are written to `evaluation_metrics.json` alongside the run artifacts.

You can limit the counting evaluation subset with `--eval-limit` to speed up turnaround during experimentation.
