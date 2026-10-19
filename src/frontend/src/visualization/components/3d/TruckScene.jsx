import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { buildSceneObjects, disposeObjects } from "../../utils/scene.js";

function createViewer(host, onSelect, onHover, onError) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#121b19");
  const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 2000);
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.domElement.tabIndex = 0;
  renderer.domElement.setAttribute("role", "img");
  renderer.domElement.setAttribute("aria-label", "3D truck state. Drag to orbit, scroll to zoom, right-drag or use arrow keys to pan. Press R to reset, plus or minus to zoom.");
  host.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.maxPolarAngle = Math.PI / 2 - 0.01;
  controls.minPolarAngle = 0.001;
  controls.listenToKeyEvents(renderer.domElement);
  scene.add(new THREE.HemisphereLight("#f4fff6", "#435144", 2.5));
  const light = new THREE.DirectionalLight("#fff2df", 3);
  light.position.set(15, 30, 10);
  scene.add(light);
  const fill = new THREE.DirectionalLight("#c9e7ff", 1);
  fill.position.set(-15, 12, -10);
  scene.add(fill);

  let content = null;
  let layout = null;
  let selectedId = null;
  let hoveredId = null;
  let showLabels = false;
  let view = "isometric";
  let pointerStart = null;
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  const render = () => renderer.render(scene, camera);

  function highlight() {
    content?.meshes.forEach(({ mesh, edges }, id) => {
      const selected = id === selectedId;
      const hovered = id === hoveredId;
      const selectedColor = mesh.userData.fragile ? "#ef6a5b" : "#8da88e";
      const hoveredColor = mesh.userData.fragile ? "#8f4035" : "#435c47";
      mesh.material.emissive.set(selected ? selectedColor : hovered ? hoveredColor : "#000000");
      mesh.material.emissiveIntensity = selected ? 0.5 : 0.35;
      edges.material.color.set(selected ? "#ffffff" : hovered ? (mesh.userData.fragile ? "#ffb4a6" : "#bde4c5") : "#25382c");
      content.labels.get(id).visible = showLabels || selected;
    });
    render();
  }

  function setView(nextView = view) {
    view = nextView;
    if (!layout) return;
    const { width, height, length } = layout.bounds;
    const bounds = new THREE.Box3(new THREE.Vector3(-1, -0.15, -2.5), new THREE.Vector3(width + 1, height + 1, length + 1));
    const sphere = bounds.getBoundingSphere(new THREE.Sphere());
    const verticalFov = THREE.MathUtils.degToRad(camera.fov);
    const horizontalFov = 2 * Math.atan(Math.tan(verticalFov / 2) * camera.aspect);
    const directions = {
      isometric: new THREE.Vector3(1.15, 0.95, 1.35),
      top: new THREE.Vector3(0.001, 1, 0.001),
      front: new THREE.Vector3(0, 0.12, 1),
      side: new THREE.Vector3(1, 0.12, 0),
    };
    const direction = directions[view].clone().normalize();
    const right = new THREE.Vector3().crossVectors(camera.up, direction).normalize();
    const up = new THREE.Vector3().crossVectors(direction, right).normalize();
    let distance = 0;
    const fitBounds = [new THREE.Box3(
      new THREE.Vector3(-0.5, -0.15, -1.8),
      new THREE.Vector3(Math.max(layout.truck.width, 3) + 0.5, Math.max(layout.truck.height, 3) + 0.5, Math.max(layout.truck.length, 3) + 0.5),
    )];
    if (layout.staging) {
      const stagingHeight = Math.max(1, ...layout.packages.filter(row => row.status === "outside").map(row => row.height));
      fitBounds.push(new THREE.Box3(
        new THREE.Vector3(layout.staging.x - 0.5, -0.15, -1.8),
        new THREE.Vector3(layout.staging.x + layout.staging.width + 0.5, stagingHeight + 0.5, layout.staging.length + 0.5),
      ));
    }
    for (const box of fitBounds) {
      for (const x of [box.min.x, box.max.x]) {
        for (const y of [box.min.y, box.max.y]) {
          for (const z of [box.min.z, box.max.z]) {
            const offset = new THREE.Vector3(x, y, z).sub(sphere.center);
            const depth = offset.dot(direction);
            distance = Math.max(distance,
              depth + Math.abs(offset.dot(right)) / Math.tan(horizontalFov / 2),
              depth + Math.abs(offset.dot(up)) / Math.tan(verticalFov / 2));
          }
        }
      }
    }
    distance *= 1.1;
    controls.target.copy(sphere.center);
    camera.position.copy(sphere.center).add(direction.multiplyScalar(distance));
    camera.near = Math.max(0.01, sphere.radius / 1000);
    camera.far = Math.max(1000, distance * 20);
    camera.updateProjectionMatrix();
    controls.minDistance = sphere.radius * 0.15;
    controls.maxDistance = distance * 5;
    controls.update();
    render();
  }

  function resize() {
    const width = Math.max(host.clientWidth, 1);
    const height = Math.max(host.clientHeight, 1);
    renderer.setSize(width, height);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    setView();
  }

  function pick(event) {
    if (!content) return null;
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.set(((event.clientX - rect.left) / rect.width) * 2 - 1, -((event.clientY - rect.top) / rect.height) * 2 + 1);
    raycaster.setFromCamera(pointer, camera);
    return raycaster.intersectObjects([...content.meshes.values()].map(({ mesh }) => mesh), false)[0]?.object.userData.packageId ?? null;
  }

  function pointerMove(event) {
    const id = pick(event);
    if (id === hoveredId) return;
    hoveredId = id;
    renderer.domElement.style.cursor = id ? "pointer" : "grab";
    onHover(id);
    highlight();
  }
  function pointerLeave() {
    hoveredId = null;
    onHover(null);
    highlight();
  }
  function pointerDown(event) {
    if (event.button === 0) pointerStart = { x: event.clientX, y: event.clientY };
  }
  function pointerUp(event) {
    if (event.button === 0 && pointerStart && Math.hypot(event.clientX - pointerStart.x, event.clientY - pointerStart.y) < 5) onSelect(pick(event));
    pointerStart = null;
  }
  function keyDown(event) {
    if (event.key.toLowerCase() === "r") setView();
    else if (["+", "=", "-"].includes(event.key)) {
      const factor = event.key === "-" ? 1.15 : 1 / 1.15;
      const offset = camera.position.clone().sub(controls.target).multiplyScalar(factor);
      offset.clampLength(controls.minDistance, controls.maxDistance);
      camera.position.copy(controls.target).add(offset);
      controls.update();
      render();
    } else return;
    event.preventDefault();
  }
  function contextLost(event) {
    event.preventDefault();
    onError("The 3D view lost its graphics context. Reopen the viewer or use Table view.");
  }

  const events = { pointermove: pointerMove, pointerleave: pointerLeave, pointerdown: pointerDown, pointerup: pointerUp, keydown: keyDown, webglcontextlost: contextLost };
  Object.entries(events).forEach(([name, handler]) => renderer.domElement.addEventListener(name, handler));
  controls.addEventListener("change", render);
  const observer = new ResizeObserver(resize);
  observer.observe(host);
  resize();

  return {
    update(nextLayout) {
      if (content) {
        scene.remove(content.root);
        disposeObjects(content.root);
      }
      layout = nextLayout;
      content = buildSceneObjects(layout);
      scene.add(content.root);
      hoveredId = null;
      onHover(null);
      highlight();
      setView();
    },
    select(id) { selectedId = id; highlight(); },
    labels(visible) { showLabels = visible; highlight(); },
    setView,
    dispose() {
      observer.disconnect();
      Object.entries(events).forEach(([name, handler]) => renderer.domElement.removeEventListener(name, handler));
      controls.removeEventListener("change", render);
      controls.dispose();
      disposeObjects(scene);
      renderer.dispose();
      renderer.forceContextLoss();
      renderer.domElement.remove();
    },
  };
}

export default function TruckScene({ layout, selectedId, showLabels, view, resetKey, onSelect }) {
  const hostRef = useRef(null);
  const viewerRef = useRef(null);
  const onSelectRef = useRef(onSelect);
  const [error, setError] = useState("");
  const [hoveredId, setHoveredId] = useState(null);

  useEffect(() => { onSelectRef.current = onSelect; }, [onSelect]);
  useEffect(() => {
    try {
      viewerRef.current = createViewer(hostRef.current, (id) => onSelectRef.current(id), setHoveredId, setError);
    } catch {
      setError("3D rendering is unavailable in this browser. You can still inspect every package in Table view.");
    }
    return () => { viewerRef.current?.dispose(); viewerRef.current = null; };
  }, []);
  useEffect(() => { viewerRef.current?.update(layout); }, [layout]);
  useEffect(() => { viewerRef.current?.select(selectedId); }, [selectedId, layout]);
  useEffect(() => { viewerRef.current?.labels(showLabels); }, [showLabels, layout]);
  useEffect(() => { viewerRef.current?.setView(view); }, [view, resetKey, layout]);

  return (
    <div className="viz-scene">
      <div className="viz-canvas-host" ref={hostRef} />
      {error && <div className="viz-scene-error" role="status">{error}</div>}
      {!error && hoveredId && <div className="viz-hover-label">{hoveredId}<span>Click to inspect</span></div>}
      <div className="viz-scene-hint">Drag to orbit <span>·</span> Scroll to zoom <span>·</span> Right-drag to pan</div>
    </div>
  );
}
