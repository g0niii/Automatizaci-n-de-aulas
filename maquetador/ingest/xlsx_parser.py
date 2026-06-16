# -*- coding: utf-8 -*-
"""Parser de la planilla "Estructura general - Para maquetación".

Detecta y soporta los dos formatos reales observados:

  VIEJO (5 columnas)  — header "Link Drive:" en fila 1.
      A: bloque/módulo   B: ítem   C: estado   D: coment. asesor   E: coment. maquetador

  NUEVO (9 columnas, "Planilla de montaje" V3) — bloque "DATOS DE LA ASIGNATURA"
      arriba con código, nombre, horas y colaboradores; luego la grilla:
      A: bloque/módulo   B: ítem   C: título actividad   D: modalidad
      E: tipo de entrega  F: link/archivo  G: estado  H/I: comentarios

Ambos comparten la misma lógica de bloques: la columna A marca el bloque
(Página de inicio / Programa / Módulo N / Actividad final Integradora) y la
columna B los ítems, con separadores INTRODUCCIÓN / CONTENIDOS / ACTIVIDADES.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl

from maquetador.models import (CourseSpec, ModuloCurso, ItemCurso, TipoItem,
                               Issue, Severidad)
from maquetador.ingest.folder_scanner import normalizar

_PAT_NUMERADO = re.compile(r"^(\d+)\.\s*(\d+)?\.?\s*")


@dataclass
class FilaPlanilla:
    bloque: str
    item: str
    titulo_actividad: str = ""
    modalidad: str = ""
    tipo_entrega: str = ""
    referencia: str = ""   # columna LINK (formato nuevo) o comentario asesor (viejo)
    estado: str = ""
    comentario_asesor: str = ""


def _detectar_formato(filas: list) -> str:
    for fila in filas[:12]:
        celda = normalizar(str(fila[0] or ""))
        if "datos de la asignatura" in celda:
            return "nuevo"
        if celda.startswith("link drive"):
            return "viejo"
    return "desconocido"


def _leer_filas(path: Path) -> list:
    wb = openpyxl.load_workbook(str(path), data_only=True)
    ws = wb.active
    filas = []
    for row in ws.iter_rows(values_only=True):
        celdas = [str(c).strip() if c is not None else "" for c in row]
        celdas += [""] * (9 - len(celdas))
        filas.append(celdas)
    wb.close()
    return filas


def _extraer_metadata_nuevo(filas: list, spec: CourseSpec):
    """Lee el bloque DATOS DE LA ASIGNATURA / COLABORADORES del formato nuevo."""
    for i, f in enumerate(filas[:20]):
        clave = normalizar(f[0])
        valor = next((c for c in f[1:] if c), "")
        if clave.startswith("codigo de la asignatura") and valor:
            spec.codigo = valor
        elif clave == "nombre" and valor:
            spec.nombre = valor
        elif clave == "contenidista" and valor:
            spec.docentes.append(valor)


def _clasificar_item(texto: str, seccion_actual: str) -> TipoItem:
    n = normalizar(texto)
    if _PAT_NUMERADO.match(texto):
        return TipoItem.PAGINA
    if "foro" in n:
        return TipoItem.FORO
    if "video" in n:
        return TipoItem.VIDEO
    # Intro del módulo: "Texto introductorio", "Introducción al módulo", o
    # cualquier ítem de la sección Introducción que hable de introducción
    # (el foro y el video ya se filtraron arriba).
    if "texto introductorio" in n or "introduccion al modulo" in n or \
            (seccion_actual == "introduccion" and "introduccion" in n):
        return TipoItem.INTRO_MODULO
    if n.startswith("tarea"):
        return TipoItem.TAREA
    if n.startswith("evaluacion"):
        return TipoItem.EVALUACION
    if "programa" in n or "hoja de ruta" in n:
        return TipoItem.ARCHIVO
    if "fotografia" in n or "esquema" in n:
        return TipoItem.IMAGEN
    if "titulacion" in n or "biografia" in n:
        return TipoItem.PAGINA
    if seccion_actual == "actividades":
        return TipoItem.TAREA
    return TipoItem.OTRO


_SECCIONES = {
    "introduccion": "introduccion",
    "contenidos": "contenidos",
}


def _es_separador_seccion(texto: str) -> str:
    """Devuelve el nombre de sección si la celda B es un separador (INTRODUCCIÓN,
    CONTENIDOS, ACTIVIDADES…), o ''."""
    n = normalizar(texto)
    if n in _SECCIONES:
        return _SECCIONES[n]
    if n.startswith("actividades"):
        return "actividades"
    return ""


def parsear_estructura(path: Path) -> CourseSpec:
    filas = _leer_filas(path)
    formato = _detectar_formato(filas)
    spec = CourseSpec(nombre=path.stem)

    if formato == "desconocido":
        spec.issues.append(Issue(Severidad.BLOQUEANTE,
            f"No reconozco el formato de la planilla '{path.name}'. "
            "Esperaba el formato viejo (header 'Link Drive:') o el nuevo "
            "('DATOS DE LA ASIGNATURA')."))
        return spec

    if formato == "nuevo":
        _extraer_metadata_nuevo(filas, spec)

    # Localizar la fila donde arranca la grilla
    inicio = 0
    for i, f in enumerate(filas):
        if normalizar(f[0]).startswith("link drive"):
            inicio = i + 1
            break

    bloque_actual = ""
    seccion_actual = ""
    modulo_actual = None
    orden = 0

    for f in filas[inicio:]:
        if formato == "nuevo":
            fila = FilaPlanilla(bloque=f[0], item=f[1], titulo_actividad=f[2],
                                modalidad=f[3], tipo_entrega=f[4], referencia=f[5],
                                estado=f[6], comentario_asesor=f[7])
        else:
            fila = FilaPlanilla(bloque=f[0], item=f[1], estado=f[2],
                                referencia=f[3], comentario_asesor=f[3])

        # --- Cambio de bloque (columna A) ---
        if fila.bloque:
            nb = normalizar(fila.bloque)
            if "observaciones" in nb:
                break
            m = re.match(r"modulo\s*(\d+)", nb)
            if m:
                titulo = re.sub(r"^m[óo]dulo\s*\d+\s*:?", "", fila.bloque,
                                flags=re.I).strip().strip(":").replace("\n", " ").strip()
                if normalizar(titulo) in ("", "nombre del modulo"):
                    titulo = ""
                modulo_actual = ModuloCurso(numero=int(m.group(1)), titulo=titulo)
                spec.modulos.append(modulo_actual)
                bloque_actual = "modulo"
                seccion_actual = ""
            elif "actividad final" in nb or re.search(r"\bafi\b", nb):
                bloque_actual = "afi"
                modulo_actual = None
                seccion_actual = ""
                # El AFI suele venir en la MISMA fila (su título está en la
                # columna A); si no hay un ítem aparte, se crea acá.
                if not fila.item:
                    orden += 1
                    spec.afi.append(ItemCurso(
                        titulo=(fila.titulo_actividad or fila.bloque).strip(),
                        tipo=_clasificar_item(fila.bloque, "afi"), orden=orden,
                        estado_planilla=fila.estado,
                        comentarios_asesor=fila.comentario_asesor,
                        detalle={k: v for k, v in {
                            "item_planilla": fila.bloque.strip(),
                            "referencia": fila.referencia,
                        }.items() if v}))
                    continue
            else:
                bloque_actual = "inicio"   # Página de inicio, Programa, etc.
                modulo_actual = None

        if not fila.item:
            continue

        # --- Separadores de sección dentro del módulo ---
        sep = _es_separador_seccion(fila.item)
        if sep:
            seccion_actual = sep
            continue

        # --- Ítem real ---
        orden += 1
        tipo = _clasificar_item(fila.item, seccion_actual)
        item = ItemCurso(
            titulo=fila.titulo_actividad or fila.item,
            tipo=tipo, orden=orden,
            estado_planilla=fila.estado,
            comentarios_asesor=fila.comentario_asesor,
            detalle={k: v for k, v in {
                "item_planilla": fila.item,
                "modalidad": fila.modalidad,
                "tipo_entrega": fila.tipo_entrega,
                "referencia": fila.referencia,
                "seccion": seccion_actual or bloque_actual,
            }.items() if v},
        )

        if bloque_actual == "modulo" and modulo_actual is not None:
            modulo_actual.items.append(item)
        elif bloque_actual == "afi":
            spec.afi.append(item)
        else:
            spec.items_inicio.append(item)

    if not spec.modulos:
        spec.issues.append(Issue(Severidad.BLOQUEANTE,
            "La planilla no tiene módulos reconocibles (filas 'Módulo N' en la columna A)."))
    return spec
