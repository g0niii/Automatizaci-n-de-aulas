"""
Generador IMSCC — Modo Institucional UCC.
Especializado para procesar la planilla de Laura Conti y archivos DOCX segmentados.
"""

import sys
import logging
from pathlib import Path
import datetime

# Agregar el directorio del proyecto al path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from readers.ucc_sheets_reader import read_ucc_structure
from processors.docx_splitter import extract_section_by_title
from processors.html_renderer import HtmlRenderer
from processors.structure_builder import CourseStructure, PageResource, ModuleStructure
from builders.package_builder import build_package

# Configuración de logs
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("main_ucc")

def main():
    print("-" * 60)
    print("  GENERADOR UCC — MODO INSTITUCIONAL")
    print("-" * 60)

    # 1. Definir rutas (usando tus archivos reales)
    base_path = Path(r"c:\Users\g0nii\Desktop\Proyecto automatización de Maquetación\Elementos de las aulas")
    xlsx_path = base_path / "Estructura general - Para maquetación (Laura Conti-Fundamentos de la Gestión de Proyectos).xlsx"
    docx_folder = base_path
    output_dir = Path("./output")

    # 2. Leer Planilla UCC
    print(f"  Leyendo planilla: {xlsx_path.name}")
    items = read_ucc_structure(xlsx_path)
    print(f"  [OK] {len(items)} ítems detectados.")

    # 3. Preparar Renderizador CIDILABS
    renderer = HtmlRenderer(theme="educacion") # Azul UCC
    
    # Estructura para el generador de paquetes
    course_id = f"UCC_GP_{datetime.datetime.now().strftime('%Y%m%d')}"
    course = CourseStructure(
        identifier=course_id,
        course_title="Fundamentos de la Gestión de Proyectos",
        modules=[]
    )

    # 4. Procesar Ítems y Dividir DOCX
    current_module_obj = None
    page_counter = 1
    
    # Agrupar ítems por módulo para el objeto CourseStructure
    modules_map = {}

    print("  Procesando contenido y dividiendo documentos...")
    for i, item in enumerate(items):
        if item.modulo not in modules_map:
            mod_id = f"mod_{len(modules_map)+1}"
            modules_map[item.modulo] = ModuleStructure(identifier=mod_id, title=item.modulo, pages=[])
            course.modules.append(modules_map[item.modulo])
        
        mod_obj = modules_map[item.modulo]
        
        # Determinar qué archivo DOCX usar (buscando M1, M2, etc en el nombre)
        # Por ahora usamos el que subiste si es Módulo 1
        docx_path = None
        if "Módulo 1" in item.modulo:
            docx_path = docx_folder / "Fundamentos_gestión_proyectos-Conti-M1.docx"
        
        if docx_path and docx_path.exists():
            # Obtener el siguiente título para saber dónde cortar
            next_title = None
            if i + 1 < len(items) and items[i+1].modulo == item.modulo:
                next_title = items[i+1].titulo
            
            # Extraer sección quirúrgica
            print(f"    -> Extrayendo: {item.titulo}")
            html_content = extract_section_by_title(docx_path, item.titulo, next_title)
            
            # Renderizar con CIDILABS
            plantilla = "home_page" if i == 0 else "cidilabs_page"
            rendered_html = renderer.render_page(
                template_name=plantilla,
                titulo=item.titulo,
                contenido_html=html_content,
                modulo_nombre=item.modulo,
                numero_pagina=page_counter
            )
            
            # Crear recurso de página
            page_res = PageResource(
                identifier=f"page_{page_counter:03d}",
                title=item.titulo,
                resource_type="webcontent",
                html_filename=f"wiki_content/page_{page_counter:03d}.html",
                html_content=rendered_html
            )
            mod_obj.pages.append(page_res)
            page_counter += 1
        else:
            logger.warning(f"    [!] No se encontró DOCX para {item.modulo}")

    # 5. Empaquetar
    print("-" * 60)
    print("  Empaquetando IMSCC...")
    pkg_path = build_package(course, output_dir, f"Aula_Real_UCC_{datetime.datetime.now().strftime('%H%M%S')}")
    
    print("-" * 60)
    print(f"  [EXITO] Aula generada: {pkg_path}")
    print("-" * 60)

if __name__ == "__main__":
    main()
