"""
Lector de Planilla de Estructura UCC.
Adaptado al formato real de los asesores pedagógicos (Laura Conti, etc.).
"""

import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
import openpyxl

logger = logging.getLogger(__name__)

@dataclass
class UCCItem:
    modulo: str
    titulo: str
    referencia: Optional[str] = None  # Link o nombre de archivo
    tipo: str = "pagina"             # Detectado por el contexto (INTRO, ACTIVIDADES)
    comentarios: Optional[str] = None

def read_ucc_structure(filepath: Path) -> list:
    """
    Lee la planilla real de la UCC y extrae la jerarquía de módulos e ítems.
    """
    wb = openpyxl.load_workbook(str(filepath), data_only=True)
    ws = wb.active
    
    items = []
    current_modulo = "General"
    
    # Empezamos a leer desde la fila 2 (asumiendo que la 1 es el link de Drive)
    for row in ws.iter_rows(min_row=2):
        col_a = row[0].value
        col_b = row[1].value
        col_d = row[3].value # Link / Referencia
        
        # Si la columna A tiene texto, es un nuevo Módulo
        if col_a and "módulo" in str(col_a).lower():
            current_modulo = str(col_a).strip().replace("\n", " ")
        
        # Si la columna B tiene texto, es un ítem (página, actividad, etc.)
        if col_b:
            titulo = str(col_b).strip()
            
            # Detectar tipo por palabras clave en el título
            tipo = "pagina"
            if "introducción" in titulo.lower() or "introduccion" in titulo.lower():
                tipo = "introduccion"
            elif "actividades" in titulo.lower() or "actividad" in titulo.lower():
                tipo = "tarea"
            elif "video" in titulo.lower():
                tipo = "video"
            
            # Limpiar el link si existe
            referencia = str(col_d).strip() if col_d else None
            
            items.append(UCCItem(
                modulo=current_modulo,
                titulo=titulo,
                referencia=referencia,
                tipo=tipo
            ))
            
    return items
