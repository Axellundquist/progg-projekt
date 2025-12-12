# YOLO Detection Service

A lightweight FastAPI service exposing a `/detect` endpoint for running object detection with a pre-trained YOLO model on images or sampled video frames.

## Getting started

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The API root returns a short status payload. Use the `/detect` endpoint with multipart form uploads.

## `/detect` endpoint

* **Image upload**: send a single image file. The service returns detected bounding boxes, labels, confidences, and per-frame counts.
* **Video upload**: send a video file and optionally `sample_n` (default `5`) to control the number of frames to sample evenly from the video. The response includes detections per sampled frame, aggregate counts across frames, and the frame stride used.

Example cURL request for an image:

```bash
curl -X POST \
  -F "file=@example.jpg" \
  http://localhost:8000/detect
```

Example cURL request for a video with 8 frame samples:

```bash
curl -X POST \
  -F "file=@clip.mp4" \
  -F "sample_n=8" \
  http://localhost:8000/detect
```
