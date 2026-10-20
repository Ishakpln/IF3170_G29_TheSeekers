import * as THREE from "three";

export function disposeObjects(root) {
  const geometries = new Set();
  const materials = new Set();
  const textures = new Set();
  root.traverse((object) => {
    if (object.geometry) geometries.add(object.geometry);
    for (const material of Array.isArray(object.material) ? object.material : [object.material]) {
      if (!material) continue;
      materials.add(material);
      for (const value of Object.values(material)) if (value?.isTexture) textures.add(value);
    }
  });
  textures.forEach((texture) => texture.dispose());
  materials.forEach((material) => material.dispose());
  geometries.forEach((geometry) => geometry.dispose());
}

function label(text, color = "#e2e4e8", width = 2.2) {
  const canvas = document.createElement("canvas");
  canvas.width = 384;
  canvas.height = 96;
  const context = canvas.getContext("2d");
  context.fillStyle = "rgba(8, 9, 11, 0.92)";
  context.fillRect(2, 2, 380, 92);
  context.strokeStyle = "#454851";
  context.strokeRect(2, 2, 380, 92);
  context.fillStyle = color;
  context.font = "600 36px system-ui, sans-serif";
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText(text, 192, 48, 360);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, depthTest: false }));
  sprite.scale.set(width, width / 4, 1);
  sprite.renderOrder = 5;
  return sprite;
}

function floor(width, length, x, color) {
  const mesh = new THREE.Mesh(
    new THREE.BoxGeometry(width, 0.12, length),
    new THREE.MeshStandardMaterial({ color, roughness: 1 }),
  );
  mesh.position.set(x + width / 2, -0.08, length / 2);
  return mesh;
}

function grid(width, length) {
  const points = [];
  const step = Math.max(1, Math.ceil(Math.max(width, length) / 50));
  for (let x = 0; x <= width; x += step) points.push(x, 0.002, 0, x, 0.002, length);
  for (let z = 0; z <= length; z += step) points.push(0, 0.002, z, width, 0.002, z);
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(points, 3));
  return new THREE.LineSegments(geometry, new THREE.LineBasicMaterial({ color: "#464951", transparent: true, opacity: 0.55 }));
}

export function buildSceneObjects(layout) {
  const root = new THREE.Group();
  const meshes = new Map();
  const labels = new Map();
  const { truck, staging } = layout;
  root.add(floor(truck.width, truck.length, 0, "#24262c"), grid(truck.width, truck.length));

  const containerGeometry = new THREE.BoxGeometry(truck.width, truck.height, truck.length);
  const container = new THREE.Mesh(containerGeometry, new THREE.MeshBasicMaterial({
    color: "#c8ccd4", opacity: 0.035, transparent: true, depthWrite: false, side: THREE.DoubleSide,
  }));
  container.position.set(truck.width / 2, truck.height / 2, truck.length / 2);
  root.add(container);
  const frame = new THREE.LineSegments(
    new THREE.EdgesGeometry(containerGeometry),
    new THREE.LineBasicMaterial({ color: "#8d929c", transparent: true, opacity: 0.7 }),
  );
  frame.position.copy(container.position);
  root.add(frame);

  const truckLabel = label(`TRUCK ${truck.id}`, "#ffad4d", 3.6);
  truckLabel.position.set(truck.width / 2, 0.2, -1.3);
  root.add(truckLabel);
  if (staging) {
    root.add(floor(staging.width, staging.length, staging.x, "#242c34"));
    const outsideLabel = label("OUTSIDE · STAGING", "#b4c4d5", 4);
    outsideLabel.position.set(staging.x + staging.width / 2, 0.2, -1.3);
    root.add(outsideLabel);
  }

  for (const [name, direction, color] of [
    ["X", new THREE.Vector3(1, 0, 0), "#f08c82"],
    ["Y", new THREE.Vector3(0, 0, 1), "#92cda1"],
    ["Z", new THREE.Vector3(0, 1, 0), "#8faff0"],
  ]) {
    const arrow = new THREE.ArrowHelper(direction, new THREE.Vector3(0, 0.05, 0), 2.4, color, 0.35, 0.2);
    root.add(arrow);
    const axisLabel = label(name, color, 0.8);
    axisLabel.position.copy(direction.clone().multiplyScalar(2.9));
    root.add(axisLabel);
  }

  for (const row of layout.packages) {
    const geometry = new THREE.BoxGeometry(...row.size);
    const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: row.color, roughness: 0.72, metalness: 0.03 }));
    mesh.position.set(...row.center);
    mesh.userData.packageId = row.package_id;
    mesh.userData.fragile = Boolean(row.fragile);
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geometry), new THREE.LineBasicMaterial({ color: "#25382c" }));
    mesh.add(edges);
    root.add(mesh);
    meshes.set(row.package_id, { mesh, edges });

    const packageLabel = label(`${row.package_id}${row.fragile ? " · FRAGILE" : ""}`, row.fragile ? "#ffb4a6" : "#ecf2ee", row.fragile ? 2.8 : 1.6);
    packageLabel.position.set(row.center[0], row.center[1] + row.size[1] / 2 + 0.35, row.center[2]);
    packageLabel.visible = false;
    root.add(packageLabel);
    labels.set(row.package_id, packageLabel);
  }
  return { root, meshes, labels };
}
