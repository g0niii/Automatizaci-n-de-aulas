"""
Constructor de estructura del curso.
Toma la estructura leída del XLSX, los contenidos de DOCX y multimedia,
y construye la estructura final del curso lista para generar el paquete IMSCC.
"""

import logging
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from readers.sheets_reader import CourseModule, CourseItem
from readers.docx_reader import DocxContent, ExtractedImage
from readers.media_collector import MediaInventory, MediaFile
from config import ID_PREFIX, RESOURCE_TYPES

logger = logging.getLogger(__name__)


def _generate_id(prefix: str = "") -> str:
    """Genera un identificador único para el manifiesto."""
    uid = uuid.uuid4().hex[:12].upper()
    if prefix:
        return f"{ID_PREFIX}_{prefix}_{uid}"
    return f"{ID_PREFIX}_{uid}"


@dataclass
class PageResource:
    """Recurso de tipo página (webcontent) listo para empaquetar."""
    identifier: str              # ID único del recurso
    title: str                   # Título de la página
    html_content: str            # HTML renderizado completo
    html_filename: str           # Nombre del archivo HTML en el paquete
    resource_type: str           # Tipo CC (webcontent, imswl_xmlv1p1, etc.)
    media_files: list = field(default_factory=list)    # MediaFile asociados
    docx_images: list = field(default_factory=list)    # ExtractedImage del DOCX
    href: Optional[str] = None   # URL para links externos
    puntos: float = 10.0
    intentos: int = 1
    vencimiento: Optional[str] = None
    plantilla: str = "base_page"


@dataclass
class ModuleStructure:
    """Estructura de un módulo listo para el manifiesto."""
    identifier: str              # ID único del módulo
    title: str                   # Nombre del módulo
    pages: list[PageResource] = field(default_factory=list)


@dataclass
class CourseStructure:
    """Estructura completa del curso lista para generar el paquete."""
    course_title: str
    identifier: str
    modules: list[ModuleStructure] = field(default_factory=list)
    all_media: dict[str, MediaFile] = field(default_factory=dict)
    all_docx_images: list[ExtractedImage] = field(default_factory=list)


def build_structure(
    modules: list[CourseModule],
    docx_contents: dict[str, DocxContent],
    media_inventory: MediaInventory,
    html_renderer,
    course_title: str = "Curso Generado",
) -> CourseStructure:
    """
    Construye la estructura completa del curso combinando la información
    de módulos, contenidos DOCX y multimedia.

    Args:
        modules: Lista de módulos leídos del XLSX.
        docx_contents: Dict de nombre_archivo -> DocxContent leídos.
        media_inventory: Inventario de archivos multimedia.
        html_renderer: Instancia de HtmlRenderer para renderizar páginas.
        course_title: Título del curso.

    Returns:
        CourseStructure con toda la información organizada.
    """
    logger.info(f"Construyendo estructura del curso: '{course_title}'")

    course = CourseStructure(
        course_title=course_title,
        identifier=_generate_id("MANIFEST"),
        all_media=dict(media_inventory.files),
    )

    page_counter = 0

    for mod_idx, module in enumerate(modules, 1):
        mod_struct = ModuleStructure(
            identifier=_generate_id(f"MOD{mod_idx:02d}"),
            title=module.nombre,
        )

        logger.info(f"  Módulo {mod_idx}: '{module.nombre}' ({len(module.items)} ítems)")

        for item in module.items:
            page_counter += 1
            page = _build_page_resource(
                item=item,
                page_number=page_counter,
                module_name=module.nombre,
                docx_contents=docx_contents,
                media_inventory=media_inventory,
                html_renderer=html_renderer,
            )

            if page:
                mod_struct.pages.append(page)

                # Acumular imágenes de DOCX para empaquetado
                course.all_docx_images.extend(page.docx_images)

        course.modules.append(mod_struct)

    logger.info(
        f"Estructura construida: {len(course.modules)} módulos, "
        f"{sum(len(m.pages) for m in course.modules)} páginas totales."
    )

    return course


def _build_page_resource(
    item: CourseItem,
    page_number: int,
    module_name: str,
    docx_contents: dict[str, DocxContent],
    media_inventory: MediaInventory,
    html_renderer,
) -> Optional[PageResource]:
    """
    Construye un PageResource a partir de un CourseItem.

    Args:
        item: Ítem del curso (del XLSX).
        page_number: Número secuencial de página.
        module_name: Nombre del módulo padre.
        docx_contents: Contenidos DOCX leídos.
        media_inventory: Inventario de multimedia.
        html_renderer: Renderizador HTML.

    Returns:
        PageResource listo o None si el tipo no genera recurso.
    """
    resource_type = RESOURCE_TYPES.get(item.tipo, "webcontent")
    identifier = _generate_id(f"PAGE{page_number:03d}")

    # Subencabezados no generan recurso propio
    if item.tipo == "subencabezado":
        return PageResource(
            identifier=identifier,
            title=item.titulo,
            html_content="",
            html_filename="",
            resource_type="subheader",
        )

    # URLs externas
    if item.tipo == "url_externa":
        return PageResource(
            identifier=identifier,
            title=item.titulo,
            html_content="",
            html_filename=f"web_resources/weblink_{page_number:03d}.xml",
            resource_type=resource_type,
            href=item.url,
        )

    # Obtener contenido del DOCX si está referenciado
    contenido_html = ""
    docx_images = []

    if item.archivo_docx and item.archivo_docx in docx_contents:
        docx = docx_contents[item.archivo_docx]
        contenido_html = docx.html
        docx_images = docx.images

        # Reemplazar rutas de imágenes placeholder con rutas relativas del paquete
        for img in docx_images:
            contenido_html = contenido_html.replace(
                f"$MEDIA_PATH$/{img.filename}",
                f"$IMS-CC-FILEBASE$/media/{img.filename}"
            )
    elif item.archivo_docx:
        logger.warning(
            f"  ⚠ DOCX referenciado no encontrado: '{item.archivo_docx}' "
            f"(ítem: '{item.titulo}')"
        )

    # Recopilar archivos multimedia asociados
    media_files = []
    media_info = []
    for media_name in item.archivo_media:
        if media_name in media_inventory.files:
            mf = media_inventory.files[media_name]
            media_files.append(mf)
            media_info.append({
                "filename": mf.filename,
                "type": mf.media_type,
                "path": f"$IMS-CC-FILEBASE$/media/{mf.filename}",
            })
        else:
            logger.warning(f"  ⚠ Media no encontrada: '{media_name}'")

    # Identificar carpetas para tipos complejos
    if item.tipo == "tarea":
        html_filename = f"g{uuid.uuid4().hex}/actividad.html"
    elif item.tipo == "evaluacion":
        html_filename = f"g{uuid.uuid4().hex}/assessment_qti.xml"
    elif item.tipo == "foro":
        html_filename = f"g{uuid.uuid4().hex}.xml"
    else:
        html_filename = f"wiki_content/page_{page_number:03d}.html"

    # Banner personalizado
    banner_url = None
    if item.banner and item.banner in media_inventory.files:
        mf_banner = media_inventory.files[item.banner]
        banner_url = f"$IMS-CC-FILEBASE$/media/{mf_banner.filename}"
        # Asegurarse de que el banner esté en la lista de media del recurso
        if mf_banner not in media_files:
            media_files.append(mf_banner)

    # Renderizar HTML con diseño institucional
    rendered_html = html_renderer.render_page(
        template_name=item.plantilla,
        titulo=item.titulo,
        contenido_html=contenido_html,
        modulo_nombre=module_name,
        numero_pagina=page_number,
        media_files=media_info,
        extra_context={"banner_url": banner_url}
    )

    return PageResource(
        identifier=identifier,
        title=item.titulo,
        html_content=rendered_html,
        html_filename=html_filename,
        resource_type=resource_type,
        media_files=media_files,
        docx_images=docx_images,
        puntos=item.puntos,
        intentos=item.intentos,
        vencimiento=item.vencimiento,
        plantilla=item.plantilla,
    )
