import { genericClasses } from "../shared/genericClasses.js";

export const GENERIC_CLASS_MAP = new Map(
  genericClasses.map((entry) => [entry.id, { label: entry.label, description: entry.description }])
);

export function getGenericClass(id) {
  return GENERIC_CLASS_MAP.get(id);
}

export function listGenericClasses() {
  return genericClasses;
}
