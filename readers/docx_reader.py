"""
Lector de archivos DOCX.
Extrae contenido textual, headings, formato (negritas, cursivas, listas)
e imágenes embebidas desde archivos .docx.
"""

import logging
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import mammoth
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT

logger = logging.getLogger(__name__)


@dataclass
class ExtractedImage:
    """Imagen extraída de un documento DOCX."""
    filename: str       # Nombre de archivo generado
    content_type: str   # MIME type (image/png, image/jpeg, etc.)
    data: bytes         # Bytes de la imagen


@dataclass
class DocxContent:
    """Contenido extraído de un archivo DOCX."""
    html: str                                        # Contenido convertido a HTML
    plain_text: str                                  # Texto plano
    images: list[ExtractedImage] = field(default_factory=list)  # Imágenes embebidas
    title: Optional[str] = None                      # Título del documento (primer H1)


# Mapeo de content types a extensiones
CONTENT_TYPE_EXT = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/svg+xml": ".svg",
    "image/bmp": ".bmp",
    "image/webp": ".webp",
    "image/tiff": ".tiff",
}


def read_docx(filepath: Path, extract_images: bool = True) -> DocxContent:
    """
    Lee un archivo DOCX y extrae su contenido como HTML, texto plano e imágenes.

    Usa mammoth para una conversión HTML limpia y python-docx para
    extracción de imágenes embebidas.

    Args:
        filepath: Ruta al archivo .docx
        extract_images: Si True, extrae imágenes embebidas.

    Returns:
        DocxContent con HTML, texto e imágenes.

    Raises:
        FileNotFoundError: Si el archivo no existe.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"No se encontró el archivo DOCX: {filepath}")

    logger.info(f"Leyendo DOCX: {filepath.name}")

    images: list[ExtractedImage] = []
    image_counter = [0]  # Usamos lista para mutabilidad en closure

    def convert_image(image):
        """Callback para mammoth: convierte imágenes embebidas."""
        image_counter[0] += 1
        content_type = image.content_type

        with image.open() as img_stream:
            img_data = img_stream.read()

        # Generar nombre de archivo basado en hash para evitar colisiones
        img_hash = hashlib.md5(img_data).hexdigest()[:8]
        ext = CONTENT_TYPE_EXT.get(content_type, ".png")
        filename = f"img_{image_counter[0]:03d}_{img_hash}{ext}"

        extracted = ExtractedImage(
            filename=filename,
            content_type=content_type,
            data=img_data,
        )
        images.append(extracted)

        # Retornar referencia relativa que será reemplazada luego
        return {"src": f"$MEDIA_PATH$/{filename}"}

    # Convertir DOCX a HTML con mammoth
    with open(filepath, "rb") as f:
        result = mammoth.convert_to_html(
            f,
            convert_image=mammoth.images.img_element(convert_image) if extract_images else None,
            style_map=_get_style_map(),
        )

    html_content = result.value

    # Reportar mensajes/advertencias de la conversión
    if result.messages:
        for msg in result.messages:
            logger.warning(f"  mammoth [{msg.type}]: {msg.message}")

    # Extraer texto plano usando python-docx
    doc = Document(str(filepath))
    plain_text = "\n".join(
        para.text for para in doc.paragraphs if para.text.strip()
    )

    # Detectar título (primer heading)
    title = None
    for para in doc.paragraphs:
        if para.style and para.style.name and para.style.name.startswith("Heading"):
            title = para.text.strip()
            break

    content = DocxContent(
        html=html_content,
        plain_text=plain_text,
        images=images,
        title=title,
    )

    logger.info(
        f"  Extraído: {len(images)} imágenes, "
        f"{len(plain_text)} chars de texto, "
        f"título: '{title or 'N/A'}'"
    )

    return content


def _get_style_map() -> str:
    """
    Devuelve el mapeo de estilos para mammoth.
    Traduce estilos de Word a elementos HTML semánticos.
    """
    return """
        p[style-name='Title'] => h1.doc-title:fresh
        p[style-name='Subtitle'] => h2.doc-subtitle:fresh
        p[style-name='Heading 1'] => h2.doc-heading:fresh
        p[style-name='Heading 2'] => h3.doc-heading:fresh
        p[style-name='Heading 3'] => h4.doc-heading:fresh
        p[style-name='Heading 4'] => h5.doc-heading:fresh
        p[style-name='Quote'] => blockquote.doc-quote:fresh
        p[style-name='Intense Quote'] => blockquote.doc-quote-intense:fresh
        r[style-name='Strong'] => strong
        r[style-name='Emphasis'] => em
        p[style-name='List Paragraph'] => li:fresh
    """.strip()
