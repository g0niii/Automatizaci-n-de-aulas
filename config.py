"""
Configuración global del generador IMSCC para Canvas LMS.
Define rutas, constantes del estándar Common Cartridge y parámetros de diseño.
"""

import os
from pathlib import Path

# ============================================================================
# RUTAS DEL PROYECTO
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATES_DIR = BASE_DIR / "templates"

# Subdirectorios de entrada
DOCX_DIR = INPUT_DIR  # Los .docx se colocan directamente en input/
MEDIA_DIR = INPUT_DIR / "media"

# Archivo de instrucciones por defecto
DEFAULT_STRUCTURE_FILE = INPUT_DIR / "estructura.xlsx"

# ============================================================================
# CONSTANTES IMS COMMON CARTRIDGE 1.1
# ============================================================================

CC_VERSION = "1.1.0"
CC_SCHEMA = "IMS Common Cartridge"

# Namespaces XML
CC_NAMESPACES = {
    "": "http://www.imsglobal.org/xsd/imscc_v1p1/imscp_v1p1",
    "lom": "http://ltsc.ieee.org/xsd/imscc_v1p1/LOM/resource",
    "lomimscc": "http://ltsc.ieee.org/xsd/imscc_v1p1/LOM/manifest",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

CC_SCHEMA_LOCATION = (
    "http://www.imsglobal.org/xsd/imscc_v1p1/imscp_v1p1 "
    "http://www.imsglobal.org/profile/cc/ccv1p1/ccv1p1_imscp_v1p2_v1p0.xsd "
    "http://ltsc.ieee.org/xsd/imscc_v1p1/LOM/resource "
    "http://www.imsglobal.org/profile/cc/ccv1p1/LOM/ccv1p1_lomresource_v1p0.xsd "
    "http://ltsc.ieee.org/xsd/imscc_v1p1/LOM/manifest "
    "http://www.imsglobal.org/profile/cc/ccv1p1/LOM/ccv1p1_lommanifest_v1p0.xsd"
)

# Tipos de recursos Common Cartridge
RESOURCE_TYPES = {
    "pagina": "webcontent",
    "archivo": "webcontent",
    "url_externa": "imswl_xmlv1p1",
    "evaluacion": "imsqti_xmlv1p2/imscc_xmlv1p1/assessment",
    "foro": "imsdt_xmlv1p1",
    "tarea": "associatedcontent/imscc_xmlv1p1/learning-application-resource",
}

# ============================================================================
# EXTENSIONES MULTIMEDIA SOPORTADAS
# ============================================================================

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".ogg", ".avi", ".mov"}
AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".aac", ".flac"}
DOCUMENT_EXTENSIONS = {".pdf", ".pptx", ".ppt", ".xlsx", ".xls", ".doc", ".docx"}

ALL_MEDIA_EXTENSIONS = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS | AUDIO_EXTENSIONS | DOCUMENT_EXTENSIONS

# ============================================================================
# DISEÑO INSTITUCIONAL — PALETA DE COLORES Y TIPOGRAFÍA
# ============================================================================

# Paleta de Colores Institucional (Extraída de tus aulas base)
COLORS = {
    "educacion": {
        "primary": "#003087",      # Azul UCC
        "secondary": "#d3d3d3",    # Gris fondo
        "accent": "#000000",       # Negro
        "text": "#1a202c",
        "white": "#ffffff"
    },
    "posgrado": {
        "primary": "#922E1F",      # Rojo Posgrado
        "secondary": "#38728F",    # Azul secundario
        "accent": "#747672",       # Gris
        "text": "#1a202c",
        "white": "#ffffff"
    }
}

# Tipografías (Extraídas de tus aulas base)
FONTS = {
    "heading": "'Lato', 'Montserrat', 'Helvetica Neue', Helvetica, Arial, sans-serif",
    "body": "'Open Sans', 'Lato', sans-serif",
}

# ============================================================================
# CONFIGURACIÓN DE GENERACIÓN
# ============================================================================

# Prefijo para los identificadores únicos en el manifiesto
ID_PREFIX = "CANVAS_GEN"

# Tamaño máximo de imagen (ancho en px) para redimensionar dentro del paquete
MAX_IMAGE_WIDTH = 1200

# Calidad de compresión JPEG para imágenes procesadas
JPEG_QUALITY = 85

# Encoding
ENCODING = "UTF-8"
