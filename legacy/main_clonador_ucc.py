"""
CLONADOR UCC v2 — Motor de Espejo con Inyección de Contenido.

Flujo:
  1. Copia el Aula Base (posgrado) como base de trabajo
  2. Lee la planilla XLSX para obtener la estructura del curso
  3. Lee el DOCX del módulo y lo segmenta en secciones
  4. Inyecta cada sección en una página CidiLabs (replicando el ejemplo maquetado)
  5. Crea las páginas nuevas (1.2, 1.3, 1.4) clonando la estructura de 1.1
  6. Actualiza imsmanifest.xml y module_meta.xml
  7. Empaqueta como .imscc

Uso:
  python main_clonador_ucc.py
"""

import os
import io
import sys
import shutil
import logging
import uuid
import zipfile
from pathlib import Path
from datetime import datetime

# Setup UTF-8 output for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Agregar el directorio del proyecto al path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from readers.ucc_sheets_reader import read_ucc_structure
from processors.docx_segmenter import segment_module_docx
from processors.cidilabs_builder import build_intro_page, build_content_page

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("clonador_ucc")


def gen_id():
    return "g" + uuid.uuid4().hex[:31]


def slugify(text: str) -> str:
    """Genera un slug para nombres de archivo a partir de un título."""
    import re
    text = text.lower().strip()
    text = re.sub(r'[áàäâ]', 'a', text)
    text = re.sub(r'[éèëê]', 'e', text)
    text = re.sub(r'[íìïî]', 'i', text)
    text = re.sub(r'[óòöô]', 'o', text)
    text = re.sub(r'[úùüû]', 'u', text)
    text = re.sub(r'[ñ]', 'n', text)
    text = re.sub(r'[^a-z0-9\s\-\.]', '', text)
    text = re.sub(r'[\s]+', '-', text)
    text = re.sub(r'\.', '-dot-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def main():
    print()
    print("=" * 60)
    print("  CLONADOR UCC v2 - Motor de Espejo")
    print("  Maquetacion Automatizada de Aulas Canvas")
    print("=" * 60)
    print()

    # =========================================================================
    # RUTAS
    # =========================================================================
    project_dir = Path(__file__).resolve().parent
    elementos_dir = project_dir / "Elementos de las aulas"

    base_dir = elementos_dir / "_extracted_posgrado"
    xlsx_path = elementos_dir / "Estructura general - Para maquetación (Laura Conti-Fundamentos de la Gestión de Proyectos).xlsx"
    docx_m1 = elementos_dir / "Fundamentos_gestión_proyectos-Conti-M1.docx"

    output_dir = project_dir / "output" / "working_clon"
    
    # Verificar archivos
    for f, label in [(base_dir, "Aula Base"), (xlsx_path, "XLSX"), (docx_m1, "DOCX M1")]:
        if not f.exists():
            logger.error(f"[ERROR] No se encontro {label}: {f}")
            sys.exit(1)
        logger.info(f"[OK] {label}: {f.name}")

    # =========================================================================
    # PASO 1: Copiar Aula Base
    # =========================================================================
    print()
    print("-" * 60)
    print("  PASO 1: Copiando Aula Base...")
    print("-" * 60)

    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(base_dir, output_dir)
    logger.info(f"Aula base copiada a: {output_dir}")

    # =========================================================================
    # PASO 2: Leer estructura del XLSX
    # =========================================================================
    print()
    print("-" * 60)
    print("  PASO 2: Leyendo planilla de estructura...")
    print("-" * 60)

    items = read_ucc_structure(xlsx_path)
    logger.info(f"Items totales: {len(items)}")

    # Filtrar solo Módulo 1
    m1_items = [it for it in items if "Módulo 1" in it.modulo or "módulo 1" in it.modulo.lower()]
    logger.info(f"Items Modulo 1: {len(m1_items)}")
    for it in m1_items:
        logger.info(f"  - [{it.tipo}] {it.titulo}")

    # =========================================================================
    # PASO 3: Segmentar DOCX del Módulo 1
    # =========================================================================
    print()
    print("-" * 60)
    print("  PASO 3: Segmentando DOCX del Modulo 1...")
    print("-" * 60)

    sections = segment_module_docx(docx_m1)
    logger.info(f"Secciones encontradas: {list(sections.keys())}")

    # =========================================================================
    # PASO 4: Construir páginas HTML con estilo CidiLabs
    # =========================================================================
    print()
    print("-" * 60)
    print("  PASO 4: Construyendo paginas CidiLabs...")
    print("-" * 60)

    # Título real del módulo
    # El XLSX solo dice "Módulo 1" sin subtítulo, lo construimos desde el DOCX/planilla
    module_title = "Módulo 1: Introducción a la gestión de proyectos"

    # Mapeo de secciones a títulos del XLSX
    content_sections = {}
    for it in m1_items:
        import re
        match = re.match(r'^(\d+\.\d+)\.?\s', it.titulo)
        if match:
            num = match.group(1)
            content_sections[num] = it.titulo

    logger.info(f"Titulo del modulo: {module_title}")
    logger.info(f"Secciones de contenido: {content_sections}")

    # Banner placeholder (se usan los de la base, luego se reemplazan en Figma)
    base_banner = "$IMS-CC-FILEBASE$/Multimedia%20cargada/Introducci%C3%B3n%20M1%20-%20EP.png"
    base_content_banner = "$IMS-CC-FILEBASE$/Multimedia%20cargada/1.1.%20(El%20primer%20uno%20hace%20referencia%20al%20modulo%20y%20el%20segundo%20uno%20corresponde%20al%20subm%C3%B3dulo)%20-%20EP.png"

    # --- Página de Introducción M1 ---
    intro_id = gen_id()
    intro_html = build_intro_page(
        intro_html=sections.get("intro", ""),
        objetivos_html=sections.get("objetivos", ""),
        banner_src=base_banner,
        identifier=intro_id,
    )

    # Sobrescribir la intro existente
    intro_path = "wiki_content/introduccion-m1-3.html"
    (output_dir / intro_path).write_text(intro_html, encoding="utf-8")
    logger.info(f"[OK] Intro M1: {len(intro_html)} chars")

    # --- Páginas de contenido (1.1, 1.2, 1.3, 1.4) ---
    page_files = {}  # num -> (filepath, identifier, title)
    
    for num in sorted(content_sections.keys()):
        title = content_sections[num]
        section_html = sections.get(num, f"<p>Contenido de {title} pendiente.</p>")
        
        page_id = gen_id()
        slug = slugify(title)
        filepath = f"wiki_content/{slug}.html"
        
        page_html = build_content_page(
            body_html=section_html,
            title=title,
            banner_src=base_content_banner,
            identifier=page_id,
        )
        
        (output_dir / filepath).write_text(page_html, encoding="utf-8")
        page_files[num] = (filepath, page_id, title)
        logger.info(f"[OK] {num}: '{title}' -> {filepath} ({len(page_html)} chars)")

    # =========================================================================
    # PASO 5: Actualizar imsmanifest.xml (preservando namespaces)
    # =========================================================================
    print()
    print("-" * 60)
    print("  PASO 5: Actualizando manifiesto...")
    print("-" * 60)

    from processors.xml_injector import inject_manifest, inject_module_meta

    manifest_path = output_dir / "imsmanifest.xml"
    manifest_xml = manifest_path.read_text(encoding="utf-8")
    
    manifest_xml = inject_manifest(
        xml_text=manifest_xml,
        module_title=module_title,
        pages=page_files
    )
    
    manifest_path.write_text(manifest_xml, encoding="utf-8")
    logger.info("Manifiesto actualizado")

    # =========================================================================
    # PASO 6: Actualizar module_meta.xml
    # =========================================================================
    print()
    print("-" * 60)
    print("  PASO 6: Actualizando module_meta.xml...")
    print("-" * 60)

    meta_path = output_dir / "course_settings" / "module_meta.xml"
    if meta_path.exists():
        meta_xml = meta_path.read_text(encoding="utf-8")
        meta_xml = inject_module_meta(
            xml_text=meta_xml,
            module_title=module_title,
            pages=page_files,
        )
        meta_path.write_text(meta_xml, encoding="utf-8")
        logger.info("module_meta.xml actualizado")

    # =========================================================================
    # PASO 7: Empaquetar como .imscc
    # =========================================================================
    print()
    print("-" * 60)
    print("  PASO 7: Empaquetando .imscc...")
    print("-" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    imscc_name = f"Aula_Maquetada_M1_{timestamp}.imscc"
    imscc_path = project_dir / "output" / imscc_name

    with zipfile.ZipFile(str(imscc_path), "w", zipfile.ZIP_DEFLATED) as zf:
        for root_path, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = Path(root_path) / file
                arcname = file_path.relative_to(output_dir)
                zf.write(file_path, arcname)

    file_size = imscc_path.stat().st_size / 1024 / 1024
    logger.info(f"Paquete generado: {imscc_path}")
    logger.info(f"Tamano: {file_size:.2f} MB")

    # =========================================================================
    # RESUMEN
    # =========================================================================
    print()
    print("=" * 60)
    print("  [OK] Maquetacion completada!")
    print(f"  Paquete: {imscc_path.name}")
    print(f"  Tamano: {file_size:.2f} MB")
    print(f"  Paginas de contenido: {len(page_files)}")
    print(f"  Secciones del DOCX: {list(sections.keys())}")
    print()
    print("  Para importar en Canvas:")
    print("    1. Configuracion > Importar contenido")
    print("    2. Common Cartridge 1.x Package")
    print("    3. Subir el .imscc")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
