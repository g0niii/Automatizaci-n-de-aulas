"""
Constructor de archivos de página.
Genera los archivos HTML individuales y archivos XML auxiliares
(web links, course settings) para el paquete IMSCC.
"""

import logging
from pathlib import Path

from processors.structure_builder import CourseStructure, PageResource

logger = logging.getLogger(__name__)


def generate_page_files(course: CourseStructure) -> dict[str, str | bytes]:
    """
    Genera todos los archivos de contenido del paquete IMSCC.

    Retorna un diccionario de {ruta_relativa: contenido} donde contenido
    puede ser str (HTML/XML) o bytes (multimedia).

    Args:
        course: Estructura completa del curso.

    Returns:
        Dict de ruta -> contenido para todos los archivos generados.
    """
    files: dict[str, str | bytes] = {}

    logger.info("Generando archivos de páginas...")

    for module in course.modules:
        for page in module.pages:
            if page.resource_type == "subheader":
                continue

            if page.resource_type == "webcontent" and page.html_content:
                # Página HTML
                files[page.html_filename] = page.html_content
                logger.debug(f"  Generada página: {page.html_filename}")

            elif page.resource_type == "imswl_xmlv1p1" and page.href:
                # Web link XML
                weblink_xml = _generate_weblink_xml(page)
                files[page.html_filename] = weblink_xml
                logger.debug(f"  Generado weblink: {page.html_filename}")

            elif "associatedcontent" in page.resource_type:
                # Tarea (Assignment)
                # 1. HTML de la consigna
                files[page.html_filename] = page.html_content
                # 2. XML de configuración (en la misma carpeta)
                settings_path = page.html_filename.replace("actividad.html", "assignment_settings.xml")
                files[settings_path] = _generate_assignment_xml(page)
                logger.debug(f"  Generada tarea: {page.html_filename}")

            elif page.resource_type == "imsdt_xmlv1p1":
                # Foro (Discussion Topic)
                files[page.html_filename] = _generate_discussion_xml(page)
                logger.debug(f"  Generado foro: {page.html_filename}")

            elif "imsqti" in page.resource_type:
                # Quiz (Cuestionario) - Placeholder por ahora
                files[page.html_filename] = _generate_quiz_qti_xml(page)
                meta_path = page.html_filename.replace("assessment_qti.xml", "assessment_meta.xml")
                files[meta_path] = _generate_quiz_meta_xml(page)
                logger.debug(f"  Generado quiz: {page.html_filename}")

    # Generar course_settings.xml
    course_settings = _generate_course_settings(course)
    files["course_settings/course_settings.xml"] = course_settings

    logger.info(f"Archivos generados: {len(files)} archivos de contenido.")
    return files


def _generate_weblink_xml(page: PageResource) -> str:
    """
    Genera el XML de un web link según el estándar CC 1.1.

    Args:
        page: PageResource de tipo url_externa.

    Returns:
        String XML del web link.
    """
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<webLink xmlns="http://www.imsglobal.org/xsd/imscc_v1p1/imswl_v1p1"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://www.imsglobal.org/xsd/imscc_v1p1/imswl_v1p1 http://www.imsglobal.org/profile/cc/ccv1p1/ccv1p1_imswl_v1p1.xsd">
  <title>{page.title}</title>
  <url href="{page.href}"/>
</webLink>"""


def _generate_course_settings(course: CourseStructure) -> str:
    """
    Genera el archivo course_settings.xml.
    Este archivo es el SECRETO para que Canvas reconozca las páginas como nativas.
    """
    wiki_pages_xml = ""
    for module in course.modules:
        for page in module.pages:
            if page.resource_type == "webcontent" and "wiki_content" in page.html_filename:
                # El URL para Canvas es el nombre del archivo sin la extensión y sin la carpeta
                page_url = Path(page.html_filename).stem
                wiki_pages_xml += f"""
    <wiki_page identifier="{page.identifier}_WIKI">
      <title>{page.title}</title>
      <url>{page_url}</url>
      <editing_roles>teachers</editing_roles>
      <workflow_state>active</workflow_state>
    </wiki_page>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<course identifier="{course.identifier}_COURSE"
        xmlns="http://canvas.instructure.com/xsd/cccv1p0"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://canvas.instructure.com/xsd/cccv1p0 https://canvas.instructure.com/xsd/cccv1p0.xsd">
  <title>{course.course_title}</title>
  <course_code>{course.course_title}</course_code>
  <is_public>false</is_public>
  <allow_student_wiki_edits>false</allow_student_wiki_edits>
  <default_view>modules</default_view>
  <wiki_pages>{wiki_pages_xml}
  </wiki_pages>
</course>"""


def _generate_assignment_xml(page: PageResource) -> str:
    """Genera el archivo assignment_settings.xml para Canvas."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<assignment identifier="{page.identifier}_ASG" xmlns="http://canvas.instructure.com/xsd/cccv1p0">
  <title>{page.title}</title>
  <points_possible>{page.puntos}</points_possible>
  <grading_type>points</grading_type>
  <submission_types>online_text_entry,online_upload</submission_types>
  <allowed_attempts>{page.intentos}</allowed_attempts>
  <workflow_state>published</workflow_state>
</assignment>"""


def _generate_discussion_xml(page: PageResource) -> str:
    """Genera el archivo XML para un foro (Discussion Topic)."""
    # Escapar contenido HTML para ponerlo dentro del XML
    from xml.sax.saxutils import escape
    escaped_content = escape(page.html_content)
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<topic xmlns="http://www.imsglobal.org/xsd/imsccv1p1/imsdt_v1p1">
  <title>{page.title}</title>
  <text texttype="text/html">{escaped_content}</text>
</topic>"""


def _generate_quiz_qti_xml(page: PageResource) -> str:
    """Genera el XML QTI básico para un cuestionario."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<questestinterop xmlns="http://www.imsglobal.org/xsd/ims_qtiasiv1p2">
  <assessment ident="{page.identifier}_QTI" title="{page.title}">
    <section ident="root_section">
      <!-- Aquí irían las preguntas -->
    </section>
  </assessment>
</questestinterop>"""


def _generate_quiz_meta_xml(page: PageResource) -> str:
    """Genera el metadata de Canvas para el quiz."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<quiz identifier="{page.identifier}" xmlns="http://canvas.instructure.com/xsd/cccv1p0">
  <title>{page.title}</title>
  <allowed_attempts>{page.intentos}</allowed_attempts>
  <scoring_policy>keep_highest</scoring_policy>
  <quiz_type>assignment</quiz_type>
  <points_possible>{page.puntos}</points_possible>
  <workflow_state>published</workflow_state>
</quiz>"""
