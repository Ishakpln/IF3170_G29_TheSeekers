import { useState } from "react";
import { packageColor } from "../../utils/state.js";

export default function PackageList({ rows, selectedId, onSelect }) {
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("all");
  const filtered = rows.filter((row) =>
    String(row.package_id).toLowerCase().includes(query.toLowerCase()) &&
    (filter === "all" || row.status === filter),
  );
  return (
    <section className="viz-package-list" aria-label="Package inventory">
      <header><h3>All packages</h3><span>{filtered.length} / {rows.length}</span></header>
      <div className="viz-list-filters">
        <input type="search" aria-label="Search packages" placeholder="Find package…" value={query} onChange={(event) => setQuery(event.target.value)} />
        <select aria-label="Package status filter" value={filter} onChange={(event) => setFilter(event.target.value)}>
          <option value="all">All</option><option value="inside">Loaded</option><option value="outside">Outside</option>
        </select>
      </div>
      <div className="viz-package-items">
        {filtered.length === 0 && <p className="viz-no-matches">No matching packages.</p>}
        {filtered.map((row) => (
          <button type="button" key={row.package_id} aria-pressed={selectedId === row.package_id} onClick={() => onSelect(row.package_id)}>
            <span className="viz-package-dot" style={{ background: packageColor(row) }} />
            <strong>{row.package_id}</strong>
            {row.fragile && <span className="viz-fragile-label">Fragile</span>}
            <span className={`viz-status-tag ${row.status}`}>{row.status === "inside" ? row.truck : "Outside"}</span>
          </button>
        ))}
      </div>
    </section>
  );
}
