# -*- coding: utf-8 -*-
"""Construcción de componentes CidiLabs a partir de los pedidos del asesor.

Un extractor de pares (título, contenido) unificado alimenta a acordeón, tabs,
expander y flip card. Dos fuentes: una tabla de 1 columna con celdas alternadas
(título/contenido/título/contenido…) o párrafos "Nombre: contenido".
"""

import re

_RE_NOMBRE_CONTENIDO = re.compile(r"^(.{2,60}?):\s+(.+)$", re.DOTALL)


def pares_de_tabla(tabla) -> list:
    """Tabla de 1 columna con celdas alternadas → [(titulo, contenido_html)]."""
    celdas = tabla.find_all(["td", "th"])
    plano = []
    for c in celdas:
        texto = c.get_text(" ", strip=True)
        inner = "".join(str(x) for x in c.children).strip()
        if texto:
            plano.append((texto, inner))
    pares = []
    for i in range(0, len(plano) - 1, 2):
        titulo = plano[i][0]
        contenido = plano[i + 1][1] or "&nbsp;"
        pares.append((titulo, contenido))
    return pares


def pares_de_texto(parrafos: list) -> list:
    """Párrafos 'Nombre: contenido' → [(nombre, contenido)]."""
    pares = []
    for p in parrafos:
        txt = p.get_text(" ", strip=True)
        m = _RE_NOMBRE_CONTENIDO.match(txt)
        if m:
            pares.append((m.group(1).strip(), m.group(2).strip()))
    return pares


def extraer_pares(el):
    """Desde el elemento anclado → (pares, consumidos). ([], []) si <2 pares.

    `consumidos` son los elementos del soup que el componente reemplaza: el
    primero se sustituye por el componente y el resto se elimina (así no quedan
    párrafos duplicados cuando el componente se arma desde varios párrafos).

    1) Tabla asociada (el mismo, o su hermano <table> siguiente).
    2) Si no, el elemento + hermanos <p>/<li> consecutivos con 'Nombre: contenido'.
    """
    # 1) Tabla
    if el.name == "table":
        tabla, consumidos_tabla = el, [el]
    else:
        t = el.find_next_sibling("table")
        tabla, consumidos_tabla = (t, [el, t]) if t is not None else (None, None)
    if tabla is not None:
        pares = pares_de_tabla(tabla)
        if len(pares) >= 2:
            return pares, consumidos_tabla

    # 2) Texto
    parrafos, actual = [], el
    while actual is not None and getattr(actual, "name", None) in ("p", "li"):
        parrafos.append(actual)
        actual = actual.find_next_sibling()
    pares = pares_de_texto(parrafos)
    if len(pares) >= 2:
        consumidos = [p for p in parrafos
                      if _RE_NOMBRE_CONTENIDO.match(p.get_text(" ", strip=True))]
        return pares, consumidos
    return [], []


def construir_panels(pares: list, variante: str = "dp-expander-default") -> str:
    """Acordeón (dp-expander-default) / tabs (dp-tabs) / expander. Misma
    estructura; cambia la clase del wrapper."""
    grupos = "\n".join(
        '<div class="dp-panel-group">\n'
        f'<h3 class="dp-panel-heading">{t}</h3>\n'
        f'<div class="dp-panel-content">{c}</div>\n</div>'
        for t, c in pares)
    return (f'<div class="dp-panels-wrapper {variante} '
            'dp-panel-color-dp-secondary dp-panel-active-color-dp-primary" '
            f'title="contenido insertado">\n{grupos}\n</div>')


def construir_flipcards(pares: list) -> str:
    """Flip cards CidiLabs: frente = título (negrita), dorso = contenido."""
    cards = "\n".join(
        '<div class="dp-flip-card">\n<div class="dp-flip-card-inner">\n'
        '<div class="dp-front-card">'
        '<div class="dp-card card h-100 dp-shadow-b3 text-center">'
        f'<p><strong>{t}</strong></p></div></div>\n'
        '<div class="dp-back-card">'
        '<div class="dp-card card h-100 text-center dp-shadow-b3" style="padding: 16px;">'
        f'<p style="text-align: left;">{c}</p></div></div>\n'
        '</div>\n</div>'
        for t, c in pares)
    return f'<div class="row justify-content-center">\n{cards}\n</div>'


def construir_popover(palabra: str, contenido: str, n: int) -> tuple:
    """Popover CidiLabs: trigger (la palabra) + content (lo que emerge)."""
    trigger = (f'<a class="dp-popover-trigger" href="#dpPopup{n}Content" '
               f'id="dpPopup{n}" aria-describedby="dpPopup{n}Content">{palabra}</a>')
    content = (f'<div class="dp-popover-content dp-popup-content" id="dpPopup{n}Content" '
               'style="border: 1px solid #A9A9A9; background: #f7f7f7; padding: 10px; '
               'width: 600px; max-width: 100%; margin: auto; border-radius: 3px;">'
               f'<p>{contenido}</p></div>')
    return trigger, content


def aplicar_cita(el) -> None:
    """Sangra el párrafo anclado (sin caja, pedido del usuario)."""
    estilo = el.get("style", "").rstrip("; ")
    el["style"] = (estilo + "; " if estilo else "") + "margin-left: 40px;"
