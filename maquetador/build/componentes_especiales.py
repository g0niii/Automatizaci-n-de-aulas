# -*- coding: utf-8 -*-
"""Componentes especiales dinámicos para el maquetador IMSCC.

Implementa procesadores para:
  - Flipcards: tarjetas de doble cara (frente/reverso)
  - Acordeones: secciones colapsables
  - Tabs: interfaz con solapas

Cada componente se parsea del HTML de entrada y se transforma
en estructura HTML/CSS con interactividad vía JavaScript.
"""

import re
from typing import Optional


def aplicar_flipcards(html_content: str) -> str:
    """Transforma <div class="flipcard"> en tarjetas interactivas de doble cara.

    Estructura esperada en HTML:
      <div class="flipcard">
        <div class="flipcard-front">Frente de tarjeta</div>
        <div class="flipcard-back">Reverso de tarjeta</div>
      </div>

    Output: HTML con CSS y JavaScript para volteo interactivo.

    Args:
        html_content: HTML con divs flipcard

    Returns:
        HTML transformado con flipcards funcionales
    """
    if not html_content or "flipcard" not in html_content:
        return html_content

    # Patrón para capturar flipcard completo (con conteo balanceado de divs)
    # Estrategia: encontrar <div class="flipcard">, luego capturar hasta el </div> balanceado
    pattern = r'<div\s+class="flipcard"[^>]*>(.+?)<div\s+class="flipcard-back"[^>]*>(.+?)</div>\s*</div>'

    def procesar_flipcard(match):
        # Extraer contenido entre <div class="flipcard"> y <div class="flipcard-back">
        antes_reverso = match.group(1)
        reverso = match.group(2).strip()

        # Extraer frente del antes_reverso
        frente_match = re.search(
            r'<div\s+class="flipcard-front"[^>]*>(.+?)</div>',
            antes_reverso,
            re.DOTALL
        )
        frente = frente_match.group(1).strip() if frente_match else ""

        # Construir tarjeta interactiva
        html_tarjeta = f'''<div class="flipcard-container" data-component="flipcard">
  <div class="flipcard-inner" onclick="this.classList.toggle('flipped')">
    <div class="flipcard-face flipcard-front">
      {frente}
    </div>
    <div class="flipcard-face flipcard-back">
      {reverso}
    </div>
  </div>
  <p class="flipcard-hint">Haz clic para ver el reverso</p>
</div>'''

        return html_tarjeta

    resultado = re.sub(pattern, procesar_flipcard, html_content, flags=re.DOTALL)

    # Inyectar CSS si no está presente
    if "flipcard-container" in resultado and ".flipcard-face" not in resultado:
        css_flipcard = _generar_css_flipcard()
        resultado = css_flipcard + resultado

    return resultado


def _generar_css_flipcard() -> str:
    """Genera CSS para flipcards."""
    return """<style>
.flipcard-container {
  perspective: 1000px;
  margin: 16px 0;
}

.flipcard-inner {
  position: relative;
  width: 100%;
  min-height: 200px;
  transition: transform 0.6s;
  transform-style: preserve-3d;
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
}

.flipcard-inner.flipped {
  transform: rotateY(180deg);
}

.flipcard-face {
  position: absolute;
  width: 100%;
  height: 100%;
  padding: 20px;
  backface-visibility: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-weight: 500;
  text-align: center;
}

.flipcard-front {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  transform: rotateY(0deg);
}

.flipcard-back {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  transform: rotateY(180deg);
}

.flipcard-hint {
  text-align: center;
  font-size: 12px;
  color: #999;
  margin-top: 8px;
  font-style: italic;
}
</style>"""


def aplicar_acordeon(html_content: str) -> str:
    """Transforma <div class="acordeon"> en secciones colapsables.

    Estructura esperada en HTML:
      <div class="acordeon">
        <div class="acordeon-item">
          <div class="acordeon-titulo">Título de sección</div>
          <div class="acordeon-contenido">Contenido...</div>
        </div>
        <div class="acordeon-item">
          ...
        </div>
      </div>

    Output: HTML con CSS y JavaScript para colapso/expansión.

    Args:
        html_content: HTML con divs acordeon

    Returns:
        HTML transformado con acordeones funcionales
    """
    if not html_content or "acordeon" not in html_content:
        return html_content

    # Patrón para capturar acordeon completo (matching balanceado de divs)
    # Usar contador de divs para encontrar el cierre correcto
    items_html = []
    resultado = html_content

    # Buscar cada <div class="acordeon">
    acordeon_pattern = r'<div\s+class="acordeon"[^>]*>(.*?)\n</div>'

    def procesar_acordeon(match):
        contenido = match.group(1)

        # Encontrar todos los acordeon-item dentro de este acordeón
        item_pattern = r'<div\s+class="acordeon-item"[^>]*>(.+?)</div>'
        items_encontrados = re.findall(item_pattern, contenido, re.DOTALL)

        items_html_list = []
        for idx, item_contenido in enumerate(items_encontrados):
            # Extraer título
            titulo_match = re.search(
                r'<div\s+class="acordeon-titulo"[^>]*>(.+?)</div>',
                item_contenido,
                re.DOTALL
            )
            # Extraer contenido
            contenido_match = re.search(
                r'<div\s+class="acordeon-contenido"[^>]*>(.+?)</div>',
                item_contenido,
                re.DOTALL
            )

            titulo = titulo_match.group(1).strip() if titulo_match else "Sección"
            contenido_item = (
                contenido_match.group(1).strip()
                if contenido_match else ""
            )

            # Construir item del acordeón
            item_html = f'''<div class="acordeon-item" data-accordion-item="{idx}">
  <button class="acordeon-boton" onclick="toggleAcordeon(this)">
    <span class="acordeon-titulo-texto">{titulo}</span>
    <span class="acordeon-icono">▼</span>
  </button>
  <div class="acordeon-contenido" style="display: none;">
    {contenido_item}
  </div>
</div>'''
            items_html_list.append(item_html)

        # Construir acordeón completo
        html_acordeon = f'''<div class="acordeon-container" data-component="acordeon">
{''.join(items_html_list)}
</div>'''

        return html_acordeon

    resultado = re.sub(acordeon_pattern, procesar_acordeon, resultado, flags=re.DOTALL)

    # Inyectar CSS y JS si no está presente
    if "acordeon-container" in resultado and "toggleAcordeon" not in resultado:
        css_acordeon = _generar_css_acordeon()
        js_acordeon = _generar_js_acordeon()
        resultado = css_acordeon + js_acordeon + resultado

    return resultado


def _generar_css_acordeon() -> str:
    """Genera CSS para acordeones."""
    return """<style>
.acordeon-container {
  border: 1px solid #ddd;
  border-radius: 8px;
  margin: 16px 0;
  overflow: hidden;
}

.acordeon-item {
  border-bottom: 1px solid #ddd;
}

.acordeon-item:last-child {
  border-bottom: none;
}

.acordeon-boton {
  width: 100%;
  padding: 16px;
  background: #f5f5f5;
  border: none;
  text-align: left;
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 14px;
  transition: background-color 0.2s;
}

.acordeon-boton:hover {
  background: #ececec;
}

.acordeon-icono {
  transition: transform 0.3s;
  display: inline-block;
  font-size: 12px;
}

.acordeon-item:not(.active) .acordeon-icono {
  transform: rotate(-90deg);
}

.acordeon-contenido {
  padding: 16px;
  background: #fafafa;
  line-height: 1.6;
}
</style>"""


def _generar_js_acordeon() -> str:
    """Genera JavaScript para acordeones."""
    return """<script>
function toggleAcordeon(boton) {
  const item = boton.parentElement;
  const contenido = item.querySelector('.acordeon-contenido');
  const estoyAbierto = item.classList.contains('active');

  // Cerrar todos los items si se abre uno (solo un item abierto)
  const contenedor = item.closest('.acordeon-container');
  contenedor.querySelectorAll('.acordeon-item.active').forEach(it => {
    if (it !== item) {
      it.classList.remove('active');
      it.querySelector('.acordeon-contenido').style.display = 'none';
    }
  });

  // Toggle del item actual
  if (estoyAbierto) {
    item.classList.remove('active');
    contenido.style.display = 'none';
  } else {
    item.classList.add('active');
    contenido.style.display = 'block';
  }
}
</script>"""


def aplicar_tabs(html_content: str) -> str:
    """Transforma <div class="tabs"> en interfaz con solapas.

    Estructura esperada en HTML:
      <div class="tabs">
        <div class="tab" data-tab-name="Tab 1">
          Contenido de Tab 1
        </div>
        <div class="tab" data-tab-name="Tab 2">
          Contenido de Tab 2
        </div>
      </div>

    Output: HTML con CSS y JavaScript para navegación entre tabs.

    Args:
        html_content: HTML con divs tabs

    Returns:
        HTML transformado con tabs funcionales
    """
    if not html_content or '<div class="tabs"' not in html_content:
        return html_content

    # Patrón para capturar tabs completo
    # Usar búsqueda basada en contador de divs para evitar confusión con divs internos
    pattern = r'<div\s+class="tabs"[^>]*>(.+?)\n</div>'

    def procesar_tabs(match):
        contenido = match.group(1)

        # Encontrar todos los tab
        tabs_pattern = r'<div\s+class="tab"[^>]*data-tab-name="([^"]*)"[^>]*>(.*?)</div>'
        tabs_encontrados = re.findall(tabs_pattern, contenido, re.DOTALL)

        if not tabs_encontrados:
            return match.group(0)

        # Generar botones de navegación
        botones_html = '<div class="tabs-navbar">'
        tabs_contenido_html = '<div class="tabs-content">'

        for idx, (tab_nombre, tab_contenido) in enumerate(tabs_encontrados):
            # Botón
            activo_class = ' active' if idx == 0 else ''
            botones_html += (
                f'<button class="tab-boton{activo_class}" '
                f'onclick="abrirTab(event, \'tab-{idx}\')">{tab_nombre}</button>'
            )

            # Contenido
            display = 'block' if idx == 0 else 'none'
            tabs_contenido_html += (
                f'<div id="tab-{idx}" class="tab-panel" style="display: {display};">'
                f'{tab_contenido.strip()}</div>'
            )

        botones_html += '</div>'
        tabs_contenido_html += '</div>'

        # Construir tabs completo
        html_tabs = f'''<div class="tabs-container" data-component="tabs">
  {botones_html}
  {tabs_contenido_html}
</div>'''

        return html_tabs

    resultado = re.sub(pattern, procesar_tabs, html_content, flags=re.DOTALL)

    # Inyectar CSS y JS si no está presente
    if "tabs-container" in resultado and "abrirTab" not in resultado:
        css_tabs = _generar_css_tabs()
        js_tabs = _generar_js_tabs()
        resultado = css_tabs + js_tabs + resultado

    return resultado


def _generar_css_tabs() -> str:
    """Genera CSS para tabs."""
    return """<style>
.tabs-container {
  margin: 16px 0;
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
}

.tabs-navbar {
  display: flex;
  background: #f5f5f5;
  border-bottom: 2px solid #ddd;
  flex-wrap: wrap;
}

.tab-boton {
  flex: 1;
  padding: 12px 16px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  color: #666;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
  white-space: nowrap;
}

.tab-boton:hover {
  background: #ececec;
  color: #333;
}

.tab-boton.active {
  color: #0066cc;
  border-bottom-color: #0066cc;
  background: white;
}

.tabs-content {
  background: white;
}

.tab-panel {
  padding: 16px;
  line-height: 1.6;
}
</style>"""


def _generar_js_tabs() -> str:
    """Genera JavaScript para tabs."""
    return """<script>
function abrirTab(evt, nombreTab) {
  // Ocultar todos los tab-panel
  const contenedor = evt.target.closest('.tabs-container');
  contenedor.querySelectorAll('.tab-panel').forEach(panel => {
    panel.style.display = 'none';
  });

  // Desactivar todos los botones
  contenedor.querySelectorAll('.tab-boton').forEach(boton => {
    boton.classList.remove('active');
  });

  // Mostrar el tab seleccionado
  const tabPanel = contenedor.querySelector('#' + nombreTab);
  if (tabPanel) {
    tabPanel.style.display = 'block';
  }

  // Activar el botón clickeado
  evt.target.classList.add('active');
}
</script>"""


def procesar_componentes_especiales(html_content: str) -> str:
    """Aplica todos los procesadores de componentes especiales.

    Flujo:
      1. flipcards
      2. acordeones
      3. tabs

    Args:
        html_content: HTML con componentes especiales

    Returns:
        HTML transformado con todos los componentes funcionales
    """
    resultado = html_content

    # Aplicar en orden
    resultado = aplicar_flipcards(resultado)
    resultado = aplicar_acordeon(resultado)
    resultado = aplicar_tabs(resultado)

    return resultado
