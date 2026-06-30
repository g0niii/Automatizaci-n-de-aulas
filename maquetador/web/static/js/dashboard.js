document.addEventListener('DOMContentLoaded', function() {
  const dragZone = document.getElementById('drag-zone');
  const fileInput = document.getElementById('file-input');
  const temaSelector = document.getElementById('tema-selector');
  const temaDisplay = document.getElementById('tema-display');

  // Menú hamburguesa (presente en todas las páginas con header)
  const hamburgerBtn = document.getElementById('hamburger-btn');
  const mobileMenu = document.getElementById('mobile-menu');
  if (hamburgerBtn && mobileMenu) {
    hamburgerBtn.addEventListener('click', function() {
      mobileMenu.classList.toggle('active');
    });
    document.querySelectorAll('.mobile-nav-item').forEach(function(item) {
      item.addEventListener('click', function() {
        mobileMenu.classList.remove('active');
      });
    });
  }

  // Drag-and-drop: solo en páginas que tienen la zona de carga (Dashboard)
  if (dragZone) {
    const dragZoneButton = document.getElementById('btn-seleccionar');

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
        enviarArchivo(files[0]);
      }
    });

    dragZoneButton.addEventListener('click', function() {
      fileInput.click();
    });

    fileInput.addEventListener('change', function() {
      if (fileInput.files.length > 0) {
        enviarArchivo(fileInput.files[0]);
      }
    });
  }

  // Selector de tema (presente en todas las páginas con header)
  if (temaSelector) {
    temaSelector.addEventListener('change', function() {
      const tema = temaSelector.value;
      if (temaDisplay) {
        temaDisplay.textContent = tema;
      }

      fetch('/api/set-tema', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ tema: tema })
      })
      .catch(error => console.error('Error setting theme:', error));
    });
  }

  // Carga el archivo en el input y envía el formulario nativo a /subir.
  // El backend redirige a la página del plan (flujo server-side existente).
  function enviarArchivo(file) {
    if (!file.name.toLowerCase().endsWith('.zip')) {
      alert('Subí un archivo .zip con la carpeta del curso.');
      return;
    }
    // Para drag-and-drop: meter el archivo soltado en el input antes de enviar.
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;

    dragZone.classList.add('loading');
    dragZone.submit();
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
