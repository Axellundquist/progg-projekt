# Visual Item Detector

A lightweight single-page workflow for uploading an image, selecting item classes, running a mock detection pass, and exporting results.

## Usage
1. Open `index.html` in your browser.
2. Upload an image by dragging it into the drop zone or using the file picker.
3. Choose the item types to include and click **Detect items**.
4. View the annotated image, per-class and total counts, and export detections as JSON.
5. Update the selected classes and re-run detection without reuploading the image. Retry if the simulated network call fails.
