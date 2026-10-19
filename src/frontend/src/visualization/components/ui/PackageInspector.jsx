import { packageColor } from "../../utils/state.js";

export default function PackageInspector({ row }) {
  if (!row) return (
    <section className="viz-inspector viz-inspector-empty">
      <div className="viz-cube-icon" aria-hidden="true">◇</div>
      <h3>Inspect a package</h3>
      <p>Select a box in the 3D view or a package in the list to see its placement and properties.</p>
    </section>
  );
  const inside = row.status === "inside";
  return (
    <section className="viz-inspector" aria-label="Selected package" aria-live="polite">
      <header>
        <span className="viz-package-dot" style={{ background: packageColor(row) }} />
        <h3>{row.package_id}</h3>
        <span className={`viz-status-tag ${inside ? "inside" : "outside"}`}>{inside ? row.truck : "Outside"}</span>
      </header>
      {row.fragile && <div className="viz-fragile-note">Fragile · cannot support another package</div>}
      <dl>
        <div><dt>Position (x, y, z)</dt><dd>{inside ? `${row.x}, ${row.y}, ${row.z}` : "Outside the truck"}</dd></div>
        <div><dt>Dimensions (w × l × h)</dt><dd>{row.width ?? "—"} × {row.length ?? "—"} × {row.height ?? "—"}</dd></div>
        <div><dt>Orientation</dt><dd>{row.orientation || "—"}</dd></div>
        <div><dt>Value</dt><dd>{row.value ?? "—"}</dd></div>
        <div><dt>Weight</dt><dd>{row.weight ?? "—"}</dd></div>
        <div><dt>ETA</dt><dd>{row.eta == null ? "—" : `${row.eta} days`}</dd></div>
      </dl>
      {!inside && <p className="viz-staging-note">Outside boxes are arranged in a staging area for inspection. They have no truck coordinates.</p>}
    </section>
  );
}
