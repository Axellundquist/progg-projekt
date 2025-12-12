const fileInput = document.getElementById('fileInput');
const detectButton = document.getElementById('detectButton');
const targetSelect = document.getElementById('targetSelect');
const targetChips = document.getElementById('targetChips');
const targetHint = document.getElementById('targetHint');
const errorBanner = document.getElementById('errorBanner');
const canvas = document.getElementById('previewCanvas');
const countsList = document.getElementById('countsList');
const statusChip = document.getElementById('statusChip');
const resultMeta = document.getElementById('resultMeta');

const ctx = canvas.getContext('2d');
const MAX_CANVAS_WIDTH = 1200;
const DETECTION_API_URL = '/api/detect';
const DETECTION_TIMEOUT = 8000;
const SUPPORTED_TYPES = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp'];
const TARGETS_ENDPOINT = '/targets';
const DEFAULT_TARGET_SELECTION = ['bottle', 'can', 'box_carton'];

const FALLBACK_TARGETS = [
  { value: 'bottle', label: 'Bottle', help_text: 'Plastic or glass bottles of any size.' },
  { value: 'can', label: 'Can', help_text: 'Aluminum or steel cans for beverages or food.' },
  { value: 'box_carton', label: 'Box / Carton', help_text: 'Cardboard boxes, cartons, or tetrapaks.' },
  { value: 'bag_pouch', label: 'Bag / Pouch', help_text: 'Flexible bags, pouches, or sachets.' },
  { value: 'cup', label: 'Cup', help_text: 'Disposable or reusable cups.' },
  { value: 'lid', label: 'Lid', help_text: 'Plastic or paper lids and tops.' },
  { value: 'utensil', label: 'Utensil', help_text: 'Single-use or reusable utensils.' },
  { value: 'tray_plate', label: 'Tray / Plate', help_text: 'Serving trays, clamshells, or plates.' },
];

let availableTargets = [];
let selectedTargets = new Set(DEFAULT_TARGET_SELECTION);

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
  setResultMeta('Resolve the error and retry detection.');
}

function clearError() {
  errorBanner.textContent = '';
  errorBanner.classList.add('hidden');
}

function setResultMeta(text) {
  resultMeta.textContent = text;
}

function updateTargetHint(text) {
  targetHint.textContent = text;
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

function renderDetections(image, data, sourceLabel = 'live') {
  const boxes = Array.isArray(data?.boxes) ? data.boxes : [];
  const counts = data?.counts || computeCountsFromBoxes(boxes);
  drawBoxes(image, boxes);
  renderCounts(counts);
  setStatus('Detection complete');
  setResultMeta(sourceLabel === 'mock' ? 'Showing mock results (API unavailable).' : 'Live API response rendered.');
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
  setResultMeta('Awaiting a detection run.');
}

function getSelectedTargets() {
  return Array.from(selectedTargets);
}

function syncDropdownSelection() {
  Array.from(targetSelect.options).forEach((option) => {
    option.selected = selectedTargets.has(option.value);
  });
}

function syncChipSelection() {
  const chips = targetChips.querySelectorAll('.chip');
  chips.forEach((chip) => {
    const isSelected = selectedTargets.has(chip.dataset.value);
    chip.classList.toggle('selected', isSelected);
    chip.setAttribute('aria-pressed', isSelected);
  });
}

function updateSelectionHint(targets = availableTargets) {
  const selectedLabels = targets
    .filter((target) => selectedTargets.has(target.value))
    .map((target) => target.label);
  updateTargetHint(
    selectedLabels.length
      ? `${selectedLabels.length} selected: ${selectedLabels.join(', ')}`
      : 'Select at least one class to run detection.'
  );
}

function toggleTarget(value) {
  if (selectedTargets.has(value)) {
    if (selectedTargets.size === 1) {
      return;
    }
    selectedTargets.delete(value);
  } else {
    selectedTargets.add(value);
  }
  syncDropdownSelection();
  syncChipSelection();
  updateSelectionHint();
}

function renderTargetChips(targets) {
  targetChips.innerHTML = '';
  targets.forEach((target) => {
    const chip = document.createElement('button');
    chip.type = 'button';
    chip.className = 'chip';
    chip.dataset.value = target.value;
    chip.title = target.help_text;
    chip.textContent = target.label;
    chip.setAttribute('role', 'option');
    chip.setAttribute('aria-pressed', selectedTargets.has(target.value));
    chip.addEventListener('click', () => toggleTarget(target.value));
    targetChips.appendChild(chip);
  });
  syncChipSelection();
}

function renderTargetDropdown(targets) {
  targetSelect.innerHTML = '';
  targets.forEach((target) => {
    const option = document.createElement('option');
    option.value = target.value;
    option.textContent = target.label;
    option.title = target.help_text;
    option.selected = selectedTargets.has(target.value);
    targetSelect.appendChild(option);
  });
  targetSelect.addEventListener('change', (event) => {
    const values = Array.from(event.target.selectedOptions).map((opt) => opt.value);
    if (values.length === 0 && availableTargets.length) {
      values.push(availableTargets[0].value);
    }
    selectedTargets = new Set(values);
    syncChipSelection();
    updateSelectionHint();
  });
  syncDropdownSelection();
}

function applyDefaultSelection(targets) {
  const supportedValues = new Set(targets.map((target) => target.value));
  const defaults = DEFAULT_TARGET_SELECTION.filter((value) => supportedValues.has(value));

  if (defaults.length > 0) {
    selectedTargets = new Set(defaults);
    return;
  }

  if (targets.length) {
    selectedTargets = new Set([targets[0].value]);
  }
}

async function loadTargets() {
  try {
    const response = await fetch(TARGETS_ENDPOINT);
    if (!response.ok) {
      throw new Error('Failed to load targets');
    }
    const data = await response.json();
    if (!Array.isArray(data) || data.length === 0) {
      throw new Error('No targets returned');
    }
    availableTargets = data;
    applyDefaultSelection(availableTargets);
    updateTargetHint('Hover or tap the chips to see details.');
  } catch (err) {
    availableTargets = FALLBACK_TARGETS;
    applyDefaultSelection(availableTargets);
    updateTargetHint('Using fallback classes.');
  }

  renderTargetChips(availableTargets);
  renderTargetDropdown(availableTargets);
  updateSelectionHint();
}

async function handleFileChange(event) {
  const file = event.target.files[0];
  if (!file) return;

  if (!isSupported(file)) {
    showError('Unsupported format. Please upload a JPG, PNG, or WEBP image.');
    fileInput.value = '';
    resetCanvas();
    updateCountsPlaceholder();
    detectButton.disabled = true;
    return;
  }

  clearError();
  setStatus('Image ready');
  setResultMeta('Image loaded. Choose target and run detection.');
  try {
    currentImage = await loadImageFromFile(file);
    currentFile = file;
    drawBaseImage(currentImage);
    updateCountsPlaceholder();
    detectButton.disabled = false;
  } catch (err) {
    showError(err.message);
    detectButton.disabled = true;
  }
}

async function callDetectionApi(file, targets) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), DETECTION_TIMEOUT);
  const formData = new FormData();
  formData.append('file', file);
  formData.append('targets', JSON.stringify(targets));

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
  setResultMeta('Running detection...');

  try {
    const targets = getSelectedTargets();
    const data = await callDetectionApi(currentFile, targets);
    renderDetections(currentImage, data, data?.source || 'live');
  } catch (err) {
    showError(err.message);
    // Provide a quick mock fallback to demonstrate the overlay even if the API fails.
    const demo = await mockDetection(currentImage);
    renderDetections(currentImage, demo, 'mock');
    setStatus('Mocked results (API unreachable)', 'error');
  } finally {
    detectButton.disabled = false;
  }
}

function init() {
  resetCanvas();
  updateCountsPlaceholder();
  loadTargets();
  fileInput.addEventListener('change', handleFileChange);
  detectButton.addEventListener('click', runDetection);
}

init();
