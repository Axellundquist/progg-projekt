const fileInput = document.getElementById('file-input');
const dropzone = document.getElementById('dropzone');
const fileName = document.getElementById('file-name');
const previewWrapper = document.getElementById('image-preview');
const previewImage = document.getElementById('preview-image');
const detectButton = document.getElementById('detect-button');
const clearSelection = document.getElementById('clear-selection');
const classPicker = document.getElementById('class-picker');
const statusLine = document.getElementById('status-line');
const loader = document.getElementById('loader');
const errorBanner = document.getElementById('error-banner');
const retryButton = document.getElementById('retry-button');
const annotatedWrapper = document.getElementById('annotated-wrapper');
const resultImage = document.getElementById('result-image');
const overlay = document.getElementById('overlay');
const metrics = document.getElementById('metrics');
const totalCount = document.getElementById('total-count');
const classCounts = document.getElementById('class-counts');
const lastRun = document.getElementById('last-run');
const exportButton = document.getElementById('export-button');

let selectedFile = null;
let imageDimensions = null;
let currentDetections = [];
let lastRequest = null;

const randomFromSeed = (seedValue) => {
  let seed = seedValue;
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};

function getSelectedClasses() {
  return Array.from(classPicker.querySelectorAll('input[name="classes"]:checked')).map((input) => input.value);
}

function updateDetectAvailability() {
  const hasFile = Boolean(selectedFile);
  const hasClasses = getSelectedClasses().length > 0;
  detectButton.disabled = !(hasFile && hasClasses);
  statusLine.textContent = hasFile ? 'Ready to detect when classes are selected.' : 'Waiting for an image…';
}

function resetResults() {
  annotatedWrapper.hidden = true;
  metrics.hidden = true;
  exportButton.disabled = true;
  errorBanner.hidden = true;
  retryButton.hidden = true;
  overlay.getContext('2d').clearRect(0, 0, overlay.width, overlay.height);
  statusLine.textContent = 'Ready to detect when classes are selected.';
}

function handleFile(file) {
  if (!file || !file.type.startsWith('image/')) {
    return;
  }
  selectedFile = file;
  const url = URL.createObjectURL(file);
  previewImage.src = url;
  previewWrapper.hidden = false;
  fileName.textContent = file.name;
  resultImage.src = url;
  resetResults();
  previewImage.onload = () => {
    imageDimensions = { width: previewImage.naturalWidth, height: previewImage.naturalHeight };
    updateDetectAvailability();
  };
}

function simulateDetection(classes) {
  const { width, height } = imageDimensions;
  const seedValue = (selectedFile?.name.length || 1) * 131 + classes.join('-').length * 17;
  const rand = randomFromSeed(seedValue);
  const detections = [];

  classes.forEach((cls, idx) => {
    const count = 1 + Math.floor(rand() * 3);
    for (let i = 0; i < count; i += 1) {
      const boxWidth = Math.max(40, Math.floor(rand() * (width / 3)));
      const boxHeight = Math.max(40, Math.floor(rand() * (height / 3)));
      const x = Math.floor(rand() * (width - boxWidth));
      const y = Math.floor(rand() * (height - boxHeight));
      detections.push({
        id: `${cls}-${idx}-${i}`,
        className: cls,
        score: Math.round((0.7 + rand() * 0.3) * 100) / 100,
        box: { x, y, width: boxWidth, height: boxHeight },
      });
    }
  });

  if (rand() < 0.12) {
    throw new Error('Model service unavailable. Please try again.');
  }

  return detections;
}

function drawDetections() {
  const img = resultImage;
  const ctx = overlay.getContext('2d');
  const displayWidth = img.clientWidth;
  const displayHeight = img.clientHeight;
  const scaleX = displayWidth / imageDimensions.width;
  const scaleY = displayHeight / imageDimensions.height;

  overlay.width = displayWidth;
  overlay.height = displayHeight;
  ctx.clearRect(0, 0, overlay.width, overlay.height);

  currentDetections.forEach((det, idx) => {
    const colors = ['#38bdf8', '#c084fc', '#f472b6', '#22d3ee', '#fb923c'];
    const color = colors[idx % colors.length];
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.fillStyle = color;
    const { x, y, width, height } = det.box;
    ctx.strokeRect(x * scaleX, y * scaleY, width * scaleX, height * scaleY);
    const label = `${det.className} (${Math.round(det.score * 100)}%)`;
    const textWidth = ctx.measureText(label).width + 8;
    const textHeight = 18;
    ctx.fillRect(x * scaleX, y * scaleY - textHeight, textWidth, textHeight);
    ctx.fillStyle = '#0b1021';
    ctx.font = '12px Inter, system-ui, sans-serif';
    ctx.fillText(label, x * scaleX + 4, y * scaleY - 5);
  });
}

function showMetrics() {
  const counts = currentDetections.reduce((acc, det) => {
    acc[det.className] = (acc[det.className] || 0) + 1;
    return acc;
  }, {});

  totalCount.textContent = currentDetections.length.toString();
  classCounts.innerHTML = '';
  Object.entries(counts).forEach(([cls, count]) => {
    const li = document.createElement('li');
    li.innerHTML = `<span>${cls}</span><strong>${count}</strong>`;
    classCounts.appendChild(li);
  });
  lastRun.textContent = new Date().toLocaleTimeString();
}

function setLoading(isLoading) {
  loader.hidden = !isLoading;
  detectButton.disabled = isLoading || !selectedFile || getSelectedClasses().length === 0;
  retryButton.hidden = isLoading;
  exportButton.disabled = isLoading || currentDetections.length === 0;
}

function setError(message) {
  errorBanner.textContent = message;
  errorBanner.hidden = false;
  retryButton.hidden = false;
  annotatedWrapper.hidden = true;
  metrics.hidden = true;
}

function clearError() {
  errorBanner.hidden = true;
  retryButton.hidden = true;
  errorBanner.textContent = '';
}

async function runDetection() {
  if (!selectedFile || !imageDimensions) return;
  const classes = getSelectedClasses();
  if (!classes.length) return;

  clearError();
  setLoading(true);
  statusLine.textContent = 'Detecting items…';
  lastRequest = classes.join(', ');

  await new Promise((resolve) => setTimeout(resolve, 650));

  try {
    currentDetections = simulateDetection(classes);
    annotatedWrapper.hidden = false;
    metrics.hidden = false;
    exportButton.disabled = false;
    drawDetections();
    showMetrics();
    statusLine.textContent = `Detected ${currentDetections.length} items for ${classes.join(', ')}.`;
  } catch (error) {
    currentDetections = [];
    setError(error.message || 'Detection failed.');
    statusLine.textContent = 'Detection failed. You can retry.';
  } finally {
    setLoading(false);
  }
}

function downloadResults() {
  if (!currentDetections.length || !selectedFile) return;
  const payload = {
    sourceImage: selectedFile.name,
    classes: getSelectedClasses(),
    detectedAt: new Date().toISOString(),
    totals: currentDetections.reduce((acc, det) => {
      acc[det.className] = (acc[det.className] || 0) + 1;
      return acc;
    }, {}),
    detections: currentDetections,
  };

  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${selectedFile.name.replace(/\.[^.]+$/, '') || 'results'}-detections.json`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function resetClasses() {
  classPicker.querySelectorAll('input[name="classes"]').forEach((input) => {
    input.checked = false;
  });
  updateDetectAvailability();
  statusLine.textContent = 'Select at least one class to run detection.';
}

fileInput.addEventListener('change', (event) => {
  const [file] = event.target.files;
  handleFile(file);
});

dropzone.addEventListener('dragover', (event) => {
  event.preventDefault();
  dropzone.classList.add('dragover');
});

dropzone.addEventListener('dragleave', () => {
  dropzone.classList.remove('dragover');
});

dropzone.addEventListener('drop', (event) => {
  event.preventDefault();
  dropzone.classList.remove('dragover');
  const file = event.dataTransfer.files[0];
  handleFile(file);
});

classPicker.addEventListener('change', () => {
  clearError();
  updateDetectAvailability();
  if (selectedFile) {
    statusLine.textContent = 'Update classes and click Detect to re-run without re-uploading.';
  }
});

detectButton.addEventListener('click', (event) => {
  event.preventDefault();
  runDetection();
});

clearSelection.addEventListener('click', () => {
  resetClasses();
});

retryButton.addEventListener('click', () => {
  runDetection();
});

exportButton.addEventListener('click', () => {
  downloadResults();
});

window.addEventListener('resize', () => {
  if (!annotatedWrapper.hidden && imageDimensions) {
    drawDetections();
  }
});

updateDetectAvailability();
