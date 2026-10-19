const OBJECTIVE_COLOR = "#ff9a3c";
const SECONDARY_COLOR = "#8fb9e8";

function runningBest(values = []) {
  let best = -Infinity;
  return values.map((value) => {
    if (!Number.isFinite(value)) return null;
    best = Math.max(best, value);
    return best;
  });
}

export function objectiveChart(experiment) {
  const metrics = experiment.metrics || {};
  if (experiment.algorithm === "Genetic Algorithm") {
    return {
      title: "Population fitness",
      xLabel: "Iteration (generation)",
      yLabel: "Objective value",
      series: [
        { label: "Maximum", color: "#92bf79", values: metrics.maximum_fitness_history ?? experiment.objective_history },
        { label: "Average", color: SECONDARY_COLOR, dashed: true, values: metrics.average_fitness_history },
      ],
      note: !metrics.average_fitness_history?.length ? "Average fitness history is unavailable for this run." : null,
    };
  }
  if (experiment.algorithm === "Simulated Annealing") {
    return {
      title: "Objective over iterations",
      xLabel: "Iteration",
      yLabel: "Objective value",
      series: [
        { label: "Current state", color: OBJECTIVE_COLOR, values: metrics.current_objective_history },
        { label: "Best so far", color: SECONDARY_COLOR, dashed: true, values: metrics.best_objective_history ?? runningBest(experiment.objective_history) },
      ],
      note: !metrics.current_objective_history?.length ? "Current-state objective history is unavailable for this run." : null,
    };
  }
  if (experiment.algorithm === "Hill Climbing - Random Restart") {
    const hasRawHistory = Array.isArray(metrics.objective_history_iterations);
    const runs = (metrics.iterations_per_restart || []).flatMap((count, run) => Array(count + 1).fill(run + 1));
    return {
      title: "Objective over iterations",
      xLabel: "Climbing iteration",
      yLabel: "Objective value",
      description: "Each restart starts at the preceding run's iteration count. Only climbing steps advance the count.",
      series: [{
        label: hasRawHistory ? "Search state" : "Best so far",
        color: OBJECTIVE_COLOR,
        values: experiment.objective_history,
        iterations: metrics.objective_history_iterations,
        runs,
      }],
      note: hasRawHistory ? null : "This saved run contains best-so-far history. Rerun it to record the values visited across restarts.",
    };
  }
  return {
    title: "Objective over iterations",
    xLabel: "Iteration",
    yLabel: "Objective value",
    series: [{ label: "Objective", color: OBJECTIVE_COLOR, values: experiment.objective_history }],
  };
}

export function probabilityChart(experiment) {
  return {
    title: "SA acceptance probability",
    xLabel: "Iteration",
    yLabel: "Probability",
    domain: [0, 1],
    description: "Non-worse proposals have probability 1. Worse proposals use exp(ΔE / T).",
    emptyMessage: "Acceptance-probability history is unavailable for this run.",
    series: [{
      label: "Acceptance probability",
      color: "#c5a0ef",
      startIteration: 1,
      values: experiment.metrics?.acceptance_probability_history,
    }],
  };
}

export function chartData(chart) {
  let minimum = Infinity;
  let maximum = -Infinity;
  let firstIteration = Infinity;
  let lastIteration = -Infinity;
  const series = chart.series.map((item) => {
    const points = (Array.isArray(item.values) ? item.values : []).map((value, index) => {
      const parsed = typeof value === "number" || (typeof value === "string" && value.trim() !== "") ? Number(value) : NaN;
      const iteration = item.iterations ? item.iterations[index] : index + (item.startIteration ?? 0);
      const point = { iteration, value: parsed };
      if (item.runs?.[index] !== undefined) point.run = item.runs[index];
      if (!Number.isFinite(parsed) || !Number.isInteger(iteration) || iteration < 0) return { ...point, value: null };
      minimum = Math.min(minimum, parsed);
      maximum = Math.max(maximum, parsed);
      firstIteration = Math.min(firstIteration, iteration);
      lastIteration = Math.max(lastIteration, iteration);
      return point;
    });
    return { ...item, points };
  }).filter((item) => item.points.some((point) => point.value !== null));
  if (!series.length) return null;
  if (chart.domain) {
    [minimum, maximum] = chart.domain;
  } else if (minimum === maximum) {
    const padding = Math.abs(minimum) * 0.05 || 1;
    minimum -= padding;
    maximum += padding;
  }
  return { series, minimum, maximum, firstIteration, lastIteration };
}
