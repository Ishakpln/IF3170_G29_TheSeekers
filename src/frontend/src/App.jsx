import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import ExperimentPlots, { ObjectiveChart } from "./visualization/components/ui/ExperimentCharts.jsx";
import { OBJECTIVES, formatObjective, selectedObjective } from "./visualization/utils/objectives.js";

const StateVisualization = lazy(() => import("./visualization/StateVisualization.jsx"));


const ALGORITHMS = [
  "Hill Climbing - Steepest-Ascent",
  "Hill Climbing - Stochastic",
  "Hill Climbing - Sideways Move",
  "Hill Climbing - Random Restart",
  "Simulated Annealing",
  "Genetic Algorithm",
];

const LABELS = {
  "Hill Climbing - Steepest-Ascent": "HC-SA",
  "Hill Climbing - Stochastic": "HC-ST",
  "Hill Climbing - Sideways Move": "HC-SW",
  "Hill Climbing - Random Restart": "HC-RR",
  "Simulated Annealing": "SA",
  "Genetic Algorithm": "GA",
};

const DEFAULT_FORM = {
  algorithm: ALGORITHMS[0],
  objective_number: 1,
  experiment_name: "",
  package_count: 30,
  truck_count: 1,
  max_iterations: 1000,
  seed: 42,
  max_sideways: 100,
  max_restarts: 5,
  initial_temperature: 100,
  cooling_rate: 0.99,
  minimum_temperature: 0.01,
  population_size: 20,
};


async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;

    try {
      const body = await response.json();
      message = body.error || message;
    } catch {
      // Keep the HTTP error when the response is not JSON.
    }

    throw new Error(message);
  }

  if (response.status === 204) return null;
  return response.json();
}


function downloadJson(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}


function ResultCard({ experiment, onDetails }) {
  const pending = experiment.status === "pending";
  const failed = experiment.status === "failed";
  const objective = selectedObjective(experiment);
  const delta =
    experiment.best_value == null || experiment.initial_value == null
      ? null
      : experiment.best_value - experiment.initial_value;

  return (
    <article className={`result-card status-${experiment.status}`}>
      <header className="card-header">
        <div>
          <h2>{LABELS[experiment.algorithm] || experiment.algorithm}</h2>
          <p title={experiment.experiment_name}>{experiment.experiment_name}</p>
        </div>
        <div className="card-badges">
          {experiment.saved && <span className="saved-badge">saved</span>}
          <span className={`status-badge ${experiment.status}`}>
            {experiment.status}
          </span>
        </div>
      </header>

      {pending ? (
        <div className="pending-content">
          <span className="spinner" />
          <strong>Experiment is running</strong>
          <p>You can start and monitor other experiments while this job runs.</p>
        </div>
      ) : failed ? (
        <div className="failed-content">
          <strong>Experiment failed</strong>
          <p>{experiment.error}</p>
        </div>
      ) : (
        <>
          <div className="card-content">
            <div className="objective-summary">
              <span title={objective.description}>Best {objective.label.toLowerCase()}</span>
              <strong title={String(experiment.best_value)}>{formatObjective(experiment.best_value)}</strong>
              <small className={delta >= 0 ? "positive" : "negative"}>
                {delta >= 0 ? "+" : ""}
                {formatObjective(delta)} from initial
              </small>
            </div>
            <ObjectiveChart experiment={experiment} compact />
          </div>
          <div className="card-metrics">
            <div><span>Iterations</span><strong>{experiment.iterations}</strong></div>
            <div>
              <span>Runtime</span>
              <strong>{Number(experiment.execution_time || 0).toFixed(3)}s</strong>
            </div>
            <div><span>Seed</span><strong>{experiment.seed}</strong></div>
          </div>
        </>
      )}

      <button
        className="details-button"
        disabled={pending}
        onClick={() => onDetails(experiment.id)}
      >
        View details ↗
      </button>
    </article>
  );
}


function ExperimentForm({ onClose, onCreated }) {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  function update(event) {
    const { name, value, type } = event.target;
    setForm((current) => ({
      ...current,
      [name]: type === "number" || name === "objective_number" ? Number(value) : value,
    }));
  }

  async function submit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");

    try {
      const created = await api("/api/experiments", {
        method: "POST",
        body: JSON.stringify(form),
      });
      onCreated(created);
    } catch (requestError) {
      setError(requestError.message);
      setSubmitting(false);
    }
  }

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <form className="modal experiment-modal" onSubmit={submit} onMouseDown={(event) => event.stopPropagation()}>
        <header className="modal-header">
          <div><span>NEW JOB</span><h2>Run experiment</h2></div>
          <button type="button" onClick={onClose}>×</button>
        </header>

        <label className="field field-wide">
          <span>Algorithm</span>
          <select name="algorithm" value={form.algorithm} onChange={update}>
            {ALGORITHMS.map((algorithm) => <option key={algorithm}>{algorithm}</option>)}
          </select>
        </label>

        <label className="field field-wide">
          <span>Objective function</span>
          <select name="objective_number" value={form.objective_number} onChange={update}>
            {OBJECTIVES.map((objective) => <option key={objective.id} value={objective.id}>{objective.label}</option>)}
          </select>
          <small className="field-description">{selectedObjective(form).description}</small>
        </label>

        <div className="form-grid">
          <label className="field field-wide">
            <span>Experiment name</span>
            <input name="experiment_name" value={form.experiment_name} onChange={update} placeholder="Optional label" />
          </label>
          <NumberField label="Package count" name="package_count" value={form.package_count} min="1" onChange={update} />
          <NumberField label="Truck count" name="truck_count" value={form.truck_count} min="1" onChange={update} />
          <NumberField label="Maximum iterations" name="max_iterations" value={form.max_iterations} min="1" onChange={update} />
          <NumberField label="Random seed" name="seed" value={form.seed} min="0" onChange={update} />

          {form.algorithm === "Hill Climbing - Sideways Move" && (
            <NumberField label="Maximum sideways" name="max_sideways" value={form.max_sideways} min="0" onChange={update} />
          )}
          {form.algorithm === "Hill Climbing - Random Restart" && (
            <NumberField label="Maximum restarts" name="max_restarts" value={form.max_restarts} min="0" onChange={update} />
          )}
          {form.algorithm === "Genetic Algorithm" && (
            <NumberField label="Population size" name="population_size" value={form.population_size} min="2" onChange={update} />
          )}
          {form.algorithm === "Simulated Annealing" && (
            <>
              <NumberField label="Initial temperature" name="initial_temperature" value={form.initial_temperature} min="0.01" step="0.01" onChange={update} />
              <NumberField label="Cooling rate" name="cooling_rate" value={form.cooling_rate} min="0.001" max="0.999" step="0.001" onChange={update} />
              <NumberField label="Minimum temperature" name="minimum_temperature" value={form.minimum_temperature} min="0.001" step="0.001" onChange={update} />
            </>
          )}
        </div>

        {error && <p className="form-error">{error}</p>}
        <button className="run-button" disabled={submitting}>
          {submitting ? "Starting…" : "Run experiment"}
        </button>
      </form>
    </div>
  );
}


function NumberField({ label, ...props }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input type="number" {...props} />
    </label>
  );
}


const PARAMETER_LABELS = {
  max_sideways: "Maximum sideways moves",
  max_restarts: "Maximum restarts",
  initial_temperature: "Initial temperature",
  cooling_rate: "Cooling rate",
  minimum_temperature: "Minimum temperature",
  population_size: "Population size",
};

const TERMINATION_COPY = {
  "maximum iterations reached": "The search stopped after reaching the configured iteration limit.",
  "minimum temperature reached": "The search stopped after cooling to the configured minimum temperature.",
  "failed to generate a valid neighbor": "The search stopped because no valid neighboring state could be generated.",
  "telah mencapai iterasi maksimum": "The search stopped after reaching the configured iteration limit.",
  "telah mencapai restart maksimum": "The search completed all configured restart attempts.",
  "telah mencapai sideways move maksimum": "The search stopped after reaching the sideways-move limit.",
  "tidak ada neighbor yang valuenya lebih tinggi": "The search stopped because no better neighboring state was available.",
  "tidak ada neighbor yang valuenya lebih tinggi atau sama": "The search stopped because no equal or better neighboring state was available.",
};

function parameterValue(name, value) {
  if (name === "cooling_rate" && Number.isFinite(Number(value))) {
    return `${formatObjective(Number(value) * 100)}% retained per iteration`;
  }
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") return formatObjective(value);
  return String(value);
}

function OverviewPanel({ experiment }) {
  const objective = selectedObjective(experiment);
  const parameters = Object.entries(experiment.algorithm_parameters || {});
  const improvement =
    experiment.best_value == null || experiment.initial_value == null
      ? null
      : experiment.best_value - experiment.initial_value;
  const termination = TERMINATION_COPY[experiment.termination_reason]
    || experiment.termination_reason
    || "No termination reason was recorded for this run.";

  return (
    <div className="overview-panel">
      <section className="overview-hero">
        <div className="overview-hero-copy">
          <div className="overview-kickers">
            <span className={`overview-status ${experiment.status}`}>{experiment.status}</span>
            <span>{experiment.saved ? "Saved result" : "Temporary result"}</span>
          </div>
          <h3>{experiment.experiment_name || "Untitled experiment"}</h3>
          <p>{termination}</p>
        </div>
        <div className={`overview-improvement ${improvement >= 0 ? "positive" : "negative"}`}>
          <span>Best improvement</span>
          <strong>{improvement == null ? "—" : `${improvement >= 0 ? "+" : ""}${formatObjective(improvement)}`}</strong>
          <small>compared with the initial state</small>
        </div>
      </section>

      <div className="overview-grid">
        <section className="overview-card">
          <header><span>SEARCH</span><h4>Run progress</h4></header>
          <dl>
            <div><dt>Iterations completed</dt><dd>{formatObjective(experiment.iterations)}</dd></div>
            <div><dt>Configured limit</dt><dd>{formatObjective(experiment.max_iterations)}</dd></div>
            <div><dt>Random seed</dt><dd>{experiment.seed ?? "—"}</dd></div>
          </dl>
        </section>

        <section className="overview-card">
          <header><span>OBJECTIVE</span><h4>{objective.label}</h4></header>
          <p>{objective.description}</p>
          <div className="overview-objective-id">Objective function {objective.id}</div>
        </section>

        <section className="overview-card">
          <header><span>PROBLEM</span><h4>Search space</h4></header>
          <dl>
            <div><dt>Packages</dt><dd>{formatObjective(experiment.package_count)}</dd></div>
            <div><dt>Containers</dt><dd>{formatObjective(experiment.truck_count)}</dd></div>
            <div><dt>Algorithm</dt><dd>{LABELS[experiment.algorithm] || experiment.algorithm}</dd></div>
          </dl>
        </section>
      </div>

      <section className="overview-parameters">
        <header><span>CONFIGURATION</span><h4>Algorithm parameters</h4></header>
        {parameters.length ? (
          <div className="parameter-grid">
            {parameters.map(([name, value]) => (
              <div key={name}>
                <span>{PARAMETER_LABELS[name] || name.replaceAll("_", " ")}</span>
                <strong>{parameterValue(name, value)}</strong>
              </div>
            ))}
          </div>
        ) : (
          <p className="overview-empty-parameters">This algorithm has no additional run parameters.</p>
        )}
      </section>
    </div>
  );
}


function DetailsModal({ experiment, onClose }) {
  const [tab, setTab] = useState("overview");
  const [stateView, setStateView] = useState("3d");

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <section className="modal details-modal" role="dialog" aria-modal="true" aria-label="Experiment details" onMouseDown={(event) => event.stopPropagation()}>
        <header className="modal-header">
          <div><span>RUN DETAILS</span><h2>{experiment.algorithm}</h2><p className="detail-objective">{selectedObjective(experiment).label}</p></div>
          <button onClick={onClose}>×</button>
        </header>
        <div className="detail-stats">
          <div><span>Initial</span><strong title={String(experiment.initial_value)}>{formatObjective(experiment.initial_value)}</strong></div>
          <div><span>Final</span><strong title={String(experiment.final_value)}>{formatObjective(experiment.final_value)}</strong></div>
          <div><span>Best</span><strong title={String(experiment.best_value)}>{formatObjective(experiment.best_value)}</strong></div>
          <div><span>Runtime</span><strong>{experiment.execution_time == null ? "—" : `${experiment.execution_time.toFixed(4)}s`}</strong></div>
        </div>
        <nav className="detail-tabs">
          {["overview", "plots", "initial_state", "final_state", "best_state", "metrics"].map((name) => (
            <button key={name} className={tab === name ? "active" : ""} onClick={() => setTab(name)}>
              {name.replace("_", " ")}
            </button>
          ))}
        </nav>
        <div className={`detail-content ${tab === "overview" ? "overview-content" : ""}`}>
          {tab === "overview" && <OverviewPanel experiment={experiment} />}
          {tab === "metrics" && <pre>{JSON.stringify(experiment.metrics || {}, null, 2)}</pre>}
          {tab === "plots" && <ExperimentPlots experiment={experiment} />}
          {["initial_state", "final_state", "best_state"].includes(tab) && (
            <>
              <div className="state-view-switch" role="group" aria-label="State display mode">
                <button type="button" aria-pressed={stateView === "3d"} onClick={() => setStateView("3d")}>3D view</button>
                <button type="button" aria-pressed={stateView === "table"} onClick={() => setStateView("table")}>Table view</button>
              </div>
              {stateView === "3d" ? (
                <Suspense fallback={<div className="viz-loading">Loading 3D viewer…</div>}>
                  <StateVisualization
                    rows={experiment[tab] || []}
                    trucks={experiment.trucks || []}
                    value={experiment[{ initial_state: "initial_value", final_state: "final_value", best_state: "best_value" }[tab]]}
                    stateLabel={tab.replace("_", " ")}
                  />
                </Suspense>
              ) : <StateTable rows={experiment[tab] || []} />}
            </>
          )}
        </div>
      </section>
    </div>
  );
}


function StateTable({ rows }) {
  if (!rows.length) return <p className="empty-copy">State is not available yet.</p>;
  const columns = ["package_id", "status", "truck", "x", "y", "z", "orientation", "value", "weight", "fragile"];

  return (
    <div className="table-wrap">
      <table>
        <thead><tr>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.package_id}>
              {columns.map((column) => <td key={column}>{String(row[column] ?? "—")}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


export default function App() {
  const [experiments, setExperiments] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [contextMenu, setContextMenu] = useState(null);
  const [details, setDetails] = useState(null);
  const [sort, setSort] = useState("newest");
  const [error, setError] = useState("");

  async function refresh() {
    try {
      const data = await api("/api/experiments");
      setExperiments(data);
      setSelected((current) => {
        const existing = new Set(data.map((item) => item.id));
        return new Set([...current].filter((id) => existing.has(id)));
      });
      setError("");
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  useEffect(() => {
    refresh();
    const interval = window.setInterval(refresh, 700);
    return () => window.clearInterval(interval);
  }, []);

  useEffect(() => {
    const closeMenu = () => setContextMenu(null);
    window.addEventListener("click", closeMenu);
    return () => window.removeEventListener("click", closeMenu);
  }, []);

  const sortedExperiments = useMemo(() => {
    const items = [...experiments];
    if (sort === "value") return items.sort((a, b) => (b.best_value ?? -Infinity) - (a.best_value ?? -Infinity));
    if (sort === "algorithm") return items.sort((a, b) => a.algorithm.localeCompare(b.algorithm));
    return items.sort((a, b) => b.created_at.localeCompare(a.created_at));
  }, [experiments, sort]);

  const displayed = sortedExperiments.filter((experiment) => selected.has(experiment.id));

  function toggleSelected(id) {
    setSelected((current) => {
      const next = new Set(current);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  function experimentCreated(experiment) {
    setExperiments((current) => [experiment, ...current]);
    setSelected((current) => new Set([...current, experiment.id]));
    setShowForm(false);
  }

  async function openDetails(id) {
    try {
      setDetails(await api(`/api/experiments/${id}`));
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function saveExperiment(id) {
    try {
      await api(`/api/experiments/${id}/save`, { method: "POST" });
      await refresh();
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function deleteExperiment(id) {
    const experiment = experiments.find((item) => item.id === id);
    const message = experiment?.status === "pending"
      ? "Cancel and delete this running experiment?"
      : "Delete this experiment result?";

    if (!window.confirm(message)) return;

    try {
      await api(`/api/experiments/${id}`, { method: "DELETE" });
      setExperiments((current) => current.filter((item) => item.id !== id));
      setSelected((current) => {
        const next = new Set(current);
        next.delete(id);
        return next;
      });
      setContextMenu(null);
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  async function exportExperiments() {
    const source = selected.size
      ? experiments.filter((item) => selected.has(item.id))
      : experiments;
    const fullResults = await Promise.all(
      source.map((item) => api(`/api/experiments/${item.id}`)),
    );
    downloadJson(fullResults, "experiment-results.json");
  }

  async function downloadExperiment(id) {
    const data = await api(`/api/experiments/${id}`);
    downloadJson(data, `experiment-${id}.json`);
  }

  return (
    <div className={`app-shell ${sidebarOpen ? "sidebar-open" : "sidebar-closed"}`}>
      <aside className="sidebar">
        <div className="sidebar-inner">
          <header className="sidebar-toolbar">
            <button className="add-button" onClick={() => setShowForm(true)} title="Run experiment">+</button>
            <button className="export-button" onClick={exportExperiments}>Export</button>
            <select value={sort} onChange={(event) => setSort(event.target.value)} title="Sort results">
              <option value="newest">Newest</option>
              <option value="value">Value</option>
              <option value="algorithm">Algorithm</option>
            </select>
          </header>
          <div className="list-header">
            <span>Experiment</span><span>Algorithm</span><span>Value</span><span>Status</span><span />
          </div>
          <div className="result-list">
            {sortedExperiments.map((experiment) => (
              <div
                className={`result-row ${selected.has(experiment.id) ? "selected" : ""}`}
                key={experiment.id}
                onDoubleClick={() => experiment.status !== "pending" && openDetails(experiment.id)}
                onContextMenu={(event) => {
                  event.preventDefault();
                  setContextMenu({ id: experiment.id, x: event.clientX, y: event.clientY });
                }}
              >
                <strong title={experiment.experiment_name}>{experiment.experiment_name}</strong>
                <span className="row-algorithm" title={experiment.algorithm}>
                  {LABELS[experiment.algorithm] || experiment.algorithm}
                </span>
                <span title={String(experiment.best_value)}>{formatObjective(experiment.best_value)}</span>
                <span className={`row-status ${experiment.status}`}>{experiment.status}</span>
                <input
                  type="checkbox"
                  checked={selected.has(experiment.id)}
                  onChange={() => toggleSelected(experiment.id)}
                  aria-label={`Display ${experiment.experiment_name}`}
                />
              </div>
            ))}
            {!sortedExperiments.length && (
              <div className="empty-list"><strong>No experiments</strong><span>Use + to start a run.</span></div>
            )}
          </div>
        </div>
      </aside>

      <div className="toggle-rail">
        <button onClick={() => setSidebarOpen((open) => !open)} title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}>
          {sidebarOpen ? "‹" : "›"}
        </button>
      </div>

      <main className="workspace">
        {error && <div className="error-banner" onClick={() => setError("")}>{error}</div>}
        {!displayed.length ? (
          <div className="empty-workspace">
            <strong>No result selected</strong>
            <span>Check results in the left panel to compare them here.</span>
          </div>
        ) : (
          <div className="cards-scroll">
            <section className="cards-grid">
              {displayed.map((experiment) => (
                <ResultCard key={experiment.id} experiment={experiment} onDetails={openDetails} />
              ))}
            </section>
          </div>
        )}
      </main>

      {contextMenu && (() => {
        const experiment = experiments.find((item) => item.id === contextMenu.id);
        if (!experiment) return null;

        return (
          <div
            className="context-menu"
            style={{ left: contextMenu.x, top: contextMenu.y }}
            onClick={(event) => event.stopPropagation()}
          >
            <small>{LABELS[experiment.algorithm]} · {experiment.experiment_name}</small>
            {experiment.status === "completed" && !experiment.saved && (
              <button onClick={() => saveExperiment(experiment.id)}>Save result</button>
            )}
            {experiment.status !== "pending" && (
              <button onClick={() => openDetails(experiment.id)}>View details</button>
            )}
            <button onClick={() => downloadExperiment(experiment.id)}>Download JSON</button>
            <hr />
            <button
              className="danger"
              onClick={() => deleteExperiment(experiment.id)}
            >
              {experiment.status === "pending" ? "Cancel and delete" : "Delete result"}
            </button>
          </div>
        );
      })()}

      {showForm && <ExperimentForm onClose={() => setShowForm(false)} onCreated={experimentCreated} />}
      {details && <DetailsModal experiment={details} onClose={() => setDetails(null)} />}
    </div>
  );
}
