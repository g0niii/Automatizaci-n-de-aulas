"""
Constructor del archivo imsmanifest.xml.
Genera el manifiesto XML según el estándar IMS Common Cartridge 1.1,
compatible con la importación de Canvas LMS.
"""

import logging
from xml.dom import minidom
import xml.etree.ElementTree as ET

from processors.structure_builder import CourseStructure, PageResource
from config import (
    CC_VERSION,
    CC_SCHEMA,
    CC_NAMESPACES,
    CC_SCHEMA_LOCATION,
    ENCODING,
)

logger = logging.getLogger(__name__)


def build_manifest(course: CourseStructure) -> str:
    """
    Genera el contenido XML del archivo imsmanifest.xml.

    Args:
        course: Estructura completa del curso.

    Returns:
        String XML del manifiesto formateado.
    """
    logger.info("Generando imsmanifest.xml...")

    # Registrar namespaces para que ElementTree los use correctamente
    for prefix, uri in CC_NAMESPACES.items():
        if prefix:  # No registrar el namespace por defecto con prefijo vacío
            ET.register_namespace(prefix, uri)
    ET.register_namespace("", CC_NAMESPACES[""])

    # Elemento raíz <manifest>
    manifest_attribs = {
        "identifier": course.identifier,
        "xmlns": CC_NAMESPACES[""],
        "xmlns:lom": CC_NAMESPACES["lom"],
        "xmlns:lomimscc": CC_NAMESPACES["lomimscc"],
        "xmlns:xsi": CC_NAMESPACES["xsi"],
        "xsi:schemaLocation": CC_SCHEMA_LOCATION,
    }

    manifest = ET.Element("manifest", manifest_attribs)

    # --- <metadata> ---
    metadata = ET.SubElement(manifest, "metadata")
    schema = ET.SubElement(metadata, "schema")
    schema.text = CC_SCHEMA
    schema_version = ET.SubElement(metadata, "schemaversion")
    schema_version.text = CC_VERSION

    # Metadata LOM del curso
    lom_ns = CC_NAMESPACES["lomimscc"]
    lom = ET.SubElement(metadata, f"{{{lom_ns}}}lom")
    lom_general = ET.SubElement(lom, f"{{{lom_ns}}}general")
    lom_title = ET.SubElement(lom_general, f"{{{lom_ns}}}title")
    lom_title_string = ET.SubElement(lom_title, f"{{{lom_ns}}}string", {"language": "es"})
    lom_title_string.text = course.course_title

    # --- <organizations> ---
    org_id = f"{course.identifier}_ORG"
    organizations = ET.SubElement(manifest, "organizations")
    organization = ET.SubElement(organizations, "organization", {
        "identifier": org_id,
        "structure": "rooted-hierarchy",
    })
    org_title = ET.SubElement(organization, "title")
    org_title.text = course.course_title

    # Agregar módulos como items jerárquicos
    for module in course.modules:
        module_item = ET.SubElement(organization, "item", {
            "identifier": f"{module.identifier}_ITEM",
        })
        module_title = ET.SubElement(module_item, "title")
        module_title.text = module.title

        # Agregar páginas como sub-items del módulo
        for page in module.pages:
            if page.resource_type == "subheader":
                # Subencabezados: solo item sin identifierref
                sub_item = ET.SubElement(module_item, "item", {
                    "identifier": f"{page.identifier}_ITEM",
                })
                sub_title = ET.SubElement(sub_item, "title")
                sub_title.text = page.title
            else:
                page_item = ET.SubElement(module_item, "item", {
                    "identifier": f"{page.identifier}_ITEM",
                    "identifierref": page.identifier,
                })
                page_title = ET.SubElement(page_item, "title")
                page_title.text = page.title

    # --- <resources> ---
    resources = ET.SubElement(manifest, "resources")

    for module in course.modules:
        for page in module.pages:
            if page.resource_type == "subheader":
                continue

            resource_attribs = {
                "identifier": page.identifier,
                "type": page.resource_type,
            }

            if page.html_filename:
                resource_attribs["href"] = page.html_filename

            resource = ET.SubElement(resources, "resource", resource_attribs)

            # Archivo principal (HTML, XML de Link, XML de Foro o XML de Quiz)
            if page.html_filename:
                ET.SubElement(resource, "file", {"href": page.html_filename})

                # Archivos adicionales para tipos complejos
                if "associatedcontent" in page.resource_type:
                    # Tarea: agregar settings
                    settings_path = page.html_filename.replace("actividad.html", "assignment_settings.xml")
                    ET.SubElement(resource, "file", {"href": settings_path})
                
                elif "imsqti" in page.resource_type:
                    # Quiz: agregar meta
                    meta_path = page.html_filename.replace("assessment_qti.xml", "assessment_meta.xml")
                    ET.SubElement(resource, "file", {"href": meta_path})

            # Archivos multimedia asociados
            for mf in page.media_files:
                ET.SubElement(resource, "file", {"href": f"media/{mf.filename}"})

            # Imágenes extraídas del DOCX
            for img in page.docx_images:
                ET.SubElement(resource, "file", {"href": f"media/{img.filename}"})

    # Agregar recursos de archivos multimedia globales (no asociados a páginas)
    for filename, media_file in course.all_media.items():
        media_res_id = f"{course.identifier}_MEDIA_{filename.replace('.', '_').upper()}"
        media_resource = ET.SubElement(resources, "resource", {
            "identifier": media_res_id,
            "type": "webcontent",
            "href": f"media/{filename}",
        })
        ET.SubElement(media_resource, "file", {"href": f"media/{filename}"})

    # Formatear XML
    xml_string = ET.tostring(manifest, encoding="unicode", xml_declaration=False)
    xml_declaration = f'<?xml version="1.0" encoding="{ENCODING}"?>\n'

    # Pretty print
    try:
        dom = minidom.parseString(xml_string)
        pretty_xml = dom.toprettyxml(indent="  ", encoding=None)
        # Remover declaración XML duplicada de minidom
        lines = pretty_xml.split("\n")
        if lines[0].startswith("<?xml"):
            lines = lines[1:]
        formatted = xml_declaration + "\n".join(lines)
    except Exception:
        formatted = xml_declaration + xml_string

    logger.info(f"imsmanifest.xml generado ({len(formatted)} chars)")
    return formatted


def _add_weblink_resource(resource_element: ET.Element, page: PageResource):
    """Agrega contenido de web link al recurso."""
    # Canvas espera un archivo XML con la URL para web links
    pass  # Se genera como archivo aparte en page_builder
