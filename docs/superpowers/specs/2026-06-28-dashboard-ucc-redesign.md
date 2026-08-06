# Dashboard Maquetador UCC - Rediseño Corporativo

> **Objetivo:** Rediseñar el dashboard actual con identidad visual corporativa UCC, header horizontal responsivo, y mantener toda la funcionalidad existente.

**Alcance:** Reemplazar sidebar fijo + drag-zone con header horizontal tipo UCC + contenido responsivo. Actualizar colores y tipografía a estilo corporativo.

**Tech Stack:** Mismo (Flask, Jinja2, CSS vanilla, JavaScript vanilla). Sin dependencias nuevas.

---

## Global Constraints

- Colores UCC exactos: #003087 (azul marino), #00BFA5 (turquesa), #ffffff (blanco), grises (#333, #666, #f5f5f5)
- Responsive: mobile (<768px), tablet (768-1024px), desktop (>1024px)
- Mantener funcionalidad: drag-and-drop, selector tema, acciones cursos (editar, eliminar)
- Tipografía sans-serif: Segoe UI, Arial, sans-serif fallback
- Hamburger menu en mobile (nav items colapsado)

---

## Estructura de Archivos

**Modificar:**
- `maquetador/web/static/css/dashboard.css` — Reescribir completamente con estilos UCC
- `maquetador/web/templates/dashboard.html` — Actualizar estructura: header horizontal + contenido

**No tocar:**
- `maquetador/web/app.py` — Rutas y endpoints
- `maquetador/web/static/js/dashboard.js` — Funcionalidad (solo actualizar selectores si es necesario)

---

## SECCIÓN 1: Header (Navegación)

### Estructura HTML
```
<header class="header">
  <div class="header-container">
    <!-- Left: Logo + Brand -->
    <div class="header-logo">
      <img src="logo-ucc.png" alt="UCC">
      <span>Maquetador</span>
    </div>
    
    <!-- Center: Nav Items -->
    <nav class="header-nav">
      <a href="#" class="nav-item active">Dashboard</a>
      <a href="#" class="nav-item">Cursos</a>
      <a href="#" class="nav-item">Configuración</a>
    </nav>
    
    <!-- Right: Theme + Profile -->
    <div class="header-right">
      <select id="tema-selector" class="theme-select">
        <option value="educacion">Educación</option>
        <option value="posgrado">Posgrado</option>
      </select>
      
      <div class="profile-dropdown">
        <button class="profile-btn">👤 Perfil</button>
        <!-- Dropdown menu (logout, etc) -->
      </div>
    </div>
    
    <!-- Mobile: Hamburger -->
    <button class="hamburger-menu">☰</button>
  </div>
</header>
```

### Estilos CSS

**Header General:**
- `background: #003087` (azul UCC)
- `color: #ffffff`
- `padding: 16px 24px`
- `position: sticky; top: 0; z-index: 1000`
- `display: flex; align-items: center; justify-content: space-between`

**Logo/Brand:**
- Font: 18px bold
- Flex: 1 (left)
- Image + text juntos

**Nav Items:**
- Font: 14px, regular
- Padding: 8px 16px
- Hover: color #00BFA5 (turquesa)
- Active: color #00BFA5 + border-bottom turquesa
- Responsive: oculto en mobile (<768px)

**Theme Selector:**
- Background: white
- Border: 1px solid #00BFA5
- Padding: 8px 12px
- Border-radius: 4px
- Font-size: 12px

**Profile Dropdown:**
- Button: white background, #003087 text
- Dropdown menu: #f5f5f5 background
- Hover items: #00BFA5 highlight

**Hamburger Menu:**
- Display: none en desktop
- Display: block en mobile
- Font-size: 24px
- Background: transparent
- Border: none

---

## SECCIÓN 2: Contenido Principal

### Layout
```
<main class="main-content">
  <div class="content-container">
    <header class="page-header">
      <h1>Maquetador UCC - Cursos</h1>
    </header>
    
    <!-- Drag Zone -->
    <div class="drag-zone" id="drag-zone">
      ...
    </div>
    
    <!-- Courses Grid -->
    <section class="courses-section">
      <h2>Cursos disponibles</h2>
      <div class="courses-grid" id="courses-grid">
        <!-- Course cards -->
      </div>
    </section>
  </div>
</main>
```

### Estilos CSS

**Main Content:**
- `margin-top: 0` (header es sticky, no desplaza)
- `padding: 40px 24px`
- `background: #f5f5f5` (gris claro)
- `min-height: calc(100vh - 60px)` (viewport menos header)

**Page Header:**
- `h1: 32px bold, #003087`
- Margin-bottom: 30px

**Drag Zone:**
- Border: 2px dashed #00BFA5 (turquesa, no azul oscuro)
- Padding: 60px 20px
- Background: white
- Hover: background #f0f8ff (azul muy claro)
- `dragover` class: background #e0f7ff, border turquesa solid

**Drag Zone Button:**
- Background: #00BFA5 (turquesa)
- Color: white
- Hover: background #0099a1 (turquesa oscuro)
- Border: none
- Border-radius: 4px
- Padding: 12px 24px
- Font-size: 14px bold

**Courses Section:**
- h2: 20px bold, #003087
- Margin-top: 40px

**Courses Grid:**
- Desktop (>1024px): `grid-template-columns: repeat(3, 1fr)`
- Tablet (768-1024px): `grid-template-columns: repeat(2, 1fr)`
- Mobile (<768px): `grid-template-columns: 1fr`
- Gap: 24px

**Course Card:**
- Background: white
- Border: 1px solid #e0e0e0
- Border-radius: 8px
- Padding: 20px
- Box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08)
- Hover: box-shadow 0 4px 12px rgba(0, 48, 135, 0.15), border-color #00BFA5

**Course Card Buttons:**
- Border: 1px solid #00BFA5
- Background: white
- Color: #00BFA5
- Hover: background #00BFA5, color white
- Padding: 8px 16px
- Border-radius: 4px
- Font-size: 12px bold

**Course Card Buttons (Danger):**
- Border: 1px solid #d32f2f
- Color: #d32f2f
- Hover: background #d32f2f, color white

---

## SECCIÓN 3: Responsive Behavior

### Desktop (>1024px)
- Header items todos visibles
- Hamburger: display none
- Content padding: 40px 24px
- Grid: 3 columnas

### Tablet (768-1024px)
- Header items: algunos ocultos si no cabe (nav items en dropdown)
- Hamburger: display none
- Content padding: 32px 20px
- Grid: 2 columnas
- Font sizes: -2px

### Mobile (<768px)
- Header layout: logo | hamburger | profile
- Nav items: ocultos, mostrados en hamburger menu (vertical dropdown)
- Content padding: 20px 16px
- Grid: 1 columna
- Drag zone: full-width, padding reducido (40px 16px)
- Font sizes: -3px
- h1: 24px

---

## SECCIÓN 4: Color Palette (Exacta UCC)

| Nombre | Hex | Uso |
|--------|-----|-----|
| Azul UCC | #003087 | Headers, titles, primary text |
| Turquesa UCC | #00BFA5 | Buttons, hovers, accents |
| Blanco | #ffffff | Backgrounds, text on dark |
| Gris claro | #f5f5f5 | Page background |
| Gris texto | #333333 | Body text |
| Gris muted | #666666 | Secondary text |
| Gris border | #e0e0e0 | Card borders |
| Rojo danger | #d32f2f | Delete buttons |

---

## SECCIÓN 5: Typography

**Font Stack:** `Segoe UI, Arial, sans-serif`

| Elemento | Size | Weight | Color | Usage |
|----------|------|--------|-------|-------|
| h1 (main) | 32px | 700 | #003087 | Page titles |
| h2 (section) | 20px | 600 | #003087 | Section headers |
| h3 (card) | 16px | 600 | #333 | Card titles |
| Body text | 14px | 400 | #333 | Regular content |
| Small text | 12px | 400 | #666 | Metadata, hints |
| Button text | 12px | 700 | varies | Buttons |

---

## SECCIÓN 6: Interactive States

**Hover States:**
- Nav items: color #00BFA5
- Buttons: background #00BFA5, color white
- Cards: shadow turquesa, border turquesa
- Drag zone: background #f0f8ff

**Focus States:**
- Outline: 2px solid #00BFA5
- Offset: 2px

**Active States:**
- Nav active item: color #00BFA5, border-bottom #00BFA5
- Selected dropdown: background #f5f5f5

**Loading State:**
- Drag zone: opacity 0.6, pointer-events none
- Spinner: turquesa #00BFA5

---

## SECCIÓN 7: Mobile Menu (Hamburger)

**Structure:**
```
<div class="mobile-menu" style="display: none;">
  <nav class="mobile-nav">
    <a href="#" class="mobile-nav-item">Dashboard</a>
    <a href="#" class="mobile-nav-item">Cursos</a>
    <a href="#" class="mobile-nav-item">Configuración</a>
  </nav>
</div>
```

**Styles:**
- Position: absolute, top 60px, left 0, width 100%
- Background: #003087 (same as header)
- Flex-direction: column
- a: padding 12px 24px, color white, border-bottom 1px solid rgba(255,255,255,0.1)
- a:hover: background rgba(0, 191, 165, 0.2)

**JavaScript:**
- Hamburger click: toggle `display: block/none` on mobile-menu

---

## SECCIÓN 8: What Stays the Same

- Funcionalidad drag-and-drop (HTML5)
- Selector de tema (POST /api/set-tema)
- Acciones de cursos (editar, eliminar)
- JavaScript en dashboard.js (sin cambios)
- API endpoints (sin cambios)

---

## Success Criteria

✅ Dashboard se ve como UCC.edu.ar (colores, tipografía, header horizontal)
✅ Responsivo en mobile/tablet/desktop
✅ Todas las funciones funcionan (drag-drop, tema, acciones)
✅ No hay cambios en backend (app.py, endpoints)
✅ Hamburger menu funciona en mobile
✅ Transiciones suaves entre breakpoints

