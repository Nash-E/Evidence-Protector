// upload.js — Handles drag-and-drop and file input upload

let currentFileId = null;

function initUpload() {
  const dropzone = document.getElementById('dropzone');
  const fileInput = document.getElementById('file-input');
  const analyzeBtn = document.getElementById('analyze-btn');

  // Drag events
  ['dragenter', 'dragover'].forEach(evt => {
    dropzone.addEventListener(evt, e => {
      e.preventDefault();
      dropzone.classList.add('drag-over');
    });
  });
  ['dragleave', 'drop'].forEach(evt => {
    dropzone.addEventListener(evt, e => {
      e.preventDefault();
      dropzone.classList.remove('drag-over');
    });
  });

  dropzone.addEventListener('drop', e => {
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  });

  dropzone.addEventListener('click', () => fileInput.click());

  fileInput.addEventListener('change', () => {
    if (fileInput.files[0]) uploadFile(fileInput.files[0]);
  });

  analyzeBtn.addEventListener('click', () => {
    if (currentFileId) runAnalysis(currentFileId);
  });

  // Sensitivity slider
  const slider = document.getElementById('sensitivity-slider');
  const valDisplay = document.getElementById('sensitivity-value');
  slider.addEventListener('input', () => {
    valDisplay.textContent = parseFloat(slider.value).toFixed(1);
  });
}

function uploadFile(file) {
  const progressSection = document.getElementById('upload-progress');
  const progressBar = document.getElementById('progress-bar');
  const progressPct = document.getElementById('progress-pct');
  const analyzeBtn = document.getElementById('analyze-btn');

  progressSection.classList.remove('hidden');
  analyzeBtn.disabled = true;
  hideError();
  hideResults();

  const xhr = new XMLHttpRequest();

  xhr.upload.addEventListener('progress', e => {
    if (e.lengthComputable) {
      const pct = Math.round((e.loaded / e.total) * 100);
      progressBar.style.width = pct + '%';
      progressPct.textContent = pct + '%';
    }
  });

  xhr.addEventListener('load', () => {
    progressSection.classList.add('hidden');
    if (xhr.status === 200) {
      const res = JSON.parse(xhr.responseText);
      currentFileId = res.file_id;
      analyzeBtn.disabled = false;

      // Update dropzone to show filename
      document.querySelector('.dropzone-text').textContent = '\u2713 ' + res.filename;
      document.querySelector('.dropzone-sub').textContent =
        formatBytes(res.size_bytes) + ' \u2014 ready to analyze';
    } else {
      showError('Upload failed: ' + xhr.responseText);
    }
  });

  xhr.addEventListener('error', () => {
    progressSection.classList.add('hidden');
    showError('Upload failed. Please try again.');
  });

  xhr.open('POST', '/api/upload?filename=' + encodeURIComponent(file.name));
  xhr.setRequestHeader('Content-Type', 'application/octet-stream');
  xhr.send(file);
}

function formatBytes(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
}

document.addEventListener('DOMContentLoaded', initUpload);
