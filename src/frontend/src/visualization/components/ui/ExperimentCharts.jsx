import { useEffect, useId, useRef, useState } from "react";
import { chartData, objectiveChart, probabilityChart } from "../../utils/charts.js";
import "../../style/charts.css";

const formatValue = (value) => new Intl.NumberFormat("en-US", { maximumFractionDigits: 3 }).format(value);

export function LineChart({ chart, compact = false }) {
  const id = useId();
  const stageRef = useRef(null);
  const [width, setWidth] = useState(compact ? 420 : 760);
  const [activeIteration, setActiveIteration] = useState(null);
  const data = chartData(chart);
  const hasData = Boolean(data);

  useEffect(() => {
    if (!stageRef.current) return;
    const observer = new ResizeObserver(([entry]) => setWidth(Math.max(240, Math.round(entry.contentRect.width))));
    observer.observe(stageRef.current);
    return () => observer.disconnect();
  }, [hasData]);

  if (!data) return <div className="experiment-chart-empty" role="status">{chart.emptyMessage || "Objective history is unavailable for this run."}</div>;

  const height = compact ? 190 : 280;
  const yTicks = [0, 0.5, 1].map((ratio) => ({ ratio, value: data.maximum - ratio * (data.maximum - data.minimum) }));
  const labelWidth = Math.max(...yTicks.map((tick) => formatValue(tick.value).length)) * 7;
  const padding = { left: Math.max(64, labelWidth + 30), right: 16, top: 16, bottom: 46 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const span = data.lastIteration - data.firstIteration;
  const x = (iteration) => padding.left + (span ? (iteration - data.firstIteration) / span : 0.5) * plotWidth;
  const y = (value) => padding.top + (data.maximum - value) / (data.maximum - data.minimum) * plotHeight;
  const xTicks = [...new Set([data.firstIteration, data.firstIteration + Math.floor(span / 2), data.lastIteration])];
  const selectedIteration = activeIteration === null ? null : Math.max(data.firstIteration, Math.min(data.lastIteration, activeIteration));
  const selectedPoints = data.series.flatMap((item) => {
    return item.points.filter((point) => point.iteration === selectedIteration && point.value !== null)
      .map((point) => ({ ...point, label: `${item.label}${point.run ? ` · run ${point.run}` : ""}`, color: item.color }));
  });

  function pointerMove(event) {
    const bounds = event.currentTarget.getBoundingClientRect();
    const position = (event.clientX - bounds.left) / bounds.width * width;
    const ratio = Math.max(0, Math.min(1, (position - padding.left) / plotWidth));
    setActiveIteration(data.firstIteration + Math.round(ratio * span));
  }

  function keyDown(event) {
    let next = selectedIteration ?? data.firstIteration;
    if (event.key === "ArrowRight") next += 1;
    else if (event.key === "ArrowLeft") next -= 1;
    else if (event.key === "Home") next = data.firstIteration;
    else if (event.key === "End") next = data.lastIteration;
    else return;
    event.preventDefault();
    setActiveIteration(Math.max(data.firstIteration, Math.min(data.lastIteration, next)));
  }

  return (
    <figure className={`experiment-chart${compact ? " compact" : ""}`}>
      <figcaption>
        <h3>{chart.title}</h3>
        <div className="experiment-chart-legend">
          {data.series.map((item) => <span key={item.label}><i style={{ borderColor: item.color, borderTopStyle: item.dashed ? "dashed" : "solid" }} />{item.label}</span>)}
        </div>
      </figcaption>
      <div className="experiment-chart-stage" ref={stageRef}>
        <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-labelledby={`${id}-title ${id}-description`} tabIndex="0"
          onPointerMove={pointerMove} onPointerLeave={() => setActiveIteration(null)}
          onFocus={() => setActiveIteration(data.firstIteration)} onBlur={() => setActiveIteration(null)} onKeyDown={keyDown}>
          <title id={`${id}-title`}>{chart.title}</title>
          <desc id={`${id}-description`}>{data.series.map((item) => item.label).join(" and ")} versus {chart.xLabel.toLowerCase()}, {data.firstIteration} to {data.lastIteration}. Use the arrow keys to inspect values, Home for the first iteration, or End for the last.</desc>
          {yTicks.map(({ ratio, value }) => {
            const position = padding.top + ratio * plotHeight;
            return <g key={ratio}>
              <line x1={padding.left} x2={width - padding.right} y1={position} y2={position} className="experiment-chart-grid" />
              <text x={padding.left - 8} y={position + 4} textAnchor="end">{formatValue(value)}</text>
            </g>;
          })}
          {xTicks.map((iteration) => <g key={iteration}>
            <line x1={x(iteration)} x2={x(iteration)} y1={padding.top + plotHeight} y2={padding.top + plotHeight + 4} className="experiment-chart-axis" />
            <text x={x(iteration)} y={height - 28} textAnchor="middle">{iteration}</text>
          </g>)}
          <text x={padding.left + plotWidth / 2} y={height - 6} textAnchor="middle">{chart.xLabel}</text>
          <text transform={`translate(13 ${padding.top + plotHeight / 2}) rotate(-90)`} textAnchor="middle">{chart.yLabel}</text>
          {[...data.series].reverse().map((item) => {
            let connected = false;
            const path = item.points.map((point) => {
              if (point.value === null) { connected = false; return ""; }
              const command = connected ? "L" : "M";
              connected = true;
              return `${command}${x(point.iteration).toFixed(2)},${y(point.value).toFixed(2)}`;
            }).join(" ");
            const onlyPoint = item.points.filter((point) => point.value !== null);
            return <g key={item.label}>
              <path d={path} fill="none" stroke={item.color} strokeWidth="2.5" strokeDasharray={item.dashed ? "7 5" : undefined} vectorEffect="non-scaling-stroke" />
              {(onlyPoint.length === 1 || span === 0) && onlyPoint.map((point, index) => <circle key={index} cx={x(point.iteration)} cy={y(point.value)} r="3.5" fill={item.color} />)}
            </g>;
          })}
          {selectedIteration !== null && <line x1={x(selectedIteration)} x2={x(selectedIteration)} y1={padding.top} y2={padding.top + plotHeight} className="experiment-chart-crosshair" />}
          {selectedPoints.map((point) => <circle key={point.label} cx={x(point.iteration)} cy={y(point.value)} r="4" fill={point.color} stroke="#101116" strokeWidth="1.5" />)}
        </svg>
        {selectedIteration !== null && <div className="experiment-chart-tooltip" role="status">
          <strong>Iteration {selectedIteration}</strong>
          {selectedPoints.length ? selectedPoints.map((point) => <span key={point.label} style={{ color: point.color }}>{point.label}: {formatValue(point.value)}</span>) : <span>No recorded value</span>}
        </div>}
      </div>
      {!compact && chart.description && <p className="experiment-chart-note">{chart.description}</p>}
      {chart.note && <p className="experiment-chart-note">{chart.note}</p>}
    </figure>
  );
}

export function ObjectiveChart({ experiment, compact = false }) {
  return <LineChart chart={objectiveChart(experiment)} compact={compact} />;
}

export default function ExperimentPlots({ experiment }) {
  return <div className="experiment-plots">
    <ObjectiveChart experiment={experiment} />
    {experiment.algorithm === "Simulated Annealing" && <LineChart chart={probabilityChart(experiment)} />}
  </div>;
}
