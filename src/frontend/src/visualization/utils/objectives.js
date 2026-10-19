export const OBJECTIVES = [
  { id: 1, label: "Total package value", description: "Maximize the total value of loaded packages." },
  { id: 2, label: "Loaded package count", description: "Maximize the number of loaded packages." },
  { id: 3, label: "Loaded package volume", description: "Maximize the total volume of loaded packages." },
  { id: 4, label: "Value per loaded volume", description: "Maximize total loaded value divided by total loaded volume." },
];

export function selectedObjective(experiment) {
  const number = Number(experiment.objective_number ?? experiment.metrics?.objective_number ?? 1);
  return OBJECTIVES.find((objective) => objective.id === number) || OBJECTIVES[0];
}

export function formatObjective(value) {
  return value == null ? "—" : new Intl.NumberFormat("en-US", { maximumFractionDigits: 3 }).format(value);
}
