"""Shared target definitions for the demo UI and placeholder model."""

from pydantic import BaseModel


class TargetClass(BaseModel):
    value: str
    label: str
    help_text: str


GENERIC_CLASSES: list[TargetClass] = [
    TargetClass(value="bottle", label="Bottle", help_text="Plastic or glass bottles of any size."),
    TargetClass(value="can", label="Can", help_text="Aluminum or steel cans for beverages or food."),
    TargetClass(value="box_carton", label="Box / Carton", help_text="Cardboard boxes, cartons, or tetrapaks."),
    TargetClass(value="bag_pouch", label="Bag / Pouch", help_text="Flexible bags, pouches, or sachets."),
    TargetClass(value="cup", label="Cup", help_text="Disposable or reusable cups."),
    TargetClass(value="lid", label="Lid", help_text="Plastic or paper lids and tops."),
    TargetClass(value="utensil", label="Utensil", help_text="Single-use or reusable utensils."),
    TargetClass(value="tray_plate", label="Tray / Plate", help_text="Serving trays, clamshells, or plates."),
]

DEFAULT_TARGET_VALUES: list[str] = ["bottle", "can", "box_carton"]
