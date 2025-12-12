# Retail Vision Improvements

This document captures the plan to address per-brand labeling, robust fine-tuning with challenging conditions, lightweight multi-frame tracking, and a continuous feedback loop for relabeling and retraining.

## 1) Per-brand labels and fine-tuning with occlusions/glare

### Label schema
- **Object class = product instance**, **attribute = brand**. Each bounding box carries a `brand` tag (e.g., `Brand=A`, `Brand=B`).
- Preserve a generic `product` class for fallback detection while encouraging per-brand classifiers.
- Encode unclear brand cases as `Brand=unknown` to keep recall without polluting brand-specific precision.

### Dataset curation
- **Balanced sampling**: ensure every brand has a minimum number of examples per lighting/angle bucket; oversample rare brands with augmentation.
- **Hard-case mining**: actively collect frames with occlusions, reflections, and motion blur; prioritize these in validation to monitor robustness.
- **Resolution policy**: keep native resolution for training crops; avoid aggressive resizing that erases brand cues.

### Labeling guidelines
- Box the **full visible extent** of the product, even if partially occluded.
- If two products overlap, label both independently; note heavy occlusion (>60%) with a `occluded=true` attribute to weight losses.
- For glare, still draw the box; set `glare=true` attribute when reflections cover key brand areas.

### Model and training changes
- Base detector: continue with a single-stage model (e.g., YOLOv8n/s) with brand classification head.
- **Loss weighting**: increase weight for underrepresented brands and for samples marked `occluded`/`glare` to improve recall on hard cases.
- **Augmentations tuned for realism**:
  - `Cutout`/`RandomErasing` to mimic occlusion; limit area to <35% to avoid destroying small items.
  - `ColorJitter` + `RandomBrightnessContrast` for glare and lighting variance.
  - Mild `MotionBlur` and `GaussianNoise` for shaky cams.
- **Validation split**: dedicate a “hard-set” containing only occlusion/glare examples; track mAP per brand on both normal and hard sets.
- **Fine-tuning schedule**: cosine LR for 50–100 epochs, mixed-precision, batch-size tuned to GPU; early stop on plateau of hard-set mAP.

### Evaluation
- Report **per-brand mAP@50/95** plus recall on the hard-set.
- Maintain a confusion matrix for brands; flag brands with >5% confusion for targeted data collection.

## 2) Lightweight tracking across frames

Goal: avoid double-counting the same product across adjacent frames.

### Approach
- Use a **SORT-style tracker** (IoU matching + Kalman filter on box center/size) to assign stable track IDs without heavy re-ID.
- Run detector every frame (or every N frames with linear interpolation for skipped frames on low-power devices).
- Apply a **time-decay**: tracks expire after `max_age` (e.g., 10 frames) without matches.

### Matching logic
1. For each frame, obtain detections `(bbox, brand, score)`.
2. Predict all active tracks with Kalman filter.
3. Compute IoU matrix between predicted tracks and detections; match with Hungarian algorithm using IoU threshold (e.g., 0.3–0.5).
4. Update matched tracks; initialize new tracks for unmatched detections; drop stale tracks.
5. Maintain **per-track brand consistency** by majority vote of observed brand labels; if conflicting, mark as `brand=ambiguous` to avoid false counts.

### Counting rule
- Count a product once per track lifetime; only count when the track is confirmed (e.g., matched in 2 consecutive frames).
- If the same product re-enters after `max_age`, it will be recounted, which aligns with leaving/entering the scene semantics.

## 3) Feedback loop for relabeling and periodic retraining

### Data capture
- Persist raw frames and detection outputs with track IDs and brand hypotheses.
- Tag frames with operational metadata (store ID, camera ID, timestamp) for targeted audits.

### Error mining
- **False positives**: detections with low confidence over time or user-flagged boxes; collect with crops and context frames.
- **False negatives**: use sudden track drops, inventory mismatches, or user flags when an item is missed.
- **Brand confusion**: tracks where brand majority flips or confidence remains low.

### Human-in-the-loop relabeling
- Send mined crops to a labeling queue with pre-filled boxes and brand suggestions to speed review.
- Enforce QC: dual review on uncertain (`occluded`/`glare`) samples; spot-check 10% of routine cases.

### Retraining cadence
- Run a **weekly incremental fine-tune** on newly labeled data mixed with a stable reference set to avoid drift.
- Promote a model only if it improves both overall and hard-set metrics; otherwise, roll back.
- Archive training configs and metrics per run; surface a dashboard showing per-brand performance and recent regressions.

### Deployment safeguards
- **Shadow deploy** new models to mirror traffic and compare counts/precision before full rollout.
- Keep the tracker parameters versioned alongside model versions to ensure reproducibility.

## Deliverables
- Updated label schema and guidelines for annotators.
- Training pipeline config supporting per-brand heads, hard-case weighting, and occlusion/glare augmentations.
- Lightweight SORT-style tracker integrated into the inference loop with per-track brand voting and count de-duplication.
- Feedback system that mines errors, routes them for relabeling, and triggers periodic fine-tunes with promotion gates.
