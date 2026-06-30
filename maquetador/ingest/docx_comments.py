# -*- coding: utf-8 -*-
"""Lectura de los COMENTARIOS de los DOCX (los globos al margen).

Los asesores dejan pedidos de maquetación como comentarios anclados a un texto:
  "Para maquetación, subtítulo."        → ese texto va como <h3>
  "Para maquetación, recuadro simple."  → recuadro
  "Para maquetación, no resaltar/sin recuadro/con sangría" → NO encuadrar
  "Para maquetación: para la lectura"   → CTA Lectura
  "Para maquetación, acordeón / flip card" → componente (se avisa, es manual)
  "Sugiero quitar…"                      → se elimina ese texto

Este módulo extrae cada comentario JUNTO con el texto al que está anclado
(de word/comments.xml + word/document.xml), lo clasifica en una acción y
aplica las acciones simples al HTML ya convertido. Las que no se pueden
automatizar (acordeón, flip card, pedidos sueltos) se devuelven para avisarlas
en el plan.
"""

import re
import zipfile
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from maquetador.ingest.folder_scanner import normalizar
from maquetador.build.snippets import resaltado_simple, cta_titulo, ICONOS
from maquetador.build.componentes_asesor import (
    extraer_pares, construir_panels, construir_flipcards,
    construir_popover, aplicar_cita,
)

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Acciones que se aplican solas vs. las que solo se avisan.
# "quitar" NO se automatiza: a veces es un micro-pedido ("quitar los dos puntos")
# y borrar el párrafo entero sería un error; se avisa para hacerlo a mano.
_AUTO = {"subtitulo", "recuadro_simple", "lectura", "video", "sin_recuadro"}

_COMPONENTES = {"acordeon", "tabs", "expander", "flip_card", "tooltip", "cita"}
_VARIANTE_PANEL = {"acordeon": "dp-expander-default",
                   "tabs": "dp-tabs",
                   "expander": "dp-expander-default"}


def _clasificar(instruccion: str) -> str:
    """Mapea el texto del comentario a una acción de maquetación (o None si es
    charla interna del equipo, no una instrucción)."""
    n = normalizar(instruccion)
    if not n:
        return None
    # Señales negativas primero (NO encuadrar)
    if any(k in n for k in ("sin recuadro", "sin cuadro", "no resaltar",
                            "no encuadrar", "con sangria", "sangria sin")):
        return "sin_recuadro"
    if "subtitulo" in n:
        return "subtitulo"
    if "acordeon" in n:
        return "acordeon"
    if any(k in n for k in ("tab ", "tabs", "pestana", "pestanas", "solapa")):
        return "tabs"
    if any(k in n for k in ("expander", "expandible", "expandir")):
        return "expander"
    if any(k in n for k in ("flip card", "flipcard", "flip-card", "tarjeta",
                            "se dan vuelta", "se da vuelta")):
        return "flip_card"
    if ("tooltip" in n or "popover" in n or "globo" in n
            or (("clic" in n or "click" in n)
                and ("emerj" in n or "emerge" in n or "aparezca" in n))):
        return "tooltip"
    if any(k in n for k in ("es una cita", "esto es una cita", "es cita", "como cita")):
        return "cita"
    if any(k in n for k in ("quitar", "sacar", "eliminar", "borrar")):
        return "quitar"
    if "recuadro" in n or "resalta" in n:
        return "recuadro_simple"
    if "lectura" in n:
        return "lectura"
    if re.search(r"\bvideo\b", n):
        return "video"
    if any(k in n for k in ("falta", "faltante", "pendiente", "hace falta",
                            "no se pudo", "a definir", "queda pendiente",
                            "sin terminar", "incompleto", "no esta disponible",
                            "esperando")):
        return "faltante"
    if n.startswith(("para maquetacion", "para el maquetado", "para diseno",
                     "para diseño", "maquetacion")):
        return "revisar"
    return None


def extraer_comentarios(docx_path) -> list:
    """[{instruccion, anclado, accion, autor}] de un DOCX. [] si no tiene."""
    try:
        with zipfile.ZipFile(docx_path) as z:
            if "word/comments.xml" not in z.namelist():
                return []
            comments_xml = z.read("word/comments.xml")
            document_xml = z.read("word/document.xml")
    except Exception:
        return []

    croot = ET.fromstring(comments_xml)
    textos, autores = {}, {}
    for c in croot.findall(f"{_W}comment"):
        cid = c.get(f"{_W}id")
        textos[cid] = " ".join(t.text or "" for t in c.iter(f"{_W}t")).strip()
        autores[cid] = c.get(f"{_W}author", "")

    # Texto anclado: lo que está entre commentRangeStart/End (en orden de doc).
    droot = ET.fromstring(document_xml)
    activos = set()
    anclado = {cid: [] for cid in textos}
    for el in droot.iter():
        tag = el.tag
        if tag == f"{_W}commentRangeStart":
            activos.add(el.get(f"{_W}id"))
        elif tag == f"{_W}commentRangeEnd":
            activos.discard(el.get(f"{_W}id"))
        elif tag == f"{_W}t" and activos:
            for cid in activos:
                if cid in anclado:
                    anclado[cid].append(el.text or "")

    out = []
    for cid, instr in textos.items():
        accion = _clasificar(instr)
        if not accion:
            continue   # charla interna, no es instrucción de maquetación
        out.append({
            "instruccion": re.sub(r"\s+", " ", instr).strip(),
            "anclado": "".join(anclado.get(cid, [])).strip(),
            "accion": accion,
            "autor": autores.get(cid, ""),
        })
    return out


def _buscar_elemento(soup, anclado: str):
    """Encuentra el <p>/<li> cuyo texto corresponde al texto anclado."""
    objetivo = normalizar(anclado)
    if len(objetivo) < 6:
        return None
    clave = objetivo[:45]
    for el in soup.find_all(["p", "li"]):
        t = normalizar(el.get_text(" ", strip=True))
        if not t:
            continue
        if t.startswith(clave) or objetivo.startswith(t[:45]) or clave in t:
            return el
    return None


def _texto_tooltip(instruccion: str) -> str:
    """Saca el contenido del popover del comentario: lo que va después de
    'emerja:'/'aparezca:'/'tooltip-->'. Si no hay marcador claro, '' (→ fallback)."""
    for sep in ("emerja lo siguiente:", "emerja:", "aparezca:", "emerge:",
                "tooltip-->", "tooltip -->", "tooltip:", "globo:"):
        if sep in instruccion.lower():
            idx = instruccion.lower().index(sep) + len(sep)
            return instruccion[idx:].strip(" .–-")
    return ""


def aplicar_comentarios(soup, comentarios: list) -> None:
    """Aplica al soup las acciones automáticas cuyo texto anclado aparezca en
    él, y arma los componentes de pedido del asesor (acordeon/tabs/expander/
    flip_card/tooltip/cita) cuando hay estructura suficiente. Marca
    c['_aplicado']=True solo en los que efectivamente se aplican. Se llama una
    vez por cada sección ya cortada (así un comentario se aplica en la sección
    que lo contiene y nunca rompe los límites de sección)."""
    contador_popover = 0
    for c in comentarios:
        accion = c["accion"]
        if c.get("_aplicado"):
            continue
        if accion not in _AUTO and accion not in _COMPONENTES:
            continue
        el = _buscar_elemento(soup, c["anclado"])
        if el is None:
            continue

        # --- Componentes de pedido del asesor ---
        if accion in _VARIANTE_PANEL:                 # acordeon / tabs / expander
            pares, consumidos = extraer_pares(el)
            if len(pares) >= 2:
                html = construir_panels(pares, _VARIANTE_PANEL[accion])
                consumidos[0].replace_with(BeautifulSoup(html, "html.parser"))
                for extra in consumidos[1:]:
                    extra.decompose()
                c["_aplicado"] = True
            continue
        if accion == "flip_card":
            pares, consumidos = extraer_pares(el)
            if len(pares) >= 2:
                html = construir_flipcards(pares)
                consumidos[0].replace_with(BeautifulSoup(html, "html.parser"))
                for extra in consumidos[1:]:
                    extra.decompose()
                c["_aplicado"] = True
            continue
        if accion == "tooltip":
            contenido = _texto_tooltip(c["instruccion"])
            palabra = (c["anclado"] or "").strip()
            if contenido and palabra:
                trigger, content = construir_popover(palabra, contenido, contador_popover)
                contador_popover += 1
                nuevo = BeautifulSoup(
                    el.get_text(" ", strip=True).replace(palabra, trigger, 1)
                    + content, "html.parser")
                el.replace_with(nuevo)
                c["_aplicado"] = True
            continue
        if accion == "cita":
            aplicar_cita(el)
            c["_aplicado"] = True
            continue

        # --- Acciones simples existentes ---
        c["_aplicado"] = True
        inner = "".join(str(x) for x in el.children).strip()
        if accion == "subtitulo":
            h3 = soup.new_tag("h3")
            h3.string = el.get_text(" ", strip=True)
            el.replace_with(h3)
        elif accion == "quitar":
            el.decompose()
        elif accion == "recuadro_simple":
            el.replace_with(BeautifulSoup(resaltado_simple(inner), "html.parser"))
        elif accion == "lectura":
            el.replace_with(BeautifulSoup(
                cta_titulo("Lectura", f"<p>{inner}</p>", ICONOS["lectura"]),
                "html.parser"))
        elif accion == "video":
            el.replace_with(BeautifulSoup(
                cta_titulo("Video", f"<p>{inner}</p>", ICONOS["video"]),
                "html.parser"))
        elif accion == "sin_recuadro":
            # El asesor pide NO encuadrar: se marca para que procesar_contenido
            # no lo convierta en recuadro por sus heurísticas.
            el["data-keep-plain"] = "1"
