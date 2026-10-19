export default function VisualizationToolbar({ trucks, truckId, onTruckChange, view, onViewChange, showOutside, onOutsideChange, showLabels, onLabelsChange, onReset }) {
  return (
    <div className="viz-toolbar">
      <label className="viz-select-field">
        <span>Container</span>
        <select aria-label="Container" value={truckId} onChange={(event) => onTruckChange(event.target.value)}>
          {trucks.map((truck) => <option key={truck.id} value={truck.id}>{truck.id} · {truck.width} × {truck.length} × {truck.height}</option>)}
        </select>
      </label>
      <label className="viz-select-field viz-camera-field">
        <span>Camera</span>
        <select aria-label="Camera view" value={view} onChange={(event) => onViewChange(event.target.value)}>
          <option value="isometric">Perspective</option>
          <option value="top">Top</option>
          <option value="front">Front</option>
          <option value="side">Side</option>
        </select>
      </label>
      <div className="viz-toolbar-toggles">
        <label><input type="checkbox" checked={showOutside} onChange={(event) => onOutsideChange(event.target.checked)} />Outside packages</label>
        <label><input type="checkbox" checked={showLabels} onChange={(event) => onLabelsChange(event.target.checked)} />Labels</label>
      </div>
      <button type="button" className="viz-reset" onClick={onReset} title="Fit the complete scene in the current camera view">↺ <span>Reset view</span></button>
    </div>
  );
}
