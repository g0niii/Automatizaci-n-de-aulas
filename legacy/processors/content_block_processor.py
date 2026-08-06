"""
Procesador de bloques de contenido CIDILABS - VERSIÓN PIXEL PERFECT.
Basado en el HTML real proporcionado por el usuario.
"""

from bs4 import BeautifulSoup

def process_content_blocks(html_content, colors=None):
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, "html.parser")
    
    # 1. Transformar "Introducción" con el estilo exacto solicitado
    for header in soup.find_all(["h1", "h2", "h3"]):
        text = header.get_text().lower()
        if "introducción" in text or "introduccion" in text:
            # Crear el bloque con fondo gris
            block = soup.new_tag("div", attrs={
                "class": "dp-content-block kl_objectives2", 
                "style": "background-color: #f8f8f8; color: #000000;"
            })
            
            # H2 con icono y clases de borde/tamaño
            new_h2 = soup.new_tag("h2", attrs={"class": "dp-has-icon"})
            icon_i = soup.new_tag("i", attrs={"class": "fas fa-book dp-i-border-mid dp-i-size-small", "aria-hidden": "true"})
            span_hidden = soup.new_tag("span", attrs={"class": "dp-icon-content", "style": "display: none;"})
            span_hidden.string = " "
            icon_i.append(span_hidden)
            
            new_h2.append(icon_i)
            new_h2.append(soup.new_string(" Introducción"))
            block.append(new_h2)
            
            # Mover el contenido
            curr = header.next_sibling
            while curr and curr.name not in ["h1", "h2", "h3"]:
                next_node = curr.next_sibling
                block.append(curr)
                curr = next_node
            
            # Agregar el placeholder de lista de objetivos al final de la intro
            block.append(soup.new_tag("ol", attrs={"id": "kl_objective_list"}))
            header.replace_with(block)

        elif "objetivos" in text:
            # Bloque de Objetivos con icono de bandera
            block = soup.new_tag("div", attrs={"class": "dp-content-block kl_readings2"})
            
            new_h2 = soup.new_tag("h2", attrs={"class": "dp-has-icon"})
            icon_i = soup.new_tag("i", attrs={"class": "fas fa-flag", "aria-hidden": "true"})
            span_hidden = soup.new_tag("span", attrs={"class": "dp-icon-content", "style": "display: none;"})
            span_hidden.string = " "
            icon_i.append(span_hidden)
            
            new_h2.append(icon_i)
            new_h2.append(soup.new_string(" Objetivos"))
            block.append(new_h2)
            
            # Mover el contenido
            curr = header.next_sibling
            while curr and curr.name not in ["h1", "h2", "h3"]:
                next_node = curr.next_sibling
                block.append(curr)
                curr = next_node
            
            header.replace_with(block)

    # 2. Transformar "Para reflexionar" en el Callout Amarillo
    for p in soup.find_all("p"):
        if p.get_text().strip().lower().startswith("para reflexionar"):
            callout = soup.new_tag("div", attrs={"class": "dp-callout dp-callout-placeholder card dp-callout-position-default dp-callout-type-info dp-callout-color-warning"})
            side = soup.new_tag("div", attrs={"class": "dp-callout-side-emphasis", "style": "background-color: #f4e600; color: #000000;"})
            side.append(soup.new_tag("i", attrs={"class": "dp-icon fas fa-lightbulb dp-default-icon"}))
            
            body = soup.new_tag("div", attrs={"class": "card-body"})
            body.append(soup.new_tag("h3", attrs={"class": "card-title", "style": "color: #757121;"}))
            body.h3.string = "Para reflexionar"
            
            content_p = soup.new_tag("p")
            content_p.string = p.get_text().replace("Para reflexionar", "").strip(": ").strip()
            body.append(content_p)
            
            callout.append(side)
            callout.append(body)
            p.replace_with(callout)

    return str(soup)
