"""
Generador de paquetes IMSCC para Canvas LMS.

Script principal que orquesta la lectura de archivos DOCX y XLSX,
el procesamiento del contenido con diseño institucional, y la generación
del paquete .imscc compatible con Canvas LMS.

Uso:
    python main.py
    python main.py --estructura estructura.xlsx --titulo "Mi Curso"
    python main.py --input ./mi_carpeta --output ./salida
"""

import argparse
import logging
import sys
import io
from pathlib import Path

# Agregar el directorio del proyecto al path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import INPUT_DIR, OUTPUT_DIR, DEFAULT_STRUCTURE_FILE, MEDIA_DIR, DOCX_DIR
from readers.sheets_reader import read_structure
from readers.docx_reader import read_docx
from readers.media_collector import collect_media
from processors.html_renderer import HtmlRenderer
from processors.structure_builder import build_structure
from builders.package_builder import build_package


def setup_logging(verbose: bool = False):
    """Configura el sistema de logging."""
    level = logging.DEBUG if verbose else logging.INFO
    # Forzar UTF-8 en la salida para soportar emojis en Windows
    utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    handler = logging.StreamHandler(utf8_stdout)
    handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    ))
    logging.basicConfig(
        level=level,
        handlers=[handler],
    )


def ensure_directories(input_dir: Path, output_dir: Path, media_dir: Path):
    """Crea los directorios necesarios si no existen."""
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    media_dir.mkdir(parents=True, exist_ok=True)


def main():
    """Punto de entrada principal del generador IMSCC."""
    parser = argparse.ArgumentParser(
        description="Generador de paquetes IMSCC para Canvas LMS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main.py
  python main.py --estructura input/estructura.xlsx --titulo "Curso de Ejemplo"
  python main.py --input ./mis_archivos --output ./paquetes
  python main.py --verbose

Estructura de entrada esperada:
  input/
  ├── estructura.xlsx       # Hoja con la estructura del curso
  ├── bienvenida.docx       # Archivos DOCX referenciados en el XLSX
  ├── tema1.docx
  └── media/                # Archivos multimedia
      ├── banner.png
      └── video_intro.mp4
        """,
    )

    parser.add_argument(
        "--estructura", "-e",
        type=str,
        default=None,
        help="Ruta al archivo XLSX con la estructura del curso (default: input/estructura.xlsx)",
    )
    parser.add_argument(
        "--titulo", "-t",
        type=str,
        default="Curso Generado",
        help="Título del curso (default: 'Curso Generado')",
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help="Directorio de archivos de entrada (default: ./input)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Directorio de salida para el paquete (default: ./output)",
    )
    parser.add_argument(
        "--nombre-archivo", "-n",
        type=str,
        default=None,
        help="Nombre del archivo .imscc de salida (sin extensión)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Mostrar mensajes detallados de depuración",
    )
    parser.add_argument(
        "--tema",
        type=str,
        choices=["educacion", "posgrado"],
        default="educacion",
        help="Tema visual del curso (default: 'educacion')",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)
    logger = logging.getLogger("main")

    # =========================================================================
    # BANNER
    # =========================================================================
    print()
    print("=" * 60)
    print("  Generador IMSCC para Canvas LMS")
    print("  Common Cartridge 1.1 — Maquetación Automatizada")
    print("=" * 60)
    print()

    # =========================================================================
    # CONFIGURAR RUTAS
    # =========================================================================
    input_dir = Path(args.input) if args.input else INPUT_DIR
    output_dir = Path(args.output) if args.output else OUTPUT_DIR
    media_dir = input_dir / "media"
    structure_file = Path(args.estructura) if args.estructura else (input_dir / "estructura.xlsx")

    ensure_directories(input_dir, output_dir, media_dir)

    logger.info(f"[DIR] Directorio de entrada: {input_dir}")
    logger.info(f"[DIR] Directorio de salida:  {output_dir}")
    logger.info(f"[DOC] Archivo de estructura: {structure_file}")
    print()

    # =========================================================================
    # PASO 1: Leer estructura del curso desde XLSX
    # =========================================================================
    print("-" * 60)
    print("  PASO 1: Leyendo estructura del curso...")
    print("-" * 60)

    try:
        modules = read_structure(structure_file)
    except FileNotFoundError as e:
        logger.error(f"❌ {e}")
        logger.error(
            f"Asegúrate de que el archivo '{structure_file.name}' existe en "
            f"la carpeta '{structure_file.parent}'."
        )
        _print_xlsx_template_help()
        sys.exit(1)
    except ValueError as e:
        logger.error(f" Error en el formato del XLSX: {e}")
        _print_xlsx_template_help()
        sys.exit(1)

    print(f"  [OK] {len(modules)} modulos encontrados\n")

    # =========================================================================
    # PASO 2: Leer archivos DOCX referenciados
    # =========================================================================
    print("-" * 60)
    print("  PASO 2: Leyendo archivos DOCX...")
    print("-" * 60)

    # Recopilar nombres de archivos DOCX referenciados
    docx_names = set()
    for module in modules:
        for item in module.items:
            if item.archivo_docx:
                docx_names.add(item.archivo_docx)

    docx_contents = {}
    for docx_name in sorted(docx_names):
        docx_path = input_dir / docx_name
        try:
            docx_contents[docx_name] = read_docx(docx_path)
        except FileNotFoundError:
            logger.warning(f"  ⚠ DOCX no encontrado: {docx_name}")
        except Exception as e:
            logger.error(f"  ❌ Error leyendo {docx_name}: {e}")

    print(f"  [OK] {len(docx_contents)}/{len(docx_names)} archivos DOCX leidos\n")

    # =========================================================================
    # PASO 3: Recolectar multimedia
    # =========================================================================
    print("-" * 60)
    print("  PASO 3: Recolectando archivos multimedia...")
    print("-" * 60)

    # Obtener todos los archivos multimedia referenciados
    referenced_media = set()
    for module in modules:
        for item in module.items:
            for media_name in item.archivo_media:
                referenced_media.add(media_name)

    media_inventory = collect_media(media_dir, list(referenced_media))

    if media_inventory.missing:
        print(f"  ⚠ Archivos multimedia faltantes: {media_inventory.missing}")
    print()

    # =========================================================================
    # PASO 4: Procesar y renderizar HTML
    # =========================================================================
    print("-" * 60)
    print("  PASO 4: Generando HTML con diseño institucional...")
    print("-" * 60)

    html_renderer = HtmlRenderer(theme=args.tema)
    course = build_structure(
        modules=modules,
        docx_contents=docx_contents,
        media_inventory=media_inventory,
        html_renderer=html_renderer,
        course_title=args.titulo,
    )
    print()

    # =========================================================================
    # PASO 5: Empaquetar IMSCC
    # =========================================================================
    print("-" * 60)
    print("  PASO 5: Empaquetando archivo .imscc...")
    print("-" * 60)

    output_path = build_package(
        course=course,
        output_dir=output_dir,
        output_filename=args.nombre_archivo,
    )

    print()
    print("=" * 60)
    print("  [OK] Proceso completado!")
    print(f"  Paquete generado: {output_path}")
    print()
    print("  Para importar en Canvas LMS:")
    print("    1. Ve a Configuración > Importar contenido del curso")
    print("    2. Selecciona 'Common Cartridge 1.x Package'")
    print("    3. Sube el archivo .imscc generado")
    print("    4. Haz clic en 'Importar'")
    print("=" * 60)
    print()


def _print_xlsx_template_help():
    """Muestra ayuda sobre el formato esperado del archivo XLSX."""
    print()
    print("  ℹ️ El archivo XLSX debe tener las siguientes columnas:")
    print("  ┌──────────────┬────────────────────────────────────┐")
    print("  │ Columna      │ Descripción                        │")
    print("  ├──────────────┼────────────────────────────────────┤")
    print("  │ modulo       │ Nombre del módulo (obligatorio)    │")
    print("  │ orden        │ Orden del ítem (obligatorio)       │")
    print("  │ tipo         │ pagina|archivo|url_externa|subenc. │")
    print("  │              │ tarea|evaluacion|foro              │")
    print("  │ titulo       │ Título del ítem (obligatorio)      │")
    print("  │ archivo_docx │ Nombre del archivo .docx           │")
    print("  │ archivo_media│ Archivos multimedia (sep. por ;)   │")
    print("  │ plantilla    │ base_page|cidilabs_page|...        │")
    print("  │ url          │ URL (si tipo=url_externa|foro)     │")
    print("  │ puntos       │ Puntaje (tareas/quizzes)           │")
    print("  │ intentos     │ Intentos (tareas/quizzes)          │")
    print("  │ notas        │ Notas adicionales                  │")
    print("  └──────────────┴────────────────────────────────────┘")
    print()


if __name__ == "__main__":
    main()
