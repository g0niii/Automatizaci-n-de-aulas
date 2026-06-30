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

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Acciones que se aplican solas vs. las que solo se avisan.
# "quitar" NO se automatiza: a veces es un micro-pedido ("quitar los dos puntos")
# y borrar el párrafo entero sería un error; se avisa para hacerlo a mano.
_AUTO = {"subtitulo", "recuadro_simple", "lectura", "video", "sin_recuadro"}


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
    if any(k in n for k in ("expander", "expandible", "expandir", "acordeon-simple")):
        return "expander"
    if any(k in n for k in ("flip card", "flipcard", "flip-card", "tarjeta",
                            "se dan vuelta", "se da vuelta")):
        return "flip_card"
    if any(k in n for k in ("tooltip", "al hacer clic", "al hacer click",
                            "emerja", "emerge", "aparezca", "popover", "globo")):
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


def aplicar_comentarios(soup, comentarios: list) -> None:
    """Aplica al soup las acciones automáticas cuyo texto anclado aparezca en
    él. Marca c['_aplicado']=True en los que aplica. Se llama una vez por cada
    sección ya cortada (así un comentario se aplica en la sección que lo
    contiene y nunca rompe los límites de sección)."""
    for c in comentarios:
        accion = c["accion"]
        if accion not in _AUTO or c.get("_aplicado"):
            continue                        # no-auto, o ya aplicado en otra sección
        el = _buscar_elemento(soup, c["anclado"])
        if el is None:
            continue
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
