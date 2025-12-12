# progg-projekt

This repository demonstrates a shared configuration for generic packaging classes used by both a backend mapping helper and a small frontend selector.

## Generic classes
The list lives in `data/generic_classes.json` and contains the following entries:
- bottle
- can
- box/carton
- bag/pouch
- cup
- lid
- utensil
- tray/plate

Each entry includes a user-friendly label and help text. The backend builds a model index map from this file, and the frontend loads the same data to render multi-select chips and a dropdown.

## Backend helper
Run `python backend/class_map.py` to print the loaded class list and the generated model indices.

## Frontend selector
Open `frontend/index.html` in a browser (or serve the repository root via `python -m http.server`) to try the chip-based selector. The dropdown below the chips provides another way to select classes, and hovering reveals tooltips with the help text. By default, bottle, can, and box/carton are selected.
