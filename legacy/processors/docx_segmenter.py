"""
Segmentador inteligente de DOCX para UCC.
Convierte un DOCX de módulo a HTML y lo segmenta en secciones
basándose en los encabezados (h1) y patrones de numeración.
"""

import re
import logging
from pathlib import Path
from bs4 import BeautifulSoup, Tag
import mammoth

logger = logging.getLogger("docx_segmenter")


def docx_to_html(docx_path: Path) -> str:
    """Convierte DOCX a HTML usando mammoth."""
    with open(docx_path, "rb") as f:
        result = mammoth.convert_to_html(f)
    if result.messages:
        for msg in result.messages:
            logger.warning(f"  mammoth: {msg}")
    return result.value


def segment_module_docx(docx_path: Path) -> dict:
    """
    Segmenta un DOCX de módulo en secciones.
    
    Retorna un dict con claves como:
      - "intro": HTML de la introducción (texto + objetivos)
      - "1.1": HTML de la sección 1.1
      - "1.2": HTML de la sección 1.2
      - etc.
      - "conclusion": HTML de la conclusión (si existe)
      - "referencias": HTML de las referencias (si existe)
    """
    full_html = docx_to_html(docx_path)
    soup = BeautifulSoup(full_html, "html.parser")
    elements = soup.find_all(recursive=False)
    
    sections = {}
    current_key = None
    current_elements = []
    
    # Patrones para detectar secciones
    section_pattern = re.compile(r'^(\d+\.\d+)\.?\s')
    
    for i, el in enumerate(elements):
        text = el.get_text().strip()
        
        # Saltar tabla de metadatos inicial
        if i == 0 and el.name == "table":
            continue
        
        # Detectar "Introducción" (texto bold sin ser h1)
        if current_key is None and _is_intro_header(el, text):
            current_key = "intro"
            current_elements = []
            continue  # No incluir el encabezado "Introducción" como texto
        
        # Detectar "Objetivos del módulo" - agregar a intro
        if current_key == "intro" and _is_objectives_header(el, text):
            current_key = "objetivos_in_intro"
            # Guardar lo que tenemos de intro
            sections["intro_text"] = _elements_to_html(current_elements)
            current_elements = []
            continue
        
        # Detectar secciones numeradas (1.1, 1.2, etc.)
        match = None
        if el.name in ["h1", "h2", "h3"]:
            match = section_pattern.match(text)
        elif el.name == "p" and el.find("strong"):
            match = section_pattern.match(text)
        
        if match:
            # Guardar sección anterior
            _save_section(sections, current_key, current_elements)
            
            current_key = match.group(1)
            current_elements = [el]
            continue
        
        # Detectar "Conclusión"
        if el.name in ["h1", "h2"] and "conclusi" in text.lower():
            _save_section(sections, current_key, current_elements)
            current_key = "conclusion"
            current_elements = []
            continue
        
        # Detectar "Referencias"
        if el.name in ["h1", "h2"] and "referencia" in text.lower():
            _save_section(sections, current_key, current_elements)
            current_key = "referencias"
            current_elements = []
            continue
        
        if current_key is not None:
            current_elements.append(el)
    
    # Guardar última sección
    _save_section(sections, current_key, current_elements)
    
    # Combinar intro_text y objetivos en "intro"
    intro_text = sections.pop("intro_text", "")
    objetivos = sections.pop("objetivos_in_intro", "")
    if intro_text or objetivos:
        sections["intro"] = intro_text
        sections["objetivos"] = objetivos
    
    # Log de resultados
    for key, html in sections.items():
        chars = len(html) if html else 0
        logger.info(f"  Seccion '{key}': {chars} chars")
    
    return sections


def _is_intro_header(el, text: str) -> bool:
    """Detecta si un elemento es el encabezado de Introducción."""
    clean = text.lower().strip()
    if clean.startswith("introducci"):
        if el.name in ["h1", "h2", "h3"]:
            return True
        if el.find("strong"):
            return True
    return False


def _is_objectives_header(el, text: str) -> bool:
    """Detecta si un elemento es el encabezado de Objetivos."""
    clean = text.lower().strip()
    if "objetivo" in clean:
        if el.name in ["h1", "h2", "h3"]:
            return True
        if el.find("strong"):
            return True
    return False


def _save_section(sections: dict, key: str, elements: list):
    """Guarda una sección en el dict."""
    if key is None:
        return
    html = _elements_to_html(elements)
    if key == "objetivos_in_intro":
        sections[key] = html
    elif key in sections:
        sections[key] += html
    else:
        sections[key] = html


def _elements_to_html(elements: list) -> str:
    """Convierte una lista de elementos BS4 a HTML string."""
    return "".join(str(el) for el in elements)
