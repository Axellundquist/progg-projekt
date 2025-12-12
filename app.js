const AVAILABLE_CLASSES = [
  "Box",
  "Bag",
  "Pallet",
  "Bottle",
  "Canister",
  "Crate",
  "Barrel",
  "Container",
];

const state = {
  imageSrc: null,
  imageDimensions: { width: 0, height: 0 },
  allDetections: null,
  filteredDetections: [],
  selectedClasses: new Set(AVAILABLE_CLASSES),
  isLoading: false,
  error: null,
};

const dropArea = document.getElementById("drop-area");
const fileInput = document.getElementById("file-input");
const fileLabel = document.getElementById("file-label");
const preview = document.getElementById("preview");
const overlay = document.getElementById("overlay");
const placeholder = document.getElementById("placeholder");
const metrics = document.getElementById("metrics");
const detectBtn = document.getElementById("detect-btn");
const retryBtn = document.getElementById("retry-btn");
const clearBtn = document.getElementById("clear-btn");
const exportBtn = document.getElementById("export-btn");
const statusArea = document.getElementById("status-area");
const statusBanner = document.getElementById("status-banner");
const selectAllBtn = document.getElementById("select-all");

function init() {
  buildClassSelector();
  attachUploader();
  detectBtn.addEventListener("click", () => handleDetection());
  retryBtn.addEventListener("click", () => handleDetection({ retry: true }));
  clearBtn.addEventListener("click", resetAll);
  exportBtn.addEventListener("click", exportResults);
  selectAllBtn.addEventListener("click", selectAllClasses);
}

function buildClassSelector() {
  const grid = document.getElementById("class-grid");
  grid.innerHTML = "";
  AVAILABLE_CLASSES.forEach((item) => {
    const card = document.createElement("label");
    card.className = "class-card";
    card.innerHTML = `
      <input type="checkbox" value="${item}" checked />
      <div>
        <strong>${item}</strong>
        <p class="hint">Include ${item.toLowerCase()} detections</p>
      </div>
    `;
    card.querySelector("input").addEventListener("change", syncSelectedClasses);
    grid.appendChild(card);
  });
}

function selectAllClasses() {
  document.querySelectorAll("#class-grid input[type='checkbox']").forEach((input) => {
    input.checked = true;
  });
  state.selectedClasses = new Set(AVAILABLE_CLASSES);
}

function syncSelectedClasses() {
  const checked = Array.from(document.querySelectorAll("#class-grid input:checked"))
    .map((input) => input.value);
  state.selectedClasses = new Set(checked);
}

function attachUploader() {
  ["dragenter", "dragover"].forEach((eventName) => {
    dropArea.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropArea.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropArea.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropArea.classList.remove("dragover");
    });
  });

  dropArea.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) {
      loadFile(file);
    }
  });

  fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) {
      loadFile(file);
    }
  });
}

function loadFile(file) {
  const allowed = ["image/png", "image/jpeg"];
  if (!allowed.includes(file.type)) {
    showStatus("Unsupported file type. Please upload a PNG or JPG.", "error");
    return;
  }

  const reader = new FileReader();
  reader.onload = (e) => {
    state.imageSrc = e.target.result;
    fileLabel.textContent = `Selected: ${file.name}`;
    placeholder.style.display = "none";
    preview.classList.remove("loaded");
    preview.src = state.imageSrc;
    state.allDetections = null;
    state.filteredDetections = [];
    statusBanner.textContent = "Image ready. Run detection when you're set.";
  };
  reader.readAsDataURL(file);
}

preview.addEventListener("load", () => {
  const { naturalWidth, naturalHeight } = preview;
  state.imageDimensions = { width: naturalWidth, height: naturalHeight };
  resizeOverlay();
  placeholder.style.display = "none";
  preview.classList.add("loaded");
  drawDetections();
});

function resizeOverlay() {
  const rect = preview.getBoundingClientRect();
  overlay.width = rect.width;
  overlay.height = rect.height;
}

function handleDetection({ retry = false } = {}) {
  if (!state.imageSrc) {
    showStatus("Please upload an image before running detection.", "error");
    return;
  }

  syncSelectedClasses();
  if (state.selectedClasses.size === 0) {
    showStatus("Select at least one item type to detect.", "error");
    return;
  }

  state.isLoading = true;
  state.error = null;
  toggleButtons();
  showStatus("Detecting items in your image...", "loading");
  retryBtn.hidden = true;

  fakeDetect(state.selectedClasses, retry)
    .then((result) => {
      state.allDetections = result.allDetections;
      state.filteredDetections = result.filtered;
      showStatus("Detection complete. Review the metrics below.", "success");
      renderMetrics();
      drawDetections();
    })
    .catch((err) => {
      state.error = err;
      showStatus(err.message || "Detection failed.", "error");
      retryBtn.hidden = false;
    })
    .finally(() => {
      state.isLoading = false;
      toggleButtons();
    });
}

function fakeDetect(selectedSet, isRetry) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const failed = Math.random() < 0.15 && !isRetry;
      if (failed) {
        reject(new Error("Network hiccup during detection. Please retry."));
        return;
      }

      if (!state.allDetections) {
        state.allDetections = generateDetections(AVAILABLE_CLASSES);
      }
      const filtered = state.allDetections.filter((det) => selectedSet.has(det.label));
      resolve({ allDetections: state.allDetections, filtered });
    }, 1100);
  });
}

function generateDetections(classes) {
  const count = Math.max(5, Math.floor(Math.random() * 8) + classes.length);
  const detections = [];
  for (let i = 0; i < count; i++) {
    const label = classes[Math.floor(Math.random() * classes.length)];
    detections.push({
      id: `${label}-${i}-${Math.floor(Math.random() * 1000)}`,
      label,
      score: Number((0.55 + Math.random() * 0.4).toFixed(2)),
      box: randomBox(),
    });
  }
  return detections;
}

function randomBox() {
  const x = Math.random() * 0.6;
  const y = Math.random() * 0.6;
  const w = 0.2 + Math.random() * 0.2;
  const h = 0.2 + Math.random() * 0.2;
  return { x, y, w, h };
}

function drawDetections() {
  const ctx = overlay.getContext("2d");
  ctx.clearRect(0, 0, overlay.width, overlay.height);
  if (!state.imageSrc || state.filteredDetections.length === 0) return;

  const colors = {
    Box: "#7bc5ff",
    Bag: "#3da9f5",
    Pallet: "#9a7bff",
    Bottle: "#5ee78b",
    Canister: "#ffce6b",
    Crate: "#ff9b6b",
    Barrel: "#ff6b9b",
    Container: "#6bf0ff",
  };

  const { width, height } = overlay;
  state.filteredDetections.forEach((det) => {
    const color = colors[det.label] || "#7bc5ff";
    const x = det.box.x * width;
    const y = det.box.y * height;
    const w = det.box.w * width;
    const h = det.box.h * height;

    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.strokeRect(x, y, w, h);

    ctx.fillStyle = color;
    ctx.font = "bold 13px Inter, sans-serif";
    const label = `${det.label} (${Math.round(det.score * 100)}%)`;
    const textWidth = ctx.measureText(label).width + 12;
    const textHeight = 20;
    ctx.fillRect(x, Math.max(y - textHeight, 0), textWidth, textHeight);

    ctx.fillStyle = "#0b1118";
    ctx.fillText(label, x + 6, Math.max(y - 6, 12));
  });
}

function renderMetrics() {
  if (!state.filteredDetections.length) {
    metrics.innerHTML = `<div class="metric-row">No detections to display.</div>`;
    exportBtn.disabled = true;
    return;
  }

  const counts = state.filteredDetections.reduce((acc, det) => {
    acc[det.label] = (acc[det.label] || 0) + 1;
    return acc;
  }, {});
  const total = state.filteredDetections.length;

  metrics.innerHTML = "";
  Object.entries(counts)
    .sort(([a], [b]) => a.localeCompare(b))
    .forEach(([label, count]) => {
      const row = document.createElement("div");
      row.className = "metric-row";
      row.innerHTML = `<span>${label}</span><strong>${count}</strong>`;
      metrics.appendChild(row);
    });

  const totalRow = document.createElement("div");
  totalRow.className = "metric-row total-row";
  totalRow.innerHTML = `<span>Total</span><strong>${total}</strong>`;
  metrics.appendChild(totalRow);
  exportBtn.disabled = false;
}

function showStatus(message, variant = "info") {
  const content = {
    loading: `<span class="spinner"></span><span>${message}</span>`,
    success: `<span class="badge success">Success</span><span>${message}</span>`,
    error: `<span class="badge error">Error</span><span>${message}</span>`,
    info: `<span class="badge info">Info</span><span>${message}</span>`,
  }[variant];
  statusArea.innerHTML = content;
  statusBanner.textContent = message;
}

function toggleButtons() {
  detectBtn.disabled = state.isLoading;
  retryBtn.disabled = state.isLoading;
  exportBtn.disabled = state.isLoading || !state.filteredDetections.length;
}

function exportResults() {
  const payload = {
    image: state.imageSrc,
    classesUsed: Array.from(state.selectedClasses),
    totalDetections: state.filteredDetections.length,
    perClassCounts: state.filteredDetections.reduce((acc, det) => {
      acc[det.label] = (acc[det.label] || 0) + 1;
      return acc;
    }, {}),
    detections: state.filteredDetections,
  };

  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "detections.json";
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

function resetAll() {
  state.imageSrc = null;
  state.allDetections = null;
  state.filteredDetections = [];
  fileInput.value = "";
  preview.src = "";
  preview.classList.remove("loaded");
  placeholder.style.display = "grid";
  metrics.innerHTML = "";
  fileLabel.textContent = "";
  statusArea.innerHTML = "";
  statusBanner.textContent = "";
  exportBtn.disabled = true;
}

window.addEventListener("resize", resizeOverlay);
init();
