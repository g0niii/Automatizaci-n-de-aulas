"""
Motor de Segmentación DOCX - VERSIÓN OJO HALCÓN.
Detecta numeraciones (1.1, 1.2...) incluso en texto plano.
"""

import os
import re
import logging
from bs4 import BeautifulSoup
import mammoth

logger = logging.getLogger("docx_splitter")

def extract_section_by_title(docx_path, target_title, next_title=None):
    """
    Extrae contenido buscando el patrón del título (ej: '1.1.') al inicio del texto.
    """
    if not os.path.exists(docx_path):
        logger.error(f"No existe el archivo: {docx_path}")
        return ""

    with open(docx_path, "rb") as docx_file:
        # Convertimos conservando el estilo de negrita para ayudar a identificar títulos
        result = mammoth.convert_to_html(docx_file)
        full_html = result.value
        
    soup = BeautifulSoup(full_html, "html.parser")
    
    # Función para limpiar y normalizar texto de búsqueda
    def get_search_pattern(title):
        if not title: return None
        # Extraer el número inicial si existe (ej: "1.1.")
        match = re.match(r'^(\d+\.\d+\.?)', title.strip())
        if match:
            return match.group(1)
        # Si no hay número, usamos las primeras 4 palabras
        words = title.split()[:4]
        return " ".join(words).lower()

    start_pattern = get_search_pattern(target_title)
    next_pattern = get_search_pattern(next_title) if next_title else None
    
    logger.info(f"Buscando patrón de inicio: '{start_pattern}'")
    
    all_elements = soup.find_all(recursive=False)
    final_nodes = []
    started = False
    
    for el in all_elements:
        text = el.get_text().strip().lower()
        
        # Detectar inicio
        if not started:
            # Si el target es Introducción
            if "introducción" in target_title.lower() and "introducción" in text[:20]:
                started = True
            # Si el target tiene numeración
            elif start_pattern and text.startswith(start_pattern.lower()):
                started = True
            
            if started:
                final_nodes.append(el)
                continue

        # Detectar fin
        if started and next_pattern:
            if text.startswith(next_pattern.lower()):
                break
            # Caso especial: si el próximo es un número pero no sabemos cuál
            # pero el actual es una numeración distinta, también podría ser el fin
            if re.match(r'^\d+\.\d+\.?', text) and not text.startswith(start_pattern.lower()):
                break
        
        if started:
            final_nodes.append(el)
            
    return "".join([str(n) for n in final_nodes])
