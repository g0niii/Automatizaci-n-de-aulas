document.addEventListener('DOMContentLoaded', function() {
  const dragZone = document.getElementById('drag-zone');
  const fileInput = document.getElementById('file-input');
  const temaSelector = document.getElementById('tema-selector');
  const temaDisplay = document.getElementById('tema-display');
  const dragZoneButton = dragZone.querySelector('.drag-zone-button');

  // Drag and drop handlers
  dragZone.addEventListener('dragover', function(e) {
    e.preventDefault();
    dragZone.classList.add('dragover');
  });

  dragZone.addEventListener('dragleave', function(e) {
    dragZone.classList.remove('dragover');
  });

  dragZone.addEventListener('drop', function(e) {
    e.preventDefault();
    dragZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      procesarArchivo(files[0]);
    }
  });

  // Click to select file
  dragZoneButton.addEventListener('click', function() {
    fileInput.click();
  });

  fileInput.addEventListener('change', function() {
    if (fileInput.files.length > 0) {
      procesarArchivo(fileInput.files[0]);
    }
  });

  // Theme selector change handler
  temaSelector.addEventListener('change', function() {
    const tema = temaSelector.value;
    temaDisplay.textContent = tema;

    fetch('/api/set-tema', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ tema: tema })
    })
    .catch(error => console.error('Error setting theme:', error));
  });

  // Process uploaded file
  function procesarArchivo(file) {
    // Validate file type
    const extension = file.name.split('.').pop().toLowerCase();
    if (extension !== 'zip' && extension !== 'rar') {
      alert('Por favor, sube un archivo .zip o .rar');
      return;
    }

    // Add loading state
    dragZone.classList.add('loading');

    // Create FormData and upload
    const formData = new FormData();
    formData.append('file', file);
    formData.append('tema', temaSelector.value);

    fetch('/upload', {
      method: 'POST',
      body: formData
    })
    .then(response => {
      if (!response.ok) {
        return response.json().then(data => {
          throw new Error(data.error || 'Error uploading file');
        });
      }
      return response.json();
    })
    .then(data => {
      alert('Archivo procesado exitosamente');
      location.reload();
    })
    .catch(error => {
      alert('Error: ' + error.message);
    })
    .finally(() => {
      dragZone.classList.remove('loading');
    });
  }
});

// Global functions for inline onclick handlers

function editarPlan(planId) {
  window.location.href = `/plan/${planId}/edit`;
}

function eliminarCurso(cursoId) {
  if (confirm('¿Seguro que quieres eliminar este curso?')) {
    fetch(`/api/course/${cursoId}`, {
      method: 'DELETE'
    })
    .then(response => {
      if (!response.ok) {
        return response.json().then(data => {
          throw new Error(data.error || 'Error deleting course');
        });
      }
      return response.json();
    })
    .then(data => {
      location.reload();
    })
    .catch(error => {
      alert('Error: ' + error.message);
    });
  }
}
