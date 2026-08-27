# -*- coding: utf-8 -*-
"""Fixtures compartidas para los tests del proyecto de maquetación."""

import pytest
from pathlib import Path
from maquetador.models import CourseSpec, ModuloCurso, ItemCurso, TipoItem


@pytest.fixture
def casos_dir():
    """Retorna la ruta del directorio 'Aulas a generar/' con archivos XLSX de prueba."""
    return Path(__file__).parent.parent / "Aulas a generar"


@pytest.fixture
def xlsx_files_reales(casos_dir):
    """Retorna paths a archivos XLSX reales encontrados en 'Aulas a generar/'."""
    archivos = []
    for xlsx in casos_dir.rglob("Estructura general*.xlsx"):
        archivos.append(xlsx)
    # También buscar archivos que empiecen con "Estructura general"
    for xlsx in casos_dir.rglob("*Estructura general*.xlsx"):
        if xlsx not in archivos:
            archivos.append(xlsx)
    return sorted(archivos)


@pytest.fixture
def filas_formato_viejo():
    """Filas de prueba para formato viejo (5 columnas, header 'Link Drive:')."""
    return [
        ["Link Drive:", "", "", "", ""],
        ["Página de inicio", "Programa", "Completo", "comentario", ""],
        ["Módulo 1", "1.1. Introducción", "Incompleto", "", "revisar"],
        ["", "1.2. Contenidos", "Completo", "", ""],
        ["", "CONTENIDOS", "", "", ""],
        ["", "1.3. Foro de debate", "Completo", "", ""],
        ["", "ACTIVIDADES", "", "", ""],
        ["", "1.4. Tarea 1", "Incompleto", "", "entregar antes del viernes"],
        ["Módulo 2", "2.1. Introducción al módulo", "Completo", "", ""],
        ["", "CONTENIDOS", "", "", ""],
        ["", "2.1. Video introductorio", "Completo", "", ""],
    ]


@pytest.fixture
def filas_formato_nuevo():
    """Filas de prueba para formato nuevo (9 columnas, con DATOS DE LA ASIGNATURA)."""
    return [
        ["DATOS DE LA ASIGNATURA", "", "", "", "", "", "", "", ""],
        ["Código de la asignatura", "EP00356", "", "", "", "", "", "", ""],
        ["Nombre", "Ética y cumplimiento corporativo", "", "", "", "", "", "", ""],
        ["Contenidista", "Dr. Juan Pérez", "", "", "", "", "", "", ""],
        ["", "", "", "", "", "", "", "", ""],
        ["Link Drive:", "", "", "", "", "", "", "", ""],
        ["Página de inicio", "Programa", "Programa del curso", "PDF", "Descarga", "link_aqui", "Completo", "OK", ""],
        ["Módulo 1", "1.1. Introducción", "Texto intro módulo", "Lectura", "Individual", "", "Completo", "Revisar formato", ""],
        ["", "INTRODUCCIÓN", "", "", "", "", "", "", ""],
        ["", "1.1. Texto introductorio", "Introducción al módulo", "Lectura", "", "", "Completo", "", ""],
        ["", "CONTENIDOS", "", "", "", "", "", "", ""],
        ["", "1.2. Conceptos fundamentales", "Video sobre ética", "Video", "", "url_video", "Completo", "", ""],
        ["", "1.3. Esquema conceptual", "Esquema de decisión ética", "Imagen", "", "url_imagen", "Completo", "", ""],
        ["", "ACTIVIDADES", "", "", "", "", "", "", ""],
        ["", "1.4. Foro de análisis", "Foro semanal", "Foro", "Grupal", "", "Incompleto", "Falta moderar", ""],
        ["", "1.5. Evaluación formativa", "Evaluación módulo 1", "Evaluación", "Individual", "", "Completo", "", ""],
        ["Módulo 2", "2.1. Introducción", "Intro módulo 2", "Lectura", "", "", "Completo", "", ""],
        ["Actividad Final Integradora", "Proyecto integrador", "Proyecto final del curso", "Tarea", "Grupal", "rubrica_aqui", "Incompleto", "Necesita revisión", ""],
        ["Observaciones", "Fin de la planilla", "", "", "", "", "", "", ""],
    ]


@pytest.fixture
def course_spec_vacio():
    """Retorna un CourseSpec vacío para pruebas."""
    return CourseSpec(nombre="test_course")


@pytest.fixture
def course_spec_con_modulos():
    """Retorna un CourseSpec con algunos módulos y items de prueba."""
    spec = CourseSpec(nombre="test_course", codigo="TEST001")

    item1 = ItemCurso(titulo="Introducción", tipo=TipoItem.PAGINA, orden=1)
    item2 = ItemCurso(titulo="Contenido 1", tipo=TipoItem.VIDEO, orden=2)

    modulo1 = ModuloCurso(numero=1, titulo="Módulo 1", items=[item1, item2])
    spec.modulos.append(modulo1)

    return spec
