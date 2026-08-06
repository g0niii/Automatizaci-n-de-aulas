"""
Inyector XML ultra-seguro para UCC.
Manipula imsmanifest.xml y module_meta.xml preservando la estructura del aula base.
"""

import re
import logging

logger = logging.getLogger("xml_injector")

def inject_manifest(xml_text: str, module_title: str, pages: dict) -> str:
    """
    Actualiza el Modulo 1 en el manifiesto sin tocar el resto.
    """
    # 1. Actualizar el titulo del modulo 1
    # Buscamos el item que contiene "Modulo 1:"
    module_pattern = re.compile(r'(<item identifier="[^"]+">\s*<title>)\s*Modulo 1:[^<]*(</title>)', re.IGNORECASE)
    xml_text = module_pattern.sub(rf'\g<1>{module_title}\2', xml_text, count=1)

    # 2. Reemplazar el bloque de items del modulo 1
    # Buscamos el bloque de items dentro del item del modulo
    # El placeholder original 1.1 tiene un identifierref especifico o un titulo patron
    
    # Primero identificamos donde empieza el modulo 1
    mod_start = xml_text.find(module_title)
    if mod_start == -1:
        # Reintentar con el titulo generico si el anterior fallo
        mod_start = xml_text.lower().find("modulo 1:")
    
    if mod_start != -1:
        # Buscamos el final del item del modulo (donde cierran sus hijos)
        # En el imsmanifest, los sub-items estan anidados
        # Placeholder 1.1:
        placeholder_regex = re.compile(r'(<item identifier="[^"]+" identifierref="[^"]+">\s*<title>[^<]*1\.1\.[^<]*</title>\s*</item>)')
        
        new_items_xml = ""
        for num in sorted(pages.keys()):
            filepath, page_id, title = pages[num]
            new_items_xml += f"""
          <item identifier="g_item_{num.replace(".","_")}" identifierref="{page_id}">
            <title>{title}</title>
          </item>"""
        
        # Reemplazamos solo el placeholder 1.1
        xml_text = placeholder_regex.sub(new_items_xml, xml_text, count=1)
    
    # 3. Agregar los nuevos recursos al final de <resources>
    res_list = ""
    for num in sorted(pages.keys()):
        filepath, page_id, title = pages[num]
        res_list += f"""
    <resource identifier="{page_id}" type="webcontent" href="{filepath}">
      <file href="{filepath}"/>
    </resource>"""
    
    if "</resources>" in xml_text:
        xml_text = xml_text.replace("</resources>", res_list + "\n  </resources>")

    return xml_text

def inject_module_meta(xml_text: str, module_title: str, pages: dict) -> str:
    """
    Actualiza module_meta.xml respetando todos los modulos.
    """
    # 1. Titulo del modulo
    xml_text = re.sub(r'(<title>)\s*Modulo 1:[^<]*(</title>)', rf'\g<1>{module_title}\2', xml_text, flags=re.IGNORECASE)
    
    # 2. Items del modulo
    # Buscamos el bloque de items del modulo 1
    # Buscamos la etiqueta <title>Modulo 1...</title> y luego el <items> que le sigue
    
    mod_match = re.search(rf'<module [^>]*>\s*<title>{re.escape(module_title)}</title>.*?(<items>.*?</items>)', xml_text, re.DOTALL)
    
    if mod_match:
        items_block = mod_match.group(1)
        
        # Placeholder 1.1 en meta
        placeholder_regex = re.compile(r'(\s*<item identifier="[^"]*">\s*<content_type>WikiPage</content_type>\s*<workflow_state>active</workflow_state>\s*<title>[^<]*1\.1\.[^<]*</title>.*?</item>)', re.DOTALL)
        
        new_meta_items = ""
        for i, num in enumerate(sorted(pages.keys())):
            filepath, page_id, title = pages[num]
            new_meta_items += f"""
      <item identifier="g_meta_{num.replace(".","_")}">
        <content_type>WikiPage</content_type>
        <workflow_state>active</workflow_state>
        <title>{title}</title>
        <identifierref>{page_id}</identifierref>
        <position>{i + 3}</position>
        <new_tab>false</new_tab>
        <indent>0</indent>
        <link_settings_json>null</link_settings_json>
      </item>"""
        
        # Reemplazar el placeholder dentro del bloque de items
        new_items_block = placeholder_regex.sub(new_meta_items, items_block, count=1)
        
        # Reemplazar el bloque viejo por el nuevo en el XML total
        xml_text = xml_text.replace(items_block, new_items_block)
        
    return xml_text
