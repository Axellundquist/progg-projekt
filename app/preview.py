import base64
import io
from dataclasses import dataclass
from typing import Iterable, List
from PIL import Image, ImageDraw, ImageFont


@dataclass
class Detection:
    label: str
    bbox: tuple
    score: float


class PreviewGenerator:
    def __init__(self, font: ImageFont.ImageFont | None = None) -> None:
        self.font = font or ImageFont.load_default()

    def annotate(self, image_path: str, detections: Iterable[Detection]) -> tuple[str, bytes]:
        image = Image.open(image_path).convert("RGB")
        draw = ImageDraw.Draw(image)

        for det in detections:
            x1, y1, x2, y2 = det.bbox
            draw.rectangle(((x1, y1), (x2, y2)), outline="red", width=2)
            label = f"{det.label} ({det.score:.2f})"
            text_size = draw.textbbox((0, 0), label, font=self.font)
            padding = 2
            draw.rectangle(
                ((x1, y1 - (text_size[3] - text_size[1]) - padding), (x1 + text_size[2], y1)),
                fill="red",
            )
            draw.text((x1, y1 - (text_size[3] - text_size[1]) - padding), label, fill="white", font=self.font)

        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        encoded = base64.b64encode(buffer.read())
        return image_path, encoded
