const fileInput = document.getElementById('fileInput');
const detectButton = document.getElementById('detectButton');
const targetSelect = document.getElementById('targetSelect');
const errorBanner = document.getElementById('errorBanner');
const canvas = document.getElementById('previewCanvas');
const countsList = document.getElementById('countsList');
const statusChip = document.getElementById('statusChip');

const ctx = canvas.getContext('2d');
const MAX_CANVAS_WIDTH = 1200;
const DETECTION_API_URL = '/api/detect';
const DETECTION_TIMEOUT = 8000;
const SUPPORTED_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];

let currentImage = null;
let currentFile = null;

function setStatus(text, variant = 'idle') {
  statusChip.textContent = text;
  statusChip.classList.remove('active', 'error');
  if (variant === 'active') {
    statusChip.classList.add('active');
  } else if (variant === 'error') {
    statusChip.classList.add('error');
  }
}

function showError(message) {
  errorBanner.textContent = message;
  errorBanner.classList.remove('hidden');
  setStatus('Error', 'error');
}

function clearError() {
  errorBanner.textContent = '';
  errorBanner.classList.add('hidden');
}

function isSupported(file) {
  return SUPPORTED_TYPES.includes(file.type.toLowerCase());
}

function resetCanvas() {
  ctx.fillStyle = '#0c1324';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
}

function fitCanvasToImage(image) {
  const scale = Math.min(1, MAX_CANVAS_WIDTH / image.naturalWidth);
  canvas.width = image.naturalWidth * scale;
  canvas.height = image.naturalHeight * scale;
}

function drawBaseImage(image) {
  fitCanvasToImage(image);
  ctx.drawImage(image, 0, 0, canvas.width, canvas.height);
}

function drawBoxes(image, boxes = []) {
  drawBaseImage(image);
  const scaleX = canvas.width / image.naturalWidth;
  const scaleY = canvas.height / image.naturalHeight;

  boxes.forEach((box) => {
    const { x, y, width, height, label = 'item', score } = box;
    ctx.strokeStyle = '#22d3ee';
    ctx.lineWidth = 2;
    ctx.strokeRect(x * scaleX, y * scaleY, width * scaleX, height * scaleY);

    const text = `${label}${score ? ` (${Math.round(score * 100)}%)` : ''}`;
    ctx.fillStyle = '#22d3ee';
    ctx.font = '14px "Inter", Arial, sans-serif';
    const textWidth = ctx.measureText(text).width;
    ctx.fillRect(x * scaleX, y * scaleY - 22, textWidth + 10, 20);

    ctx.fillStyle = '#0b1220';
    ctx.fillText(text, x * scaleX + 5, y * scaleY - 7);
  });
}

function renderCounts(counts) {
  countsList.innerHTML = '';
  if (!counts || Object.keys(counts).length === 0) {
    const li = document.createElement('li');
    li.textContent = 'No detections yet.';
    countsList.appendChild(li);
    return;
  }

  Object.entries(counts).forEach(([label, count]) => {
    const li = document.createElement('li');
    li.innerHTML = `${label}: <span class="legend-count">${count}</span>`;
    countsList.appendChild(li);
  });
}

function computeCountsFromBoxes(boxes = []) {
  return boxes.reduce((acc, box) => {
    const label = box.label || 'item';
    acc[label] = (acc[label] || 0) + 1;
    return acc;
  }, {});
}

function renderDetections(image, data) {
  const boxes = Array.isArray(data?.boxes) ? data.boxes : [];
  const counts = data?.counts || computeCountsFromBoxes(boxes);
  drawBoxes(image, boxes);
  renderCounts(counts);
  setStatus('Detection complete');
}

function loadImageFromFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error('Could not load image.'));
      img.src = reader.result;
    };
    reader.onerror = () => reject(new Error('Could not read file.'));
    reader.readAsDataURL(file);
  });
}

function updateCountsPlaceholder() {
  countsList.innerHTML = '';
  const li = document.createElement('li');
  li.textContent = 'Run detection to see results.';
  countsList.appendChild(li);
}

async function handleFileChange(event) {
  const file = event.target.files[0];
  if (!file) return;

  if (!isSupported(file)) {
    showError('Unsupported format. Please upload a JPG, PNG, or WEBP image.');
    fileInput.value = '';
    resetCanvas();
    updateCountsPlaceholder();
    return;
  }

  clearError();
  setStatus('Image ready');
  try {
    currentImage = await loadImageFromFile(file);
    currentFile = file;
    drawBaseImage(currentImage);
    updateCountsPlaceholder();
  } catch (err) {
    showError(err.message);
  }
}

async function callDetectionApi(file, target) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DETECTION_TIMEOUT);
  const formData = new FormData();
  formData.append('file', file);
  formData.append('target', target);

  try {
    const response = await fetch(DETECTION_API_URL, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`Detection failed with status ${response.status}.`);
    }

    return await response.json();
  } catch (err) {
    if (err.name === 'AbortError') {
      throw new Error('Detection timed out. Please try again.');
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
}

function mockDetection(image) {
  return new Promise((resolve) => {
    setTimeout(() => {
      const boxes = [
        { x: image.naturalWidth * 0.1, y: image.naturalHeight * 0.15, width: image.naturalWidth * 0.35, height: image.naturalHeight * 0.3, label: 'demo', score: 0.86 },
        { x: image.naturalWidth * 0.6, y: image.naturalHeight * 0.25, width: image.naturalWidth * 0.25, height: image.naturalHeight * 0.4, label: 'demo', score: 0.74 },
      ];
      resolve({ boxes, counts: computeCountsFromBoxes(boxes), source: 'mock' });
    }, 500);
  });
}

async function runDetection() {
  if (!currentFile || !currentImage) {
    showError('Please upload an image before running detection.');
    return;
  }

  clearError();
  setStatus('Detecting...', 'active');
  detectButton.disabled = true;

  try {
    const target = targetSelect.value;
    const data = await callDetectionApi(currentFile, target);
    renderDetections(currentImage, data);
  } catch (err) {
    showError(err.message);
    // Provide a quick mock fallback to demonstrate the overlay even if the API fails.
    const demo = await mockDetection(currentImage);
    renderDetections(currentImage, demo);
    setStatus('Mocked results (API unreachable)', 'error');
  } finally {
    detectButton.disabled = false;
  }
}

function init() {
  resetCanvas();
  updateCountsPlaceholder();
  fileInput.addEventListener('change', handleFileChange);
  detectButton.addEventListener('click', runDetection);
}

init();
