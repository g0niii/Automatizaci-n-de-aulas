# -*- coding: utf-8 -*-
"""Construcción de componentes CidiLabs a partir de los pedidos del asesor.

Un extractor de pares (título, contenido) unificado alimenta a acordeón, tabs,
expander y flip card. Dos fuentes: una tabla de 1 columna con celdas alternadas
(título/contenido/título/contenido…) o párrafos "Nombre: contenido".
"""

import re

from bs4 import BeautifulSoup

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
