# Plan de Implementación: Dashboard Moderno para Maquetador UCC

> **Para trabajadores autónomos:** REQUERIDO: Usar superpowers:subagent-driven-development o superpowers:executing-plans para implementar tarea por tarea.

**Objetivo:** Rediseñar la interfaz web del maquetador con un dashboard moderno que tenga: barra lateral fija (navegación + selector de tema), zona central grande (arrastra ZIP aquí), y tarjetas de cursos con botones de acciones.

**Arquitectura:** Reemplazamos el formulario simple actual con un diseño de dos columnas: sidebar fijo a la izquierda (ancho 220px) y área principal flexible (arrastra-zona + tarjetas). Todos los estilos van en CSS nuevo, la estructura en HTML, y la interactividad en JavaScript vanilla. El backend Flask casi no cambia.

**Stack técnico:** Flask (existente), Jinja2 (existente), CSS/JavaScript vanilla (sin nuevas dependencias), drag-and-drop nativo del navegador.

## Restricciones globales

- Mantener compatibilidad con rutas Flask existentes
- Soportar temas: educacion y posgrado
- Mantener funcionalidad de upload ZIP (solo cambiar UI)
- Tarjetas deben mostrar: nombre, tema, cantidad módulos, cantidad items, estado, botones de acciones
- Sidebar fijo al scroll
- Aceptar solo archivos .zip
- No es necesario responsive mobile (es herramienta interna)

---

## Estructura de archivos

**Crear:**
- `maquetador/web/static/css/dashboard.css` — Estilos: sidebar, área principal, tarjetas, zona arrastra
- `maquetador/web/static/js/dashboard.js` — Drag-and-drop, selector tema, acciones de cursos
- `maquetador/web/templates/dashboard.html` — Template nuevo con sidebar + tarjetas

**Modificar:**
- `maquetador/web/app.py` — Actualizar ruta GET / para renderizar dashboard.html

---

### Tarea 1: Crear CSS del Dashboard (Layout + Estilos)

**Archivos:**
- Crear: `maquetador/web/static/css/dashboard.css`

**Qué consume:** Nada (archivo nuevo)
**Qué produce:** Clases CSS: `.sidebar`, `.main-area`, `.drag-zone`, `.course-card`, `.course-action`

- [ ] **Paso 1: Crear dashboard.css con todo el layout**

Crear archivo `maquetador/web/static/css/dashboard.css` con estos estilos:

```css
/* Sidebar - Navegación a la izquierda */
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  width: 220px;
  height: 100vh;
  background: #1b1e31;
  color: #fff;
  padding: 20px;
  box-sizing: border-box;
  overflow-y: auto;
  z-index: 100;
}

.sidebar h1 {
  font-size: 18px;
  margin: 0 0 30px 0;
  font-weight: 600;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  color: #cfd6e4;
  cursor: pointer;
  font-size: 14px;
  gap: 10px;
  transition: color 0.2s;
}

.nav-item:hover {
  color: #fff;
}

/* Selector de tema en sidebar */
.theme-selector {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid #444;
}

.theme-selector label {
  display: block;
  font-size: 12px;
  color: #aaa;
  margin-bottom: 8px;
  font-weight: 600;
}

.theme-selector select {
  width: 100%;
  padding: 8px;
  border: 1px solid #555;
  border-radius: 4px;
  background: #2a2d42;
  color: #fff;
  font-size: 13px;
}

/* Área principal (corrida a la derecha del sidebar) */
.main-area {
  margin-left: 220px;
  padding: 30px;
  background: #f4f5f7;
  min-height: 100vh;
}

.main-header {
  margin-bottom: 30px;
}

.main-header h2 {
  font-size: 24px;
  margin: 0;
  color: #1a202c;
}

/* Zona de ARRASTRA ZIP */
.drag-zone {
  background: #fff;
  border: 2px dashed #003087;
  border-radius: 8px;
  padding: 60px 20px;
  text-align: center;
  cursor: pointer;
  margin-bottom: 40px;
  transition: background 0.2s, border-color 0.2s;
}

.drag-zone:hover {
  background: #f9fafb;
  border-color: #0047bf;
}

.drag-zone.dragover {
  background: #e8f0ff;
  border-color: #0047bf;
}

.drag-zone-icon {
  font-size: 48px;
  margin-bottom: 15px;
}

.drag-zone-text {
  font-size: 18px;
  font-weight: 600;
  color: #1a202c;
  margin-bottom: 5px;
}

.drag-zone-subtext {
  font-size: 13px;
  color: #666;
  margin-bottom: 15px;
}

.drag-zone-button {
  background: #003087;
  color: #fff;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  font-weight: 600;
}

.drag-zone-button:hover {
  background: #0047bf;
}

.drag-zone input[type="file"] {
  display: none;
}

.current-theme {
  font-size: 12px;
  color: #666;
  margin-top: 10px;
}

/* Tarjetas de cursos */
.courses-section {
  margin-top: 40px;
}

.courses-title {
  font-size: 16px;
  font-weight: 600;
  color: #1a202c;
  margin-bottom: 20px;
}

.courses-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.course-card {
  background: #fff;
  border: 1px solid #d8dce3;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: box-shadow 0.2s, border-color 0.2s;
}

.course-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #b8860b;
}

.course-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.course-name {
  font-size: 15px;
  font-weight: 600;
  color: #1a202c;
  flex: 1;
}

.course-theme {
  font-size: 11px;
  background: #f0f1f3;
  color: #666;
  padding: 4px 8px;
  border-radius: 3px;
  white-space: nowrap;
}

.course-info {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #666;
  margin-bottom: 15px;
}

.course-status {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #1e7e34;
}

.course-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.course-action {
  flex: 1;
  min-width: 70px;
  padding: 8px 12px;
  border: 1px solid #003087;
  background: #fff;
  color: #003087;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s, color 0.2s;
  text-align: center;
}

.course-action:hover {
  background: #003087;
  color: #fff;
}

.course-action.danger {
  border-color: #b02a37;
  color: #b02a37;
}

.course-action.danger:hover {
  background: #b02a37;
  color: #fff;
}

/* Loading */
.loading {
  opacity: 0.6;
  pointer-events: none;
}
```

- [ ] **Paso 2: Verificar que el archivo existe**
- [ ] **Paso 3: Hacer commit**

---

### Tarea 2: Crear Template HTML del Dashboard

**Archivos:**
- Crear: `maquetador/web/templates/dashboard.html`

**Qué consume:** Lista `courses` desde Flask (cada uno con: nombre, codigo, tema, módulos, items, status)
**Qué produce:** HTML del sidebar + zona arrastra + tarjetas de cursos

Crear archivo con el sidebar, zona de arrastra, y tarjetas de cursos como se especifica en el plan.

---

### Tarea 3: Crear JavaScript (Drag-and-drop + Interacciones)

**Archivos:**
- Crear: `maquetador/web/static/js/dashboard.js`

**Qué consume:** Elementos HTML con IDs específicos
**Qué produce:** Event handlers para drag-and-drop, upload de archivos, cambio de tema, acciones en cursos

Implementar drag-and-drop, selector de tema, y acciones de cursos como se especifica en el plan.

---

### Tarea 4: Actualizar Rutas Flask para Servir Dashboard

**Archivos:**
- Modificar: `maquetador/web/app.py`

**Qué consume:** App Flask existente, archivos de cursos en `output/planes/`
**Qué produce:** Ruta GET / que renderiza dashboard.html con lista de cursos

Actualizar la ruta GET / para renderizar el nuevo dashboard.html en lugar del template anterior.

---

### Tarea 5: Agregar Endpoints API para Acciones de Cursos

**Archivos:**
- Modificar: `maquetador/web/app.py`

**Qué consume:** Archivos de cursos en `output/planes/`
**Qué produce:** Endpoints: POST /api/set-tema, DELETE /api/course/<id>

Agregar dos nuevos endpoints para tema y eliminación de cursos.

---

### Tarea 6: Verificación e Integración (Probar Todo)

**Archivos:**
- Test: Navegador en http://localhost:5000

**Qué consume:** Todas las tareas anteriores
**Qué produce:** Dashboard funcional en el navegador

Probar drag-and-drop, selector de tema, botones de cursos, verificar que todo funciona.
