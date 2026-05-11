"""
Constructor del paquete IMSCC.
Empaqueta todos los archivos generados (manifiesto, páginas HTML,
multimedia, configuración) en un archivo .imscc (ZIP).
"""

import logging
import zipfile
from pathlib import Path
from datetime import datetime

from processors.structure_builder import CourseStructure
from builders.manifest_builder import build_manifest
from builders.page_builder import generate_page_files
from config import OUTPUT_DIR, ENCODING

logger = logging.getLogger(__name__)


def build_package(
    course: CourseStructure,
    output_dir: Path = OUTPUT_DIR,
    output_filename: str | None = None,
) -> Path:
    """
    Construye el paquete .imscc final.

    Genera el manifiesto, las páginas HTML, y empaqueta todo junto con
    los archivos multimedia en un archivo ZIP con extensión .imscc.

    Args:
        course: Estructura completa del curso.
        output_dir: Directorio de salida.
        output_filename: Nombre del archivo de salida (sin extensión).
                        Si None, usa el título del curso + timestamp.

    Returns:
        Path al archivo .imscc generado.
    """
    # Crear directorio de salida
    output_dir.mkdir(parents=True, exist_ok=True)

    # Nombre del archivo de salida
    if not output_filename:
        safe_title = "".join(
            c if c.isalnum() or c in (" ", "-", "_") else "_"
            for c in course.course_title
        ).strip().replace(" ", "_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{safe_title}_{timestamp}"

    output_path = output_dir / f"{output_filename}.imscc"

    logger.info(f"Empaquetando IMSCC: {output_path}")

    # Generar manifiesto XML
    manifest_xml = build_manifest(course)

    # Generar archivos de página
    page_files = generate_page_files(course)

    # Crear paquete ZIP
    with zipfile.ZipFile(
        str(output_path),
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as zf:
        # 1. imsmanifest.xml (DEBE estar en la raíz)
        zf.writestr("imsmanifest.xml", manifest_xml)
        logger.debug("  + imsmanifest.xml")

        # 2. Archivos de página (HTML, XML, course_settings)
        for filepath, content in page_files.items():
            if isinstance(content, bytes):
                zf.writestr(filepath, content)
            else:
                # Importante: Escribir con UTF-8 explícito para evitar caracteres extraños
                # En algunos casos, Canvas prefiere UTF-8 sin BOM para snippets
                zf.writestr(filepath, content.encode("utf-8"))
            logger.debug(f"  + {filepath}")

        # 3. Archivos multimedia del inventario
        media_count = 0
        for filename, media_file in course.all_media.items():
            archive_path = f"media/{filename}"
            if media_file.source_path.exists():
                zf.write(str(media_file.source_path), archive_path)
                media_count += 1
                logger.debug(f"  + {archive_path}")
            else:
                logger.warning(f"  [WARN] Archivo multimedia no encontrado: {media_file.source_path}")

        # 4. Imágenes extraídas de documentos DOCX
        docx_img_count = 0
        seen_images = set()
        for img in course.all_docx_images:
            if img.filename not in seen_images:
                archive_path = f"media/{img.filename}"
                zf.writestr(archive_path, img.data)
                seen_images.add(img.filename)
                docx_img_count += 1
                logger.debug(f"  + {archive_path} (DOCX)")

    # Estadísticas finales
    file_size = output_path.stat().st_size
    logger.info(
        f"\n{'='*60}\n"
        f"[OK] Paquete IMSCC generado exitosamente\n"
        f"{'='*60}\n"
        f"  [PKG] Archivo: {output_path}\n"
        f"  [TAM] Tamano: {file_size / 1024 / 1024:.2f} MB\n"
        f"  [PAG] Paginas: {sum(len(m.pages) for m in course.modules)}\n"
        f"  [MED] Media: {media_count} archivos\n"
        f"  [IMG] Imagenes DOCX: {docx_img_count}\n"
        f"  [MOD] Modulos: {len(course.modules)}\n"
        f"{'='*60}"
    )

    return output_path
