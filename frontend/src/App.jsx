import { useEffect, useMemo, useState } from "react";


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


function ObjectiveChart({ history }) {
  const values = (history || []).map(Number).filter(Number.isFinite);

  if (!values.length) {
    return <div className="chart-empty">Waiting for objective data…</div>;
  }

  const width = 420;
  const height = 180;
  const padding = { left: 46, right: 10, top: 14, bottom: 30 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const minimum = Math.min(...values);
  const maximum = Math.max(...values);
  const range = maximum - minimum || 1;
  const points = values.map((value, index) => ({
    x:
      values.length === 1
        ? padding.left + plotWidth / 2
        : padding.left + (index / (values.length - 1)) * plotWidth,
    y: padding.top + ((maximum - value) / range) * plotHeight,
  }));
  const pointString = points.map((point) => `${point.x},${point.y}`).join(" ");

  return (
    <svg className="objective-chart" viewBox={`0 0 ${width} ${height}`}>
      {[0, 0.5, 1].map((ratio) => {
        const y = padding.top + ratio * plotHeight;
        const label = maximum - ratio * (maximum - minimum);

        return (
          <g key={ratio}>
            <line
              x1={padding.left}
              x2={width - padding.right}
              y1={y}
              y2={y}
              className="chart-grid"
            />
            <text x={padding.left - 7} y={y + 4} textAnchor="end">
              {label.toFixed(label % 1 ? 1 : 0)}
            </text>
          </g>
        );
      })}
      <polyline points={pointString} className="chart-line" />
      {points.map((point, index) => (
        <circle key={index} cx={point.x} cy={point.y} r="3.5" />
      ))}
      <text x={padding.left + plotWidth / 2} y={height - 5} textAnchor="middle">
        Iteration
      </text>
    </svg>
  );
}


function ResultCard({ experiment, onDetails }) {
  const pending = experiment.status === "pending";
  const failed = experiment.status === "failed";
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
              <span>Best objective</span>
              <strong>{experiment.best_value}</strong>
              <small className={delta >= 0 ? "positive" : "negative"}>
                {delta >= 0 ? "+" : ""}
                {delta} from initial
              </small>
            </div>
            <ObjectiveChart history={experiment.objective_history} />
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
      [name]: type === "number" ? Number(value) : value,
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
              <NumberField label="Cooling rate" name="cooling_rate" value={form.cooling_rate} min="0.001" max="1" step="0.001" onChange={update} />
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


function DetailsModal({ experiment, onClose }) {
  const [tab, setTab] = useState("overview");

  return (
    <div className="modal-backdrop" onMouseDown={onClose}>
      <section className="modal details-modal" onMouseDown={(event) => event.stopPropagation()}>
        <header className="modal-header">
          <div><span>RUN DETAILS</span><h2>{experiment.algorithm}</h2></div>
          <button onClick={onClose}>×</button>
        </header>
        <div className="detail-stats">
          <div><span>Initial</span><strong>{experiment.initial_value ?? "—"}</strong></div>
          <div><span>Final</span><strong>{experiment.final_value ?? "—"}</strong></div>
          <div><span>Best</span><strong>{experiment.best_value ?? "—"}</strong></div>
          <div><span>Runtime</span><strong>{experiment.execution_time == null ? "—" : `${experiment.execution_time.toFixed(4)}s`}</strong></div>
        </div>
        <nav className="detail-tabs">
          {["overview", "initial_state", "final_state", "best_state", "metrics"].map((name) => (
            <button key={name} className={tab === name ? "active" : ""} onClick={() => setTab(name)}>
              {name.replace("_", " ")}
            </button>
          ))}
        </nav>
        <div className="detail-content">
          {tab === "overview" && <pre>{JSON.stringify({
            status: experiment.status,
            saved: experiment.saved,
            iterations: experiment.iterations,
            termination_reason: experiment.termination_reason,
            parameters: experiment.algorithm_parameters,
          }, null, 2)}</pre>}
          {tab === "metrics" && <pre>{JSON.stringify(experiment.metrics || {}, null, 2)}</pre>}
          {["initial_state", "final_state", "best_state"].includes(tab) && (
            <StateTable rows={experiment[tab] || []} />
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
    if (sort === "runtime") return items.sort((a, b) => (a.execution_time ?? Infinity) - (b.execution_time ?? Infinity));
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
    if (!window.confirm("Delete this experiment result?")) return;

    try {
      await api(`/api/experiments/${id}`, { method: "DELETE" });
      await refresh();
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
              <option value="runtime">Runtime</option>
              <option value="algorithm">Algorithm</option>
            </select>
          </header>
          <div className="list-header">
            <span>Algorithm</span><span>Runtime</span><span>Value</span><span>Status</span><span />
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
                <strong>{LABELS[experiment.algorithm] || experiment.algorithm}</strong>
                <span>{experiment.execution_time == null ? "—" : `${experiment.execution_time.toFixed(2)}s`}</span>
                <span>{experiment.best_value ?? "—"}</span>
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
              disabled={experiment.status === "pending"}
              onClick={() => deleteExperiment(experiment.id)}
            >
              Delete result
            </button>
          </div>
        );
      })()}

      {showForm && <ExperimentForm onClose={() => setShowForm(false)} onCreated={experimentCreated} />}
      {details && <DetailsModal experiment={details} onClose={() => setDetails(null)} />}
    </div>
  );
}
