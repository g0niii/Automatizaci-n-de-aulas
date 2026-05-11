import os
import io
import sys
import shutil
import logging
import uuid
from pathlib import Path
from datetime import datetime

# Setup UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Agregar el directorio del proyecto al path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from readers.ucc_sheets_reader import read_ucc_structure
from processors.docx_segmenter import segment_module_docx
from processors.cidilabs_builder import build_intro_page, build_content_page
from processors.xml_injector import inject_manifest, inject_module_meta
import zipfile

def create_imscc_package(source_dir: Path, output_file: Path):
    """Crea un archivo .imscc comprimiendo el directorio fuente."""
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in source_dir.rglob('*'):
            if file.is_file():
                zipf.write(file, file.relative_to(source_dir))
    logger.info(f"Paquete creado: {output_file}")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("clonador_feldman")

def gen_id():
    return "g" + uuid.uuid4().hex[:31]

def run_feldman():
    # 1. Rutas
    base_dir = Path(r"c:\Users\g0nii\Desktop\Proyecto automatización de Maquetación")
    elementos_dir = base_dir / "Elementos de las aulas"
    aula_base = elementos_dir / "_extracted_posgrado"
    output_dir = base_dir / "output" / "working_clon_feldman"
    
    xlsx_path = elementos_dir / "Estructura general - Para maquetación (Feldman, Gabriel y Análisis Financiero para la toma de decisiones)).xlsx"
    docx_path = elementos_dir / "Material multimedial Módulo I.docx"

    # 2. Copiar Aula Base
    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(aula_base, output_dir)
    logger.info(f"Aula Base copiada a {output_dir}")

    # 3. Leer Estructura XLSX
    items = read_ucc_structure(xlsx_path)
    m1_items = [it for it in items if "Módulo 1" in it.modulo or "módulo 1" in it.modulo.lower() or "M1" in it.modulo]
    
    # 4. Segmentar DOCX (Mapeo personalizado para Feldman)
    # El segmentador por defecto no va a encontrar los 11 puntos porque los encabezados son distintos.
    # Vamos a usar un mapeo manual de encabezados del DOCX a los titulos del XLSX.
    
    import mammoth
    from bs4 import BeautifulSoup
    with open(docx_path, "rb") as f:
        html = mammoth.convert_to_html(f).value
    soup = BeautifulSoup(html, "html.parser")
    elements = list(soup.find_all(recursive=False))
    
    # Definimos los puntos de corte basados en el DOCX
    # Buscamos los textos que identificamos antes
    split_points = [
        ("1.1. Definici", "1.1. Introducción"),
        ("1.1.1. Riesgo como condici", "1.2. El rol del riesgo en la toma de decisiones organizacionales"),
        ("1.1.4. Riesgo e incertidumbre", "1.3. Conceptos fundamentales de la gestión del riesgo"),
        ("1.2. Herramientas cualitativas", "1.4. Herramientas cualitativas para el análisis estructurado"),
        ("1.3. Introducción a las finanzas", "1.5. Riesgo y estructura operativa: introducción a NOF y FM"),
        ("1.4.1. Supuestos, modelos", "1.6. Supuestos, modelos financieros y riesgo"),
        ("1.4.2. Reflexión integradora", "1.7. Reflexión integradora: riesgo, operación y finanzas"),
        ("1.5.1. Integración conceptual", "1.8. Integración conceptual: del riesgo a la toma de decisiones financieras"),
        ("1.5.2. Hacia una visión", "1.9. Hacia una visión sistémica: conexiones entre contexto, operación y finanzas"),
        ("1.5.3. Riesgo como fundamento", "1.10. Riesgo como fundamento de la proyección financiera"),
        ("cierre", "1.11. Reflexión final") # Punto extra si existe
    ]
    
    pages_content = {}
    current_title = "1.1. Introducción"
    current_html = []
    
    point_idx = 1
    for el in elements:
        txt = el.get_text().strip()
        
        # ¿Es un punto de corte?
        found_new = False
        if point_idx < len(split_points):
            marker, next_title = split_points[point_idx]
            if marker in txt:
                # Guardar página actual
                pages_content[current_title] = "".join([str(x) for x in current_html])
                current_title = next_title
                current_html = [el]
                point_idx += 1
                found_new = True
        
        if not found_new:
            current_html.append(el)
            
    # Guardar la última
    pages_content[current_title] = "".join([str(x) for x in current_html])

    # 5. Construir páginas HTML
    logger.info(f"Construyendo {len(pages_content)} paginas para Feldman...")
    
    # Banners (usamos los de posgrado por ahora)
    base_content_banner = "../web_resources/Multimedia%20cargada/2.1.%20La%20ense%C3%B1anza%20y%20el%20profesor.%20Ser%20docente%20hoy.%20Sus%20trayectorias%20e%20incidencia%20en%20las%20pr%C3%A1cticas%20docentes.%20Una%20mirada%20multidimensional%20trabajo,%20oficio,%20artesan%C3%ADa,%20profesi%C3%B3n..png"
    
    page_files = {}
    for i, (title, content_html) in enumerate(pages_content.items(), 1):
        num = f"1.{i}"
        page_id = "g_feldman_p" + str(i)
        slug = title.lower().replace(" ", "-").replace(".", "-").replace(":", "").replace("á","a").replace("é","e").replace("í","i").replace("ó","o").replace("ú","u")[:50]
        filepath = f"wiki_content/{slug}.html"
        
        page_html = build_content_page(
            body_html=content_html,
            title=title,
            banner_src=base_content_banner,
            identifier=page_id
        )
        
        (output_dir / filepath).parent.mkdir(parents=True, exist_ok=True)
        (output_dir / filepath).write_text(page_html, encoding="utf-8")
        page_files[num] = (filepath, page_id, title)
        logger.info(f"[OK] {num}: {title}")

    # 6. Inyectar en XMLs
    module_title = "Módulo 1: Análisis Financiero para la toma de decisiones"
    
    manifest_path = output_dir / "imsmanifest.xml"
    manifest_xml = manifest_path.read_text(encoding="utf-8")
    manifest_xml = inject_manifest(manifest_xml, module_title, page_files)
    manifest_path.write_text(manifest_xml, encoding="utf-8")
    
    meta_path = output_dir / "course_settings" / "module_meta.xml"
    meta_xml = meta_path.read_text(encoding="utf-8")
    meta_xml = inject_module_meta(meta_xml, module_title, page_files)
    meta_path.write_text(meta_xml, encoding="utf-8")
    
    # 7. Empaquetar
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    imscc_filename = f"Aula_Feldman_M1_{timestamp}.imscc"
    create_imscc_package(output_dir, base_dir / "output" / imscc_filename)
    
    print("\n" + "="*60)
    print(f"  [OK] Maquetacion de FELDMAN completada!")
    print(f"  Paquete: {imscc_filename}")
    print("="*60)

if __name__ == "__main__":
    run_feldman()
