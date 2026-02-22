const API_RUN = "/api/run";
const API_COMPARE = "/api/compare";
const API_DENSITY = "/api/experiment/density";
const API_HEALTH = "/api/health";
const API_EXPORT = "/api/export/run.csv";

const $ = (id) => document.getElementById(id);

function bindSlider(sliderId, labelId) {
  const s = $(sliderId);
  const l = $(labelId);
  l.textContent = s.value;
  s.addEventListener("input", () => (l.textContent = s.value));
}
bindSlider("n_nodes", "n_nodes_val");

function payloadFromUI() {
  return {
    n_nodes: +$("n_nodes").value,
    width: +$("width").value,
    height: +$("height").value,
    sensing_radius: +$("radius").value,
    threshold_coeff: +$("th").value,
    seed: +$("seed").value,
    enable_fault_tolerance: $("ft").checked,
    failure_prob_per_round: +$("failp").value,
    n_rounds: +$("rounds").value,
  };
}

async function checkHealth() {
  try {
    const res = await fetch(API_HEALTH);
    const data = await res.json();
    $("statusLine").textContent = `API: ${data.status} (same origin)`;
  } catch {
    $("statusLine").textContent = "API: offline — start backend";
  }
}

function setBusy(btn, busy) {
  btn.disabled = !!busy;
  btn.dataset.old = btn.dataset.old || btn.textContent;
  btn.textContent = busy ? "Working…" : btn.dataset.old;
}

function updateRunCards(m) {
  $("activeNodes").textContent = m.n_on;
  $("backupNodes").textContent = m.n_off;
  $("energySaved").textContent = Number(m.energy_saved_pct).toFixed(2);
  $("coverage").textContent = Number(m.coverage_scheduled).toFixed(4);
}

function drawVoronoi(svgId, points, activeMask) {
  const svg = $(svgId);
  while (svg.firstChild) svg.removeChild(svg.firstChild);

  const W = svg.clientWidth || 900;
  const H = svg.clientHeight || 520;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  const pad = 20;

  const activePts = points.filter((_, i) => activeMask[i]);
  if (activePts.length >= 2) {
    const delaunay = d3.Delaunay.from(activePts);
    const vor = delaunay.voronoi([pad, pad, W - pad, H - pad]);
    for (let i = 0; i < activePts.length; i++) {
      const path = vor.renderCell(i);
      const cell = document.createElementNS("http://www.w3.org/2000/svg", "path");
      cell.setAttribute("d", path);
      cell.setAttribute("fill", "rgba(110,231,255,0.06)");
      cell.setAttribute("stroke", "rgba(110,231,255,0.35)");
      cell.setAttribute("stroke-width", "1");
      svg.appendChild(cell);
    }
  }

  for (let i = 0; i < points.length; i++) {
    const [x, y] = points[i];
    const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    c.setAttribute("cx", x);
    c.setAttribute("cy", y);
    c.setAttribute("r", 4);
    c.setAttribute("fill", activeMask[i] ? "#6ee7ff" : "#ff7a7a");
    c.setAttribute("opacity", activeMask[i] ? "0.95" : "0.85");
    svg.appendChild(c);
  }

  const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  rect.setAttribute("x", String(pad));
  rect.setAttribute("y", String(pad));
  rect.setAttribute("width", String(W - 2 * pad));
  rect.setAttribute("height", String(H - 2 * pad));
  rect.setAttribute("fill", "none");
  rect.setAttribute("stroke", "rgba(255,255,255,0.18)");
  rect.setAttribute("stroke-width", "1");
  svg.appendChild(rect);
}

function drawFaultCharts(logs) {
  if (!logs) {
    Plotly.purge("chartCoverage");
    Plotly.purge("chartActive");
    return;
  }
  const rounds = logs.map((x) => x.round);
  const cov = logs.map((x) => x.coverage);
  const active = logs.map((x) => x.n_active);

  Plotly.newPlot("chartCoverage",
    [{ x: rounds, y: cov, mode: "lines+markers", name: "Coverage" }],
    { title: "Coverage Over Rounds", paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", font: { color: "#e6eaf2" }, margin: { l: 45, r: 20, t: 50, b: 40 } },
    { displayModeBar: false }
  );

  Plotly.newPlot("chartActive",
    [{ x: rounds, y: active, mode: "lines+markers", name: "Active nodes" }],
    { title: "Active Nodes Over Rounds", paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", font: { color: "#e6eaf2" }, margin: { l: 45, r: 20, t: 50, b: 40 } },
    { displayModeBar: false }
  );
}

function setTab(tabId) {
  document.querySelectorAll(".tab").forEach((b) => b.classList.remove("active"));
  document.querySelectorAll(".tabpane").forEach((p) => p.classList.remove("active"));
  document.querySelector(`.tab[data-tab="${tabId}"]`).classList.add("active");
  $(tabId).classList.add("active");
}
document.querySelectorAll(".tab").forEach((btn) => btn.addEventListener("click", () => setTab(btn.dataset.tab)));

async function runVoronoi() {
  const btn = $("runBtn");
  setBusy(btn, true);
  try {
    const res = await fetch(API_RUN, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payloadFromUI()) });
    const data = await res.json();
    updateRunCards(data.metrics);

    const svg = $("voronoiSvg");
    const W = svg.clientWidth || 900;
    const H = svg.clientHeight || 520;
    const pad = 20;
    const sx = (x) => (x / data.metrics.width) * (W - 2 * pad) + pad;
    const sy = (y) => (y / data.metrics.height) * (H - 2 * pad) + pad;
    const pts = data.points.map((p) => [sx(p[0]), sy(p[1])]);

    drawVoronoi("voronoiSvg", pts, data.active_mask);
    drawFaultCharts(data.fault_logs);
  } catch {
    alert("Run failed. Make sure backend is running.");
  } finally {
    setBusy(btn, false);
  }
}

$("runBtn").addEventListener("click", () => { setTab("tab_run"); runVoronoi(); });

$("exportBtn").addEventListener("click", async () => {
  try {
    const res = await fetch(API_EXPORT, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payloadFromUI()) });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "wsn_run_export.csv";
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  } catch {
    alert("CSV export failed.");
  }
});

let compareCache = null;
let compareView = "voronoi";

function renderCompareMetrics(elId, m) {
  $(elId).innerHTML = `
    <div><b>Coverage:</b> ${Number(m.coverage_scheduled).toFixed(4)}</div>
    <div><b>Backup nodes:</b> ${m.n_off}</div>
    <div><b>Energy saved:</b> ${Number(m.energy_saved_pct).toFixed(2)}%</div>
    <div class="muted" style="margin-top:8px">
      Baseline energy: ${Number(m.baseline_energy).toFixed(2)}<br/>
      Scheduled energy: ${Number(m.scheduled_energy).toFixed(2)}
    </div>`;
}

function renderCompareViz() {
  if (!compareCache) return;
  const svg = $("cmpSvg");
  const W = svg.clientWidth || 900;
  const H = svg.clientHeight || 520;
  const pad = 20;
  const { width, height } = payloadFromUI();
  const sx = (x) => (x / width) * (W - 2 * pad) + pad;
  const sy = (y) => (y / height) * (H - 2 * pad) + pad;
  const pts = compareCache.points.map((p) => [sx(p[0]), sy(p[1])]);

  let activeMask = compareCache.voronoi.active_mask;
  if (compareView === "r1") activeMask = compareCache.random_same_off.active_mask;
  if (compareView === "r2") activeMask = compareCache.random_greedy_cov.active_mask;

  drawVoronoi("cmpSvg", pts, activeMask);
}

document.querySelectorAll(".segbtn").forEach((b) => {
  b.addEventListener("click", () => {
    document.querySelectorAll(".segbtn").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    compareView = b.dataset.algo;
    renderCompareViz();
  });
});

async function runCompare() {
  const btn = $("compareBtn");
  setBusy(btn, true);
  try {
    const res = await fetch(API_COMPARE, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payloadFromUI()) });
    const data = await res.json();
    compareCache = data;

    renderCompareMetrics("cmp_voronoi", data.voronoi.metrics);
    renderCompareMetrics("cmp_r1", data.random_same_off.metrics);
    renderCompareMetrics("cmp_r2", data.random_greedy_cov.metrics);

    setTab("tab_compare");
    compareView = "voronoi";
    document.querySelectorAll(".segbtn").forEach((x) => x.classList.remove("active"));
    document.querySelector('.segbtn[data-algo="voronoi"]').classList.add("active");
    renderCompareViz();
  } catch {
    alert("Compare failed.");
  } finally {
    setBusy(btn, false);
  }
}
$("compareBtn").addEventListener("click", runCompare);

let expRows = [];

function renderExpTable(rows) {
  const tb = document.querySelector("#expTable tbody");
  tb.innerHTML = "";
  for (const r of rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${Number(r.field_area).toFixed(2)}</td>
      <td>${Number(r.density).toFixed(5)}</td>
      <td>${r.backup_nodes}</td>
      <td>${Number(r.coverage).toFixed(4)}</td>
      <td>${Number(r.energy_saved_pct).toFixed(2)}</td>`;
    tb.appendChild(tr);
  }
}

function renderExpCharts(rows) {
  const dens = rows.map((r) => r.density);
  const energy = rows.map((r) => r.energy_saved_pct);
  const backups = rows.map((r) => r.backup_nodes);

  Plotly.newPlot("chartEnergyDensity",
    [{ x: dens, y: energy, mode: "lines+markers", name: "Energy Saved (%)" }],
    { title: "Energy Saved (%) vs Density", xaxis: { title: "Density (N / Area)" }, yaxis: { title: "Energy Saved (%)" },
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", font: { color: "#e6eaf2" }, margin: { l: 55, r: 20, t: 50, b: 50 } },
    { displayModeBar: false });

  Plotly.newPlot("chartBackupDensity",
    [{ x: dens, y: backups, mode: "lines+markers", name: "Backup nodes" }],
    { title: "Backup Nodes vs Density", xaxis: { title: "Density (N / Area)" }, yaxis: { title: "Backup nodes" },
      paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)", font: { color: "#e6eaf2" }, margin: { l: 55, r: 20, t: 50, b: 50 } },
    { displayModeBar: false });
}

async function runExperiment() {
  const btn = $("expBtn");
  setBusy(btn, true);
  try {
    const res = await fetch(API_DENSITY, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payloadFromUI()) });
    const data = await res.json();
    expRows = data.rows || [];
    renderExpTable(expRows);
    renderExpCharts(expRows);
    setTab("tab_experiment");
  } catch {
    alert("Experiment failed.");
  } finally {
    setBusy(btn, false);
  }
}
$("expBtn").addEventListener("click", runExperiment);

$("expCsvBtn").addEventListener("click", () => {
  if (!expRows.length) return alert("Run experiment first.");
  const header = ["field_area","density","backup_nodes","coverage","energy_saved_pct"];
  const lines = [header.join(",")];
  for (const r of expRows) lines.push([r.field_area, r.density, r.backup_nodes, r.coverage, r.energy_saved_pct].join(","));
  const blob = new Blob([lines.join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "wsn_experiment_density.csv";
  document.body.appendChild(a); a.click(); a.remove();
  URL.revokeObjectURL(url);
});

checkHealth();
runVoronoi();
