const PACKAGE_COLORS = ["#83b18a", "#67a59a", "#a8b876", "#7799bc", "#b39ac2", "#c4aa7c"];

export function packageColor(row) {
  if (row.fragile) return "#ef6a5b";
  let hash = 0;
  for (const character of String(row.package_id)) hash = (hash * 31 + character.charCodeAt(0)) >>> 0;
  return PACKAGE_COLORS[hash % PACKAGE_COLORS.length];
}

export function hasDimensions(item) {
  return [item?.width, item?.length, item?.height].every((value) => Number.isFinite(value) && value > 0);
}

export function summarizeState(rows, truck) {
  const loaded = rows.filter((row) => row.status === "inside");
  const inTruck = loaded.filter((row) => row.truck === truck?.id);
  return {
    loaded: loaded.length,
    outside: rows.filter((row) => row.status === "outside").length,
    value: loaded.reduce((sum, row) => sum + Number(row.value || 0), 0),
    weight: inTruck.reduce((sum, row) => sum + Number(row.weight || 0), 0),
    inTruck: inTruck.length,
  };
}

export function sceneBox(row, position = row) {
  return {
    ...row,
    color: packageColor(row),
    size: [row.width, row.height, row.length],
    center: [position.x + row.width / 2, position.z + row.height / 2, position.y + row.length / 2],
  };
}

export function buildSceneLayout(rows, truck, showOutside = true) {
  const loaded = rows.filter((row) => row.status === "inside" && row.truck === truck.id);
  const outside = showOutside ? rows.filter((row) => row.status === "outside") : [];
  const validLoaded = loaded.filter((row) => hasDimensions(row) && [row.x, row.y, row.z].every(Number.isFinite));
  const validOutside = outside.filter(hasDimensions);
  const columns = Math.min(4, Math.max(1, Math.ceil(Math.sqrt(validOutside.length))));
  const cellWidth = Math.max(1, ...validOutside.map((row) => row.width)) + 1;
  const cellLength = Math.max(1, ...validOutside.map((row) => row.length)) + 1;
  const staging = validOutside.length ? {
    x: truck.width + 4,
    width: columns * cellWidth,
    length: Math.ceil(validOutside.length / columns) * cellLength,
  } : null;
  const packages = [
    ...validLoaded.map((row) => sceneBox(row)),
    ...validOutside.map((row, index) => sceneBox(row, {
      x: staging.x + (index % columns) * cellWidth + (cellWidth - row.width) / 2,
      y: Math.floor(index / columns) * cellLength + (cellLength - row.length) / 2,
      z: 0,
    })),
  ];
  return {
    truck,
    staging,
    packages,
    missingDimensions: loaded.length + outside.length - packages.length,
    bounds: {
      width: staging ? staging.x + staging.width : truck.width,
      length: Math.max(truck.length, staging?.length || 0),
      height: Math.max(truck.height, ...validOutside.map((row) => row.height)),
    },
  };
}
