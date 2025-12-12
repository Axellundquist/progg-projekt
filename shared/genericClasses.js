export const genericClasses = [
  {
    id: "bottle",
    label: "Bottle",
    description: "Rigid container such as plastic or glass bottles."
  },
  {
    id: "can",
    label: "Can",
    description: "Metal or composite cans for beverages or food."
  },
  {
    id: "box_carton",
    label: "Box / Carton",
    description: "Paperboard or corrugated boxes and cartons."
  },
  {
    id: "bag_pouch",
    label: "Bag / Pouch",
    description: "Flexible packaging like bags, pouches, or sachets."
  },
  {
    id: "cup",
    label: "Cup",
    description: "Single-serve cups, often for drinks or yogurt."
  },
  {
    id: "lid",
    label: "Lid",
    description: "Lids or caps that seal containers."
  },
  {
    id: "utensil",
    label: "Utensil",
    description: "Cutlery such as forks, spoons, or knives."
  },
  {
    id: "tray_plate",
    label: "Tray / Plate",
    description: "Flat serving items like trays or plates."
  }
];

export const genericClassMap = Object.freeze(
  genericClasses.reduce((map, entry) => {
    map[entry.id] = {
      label: entry.label,
      description: entry.description
    };
    return map;
  }, {})
);
