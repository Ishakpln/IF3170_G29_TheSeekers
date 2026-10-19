export async function fetchExperimentReport(id) {
  const response = await fetch(`/api/experiments/${encodeURIComponent(id)}/export`);
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.error || `Report download failed (${response.status})`);
  }
  const disposition = response.headers.get("Content-Disposition") || "";
  const filename = disposition.match(/filename="([^"]+)"/)?.[1] || `experiment-${id}.txt`;
  return { filename, blob: await response.blob() };
}

export function downloadExperimentReport({ filename, blob }) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  try {
    document.body.appendChild(anchor);
    anchor.click();
  } finally {
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}
