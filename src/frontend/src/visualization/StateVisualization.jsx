import { useCallback, useMemo, useState } from "react";
import TruckScene from "./components/3d/TruckScene.jsx";
import PackageInspector from "./components/ui/PackageInspector.jsx";
import PackageList from "./components/ui/PackageList.jsx";
import VisualizationToolbar from "./components/ui/VisualizationToolbar.jsx";
import { buildSceneLayout, hasDimensions, summarizeState } from "./utils/state.js";
import "./style/visualization.css";

export default function StateVisualization({ rows, trucks = [], value, stateLabel }) {
  const [truckId, setTruckId] = useState(null);
  const [selectedId, setSelectedId] = useState(null);
  const [view, setView] = useState("isometric");
  const [showOutside, setShowOutside] = useState(true);
  const [showLabels, setShowLabels] = useState(false);
  const [resetKey, setResetKey] = useState(0);
  const validTrucks = useMemo(() => trucks.filter(hasDimensions), [trucks]);
  const truck = validTrucks.find((item) => item.id === truckId) || validTrucks[0];
  const selected = rows.find((row) => row.package_id === selectedId);
  const summary = useMemo(() => summarizeState(rows, truck), [rows, truck]);
  const layout = useMemo(() => truck ? buildSceneLayout(rows, truck, showOutside) : null, [rows, truck, showOutside]);

  const selectPackage = useCallback((id) => {
    setSelectedId(id);
    const row = rows.find((item) => item.package_id === id);
    if (row?.status === "inside") setTruckId(row.truck);
    if (row?.status === "outside") setShowOutside(true);
  }, [rows]);

  if (!rows.length) return <div className="viz-empty" role="status">State data is not available for this run.</div>;
  if (!truck) return <div className="viz-empty" role="status">Container dimensions are unavailable. Use Table view to inspect the package state.</div>;

  return (
    <section className="state-visualization" aria-label={`${stateLabel} 3D visualization`}>
      <div className="viz-heading"><div><span>SPATIAL VIEW</span><h3>{stateLabel}</h3></div><span className="viz-live-badge"><i />{truck.id}</span></div>
      <div className="viz-summary">
        <div><span>Objective value</span><strong>{value ?? summary.value}</strong></div>
        <div><span>Loaded · all trucks</span><strong>{summary.loaded}<small> / {rows.length}</small></strong></div>
        <div><span>Outside</span><strong>{summary.outside}</strong></div>
        <div><span>{truck.id} weight</span><strong>{summary.weight}<small> / {truck.max_capacity ?? "—"}</small></strong></div>
      </div>
      <VisualizationToolbar
        trucks={validTrucks} truckId={truck.id} onTruckChange={setTruckId}
        view={view} onViewChange={setView} showOutside={showOutside} onOutsideChange={setShowOutside}
        showLabels={showLabels} onLabelsChange={setShowLabels} onReset={() => setResetKey((key) => key + 1)}
      />
      {layout.missingDimensions > 0 && <p className="viz-data-note">{layout.missingDimensions} packages have incomplete geometry. Their details are available in the list and Table view.</p>}
      <div className="viz-body">
        <div className="viz-stage">
          <TruckScene layout={layout} selectedId={selectedId} showLabels={showLabels} view={view} resetKey={resetKey} onSelect={selectPackage} />
          <div className="viz-legend"><span><i className="loaded" />Loaded packages</span><span><i className="fragile" />Fragile</span><span><i className="outside" />Outside staging area</span><span className="viz-axis-copy">X width · Y length · Z height</span></div>
        </div>
        <aside className="viz-sidebar">
          <PackageInspector row={selected} />
          <PackageList rows={rows} selectedId={selectedId} onSelect={selectPackage} />
        </aside>
      </div>
    </section>
  );
}
