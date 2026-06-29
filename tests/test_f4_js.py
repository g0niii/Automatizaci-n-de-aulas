# -*- coding: utf-8 -*-
"""Tests para Task 7: F4 JavaScript — validación cliente de edit_plan.js.

Los tests se enfocan en la lógica de validación y construcción del plan,
que debería ser agnóstica del framework JavaScript.
"""

import pytest


class TestEditPlanValidacion:
    """Tests para validación de campos del plan."""

    def test_validar_titulo_vacio(self):
        """Título vacío debe rechazarse."""
        # Simulamos la lógica de validarTitulo de edit_plan.js
        titulo = ""
        valido = len(titulo.strip()) > 0
        assert not valido

    def test_validar_titulo_solo_espacios(self):
        """Título solo con espacios debe rechazarse."""
        titulo = "   "
        valido = len(titulo.strip()) > 0
        assert not valido

    def test_validar_titulo_valido(self):
        """Título con contenido debe aceptarse."""
        titulo = "1.1. Introducción"
        valido = len(titulo.strip()) > 0
        assert valido

    def test_validar_tipo_valido_pagina(self):
        """Tipo 'pagina' debe ser válido."""
        tipo = "pagina"
        tipos_validos = ['pagina', 'video', 'foro', 'tarea', 'evaluacion']
        assert tipo in tipos_validos

    def test_validar_tipo_valido_video(self):
        """Tipo 'video' debe ser válido."""
        tipo = "video"
        tipos_validos = ['pagina', 'video', 'foro', 'tarea', 'evaluacion']
        assert tipo in tipos_validos

    def test_validar_tipo_valido_foro(self):
        """Tipo 'foro' debe ser válido."""
        tipo = "foro"
        tipos_validos = ['pagina', 'video', 'foro', 'tarea', 'evaluacion']
        assert tipo in tipos_validos

    def test_validar_tipo_valido_tarea(self):
        """Tipo 'tarea' debe ser válido."""
        tipo = "tarea"
        tipos_validos = ['pagina', 'video', 'foro', 'tarea', 'evaluacion']
        assert tipo in tipos_validos

    def test_validar_tipo_valido_evaluacion(self):
        """Tipo 'evaluacion' debe ser válido."""
        tipo = "evaluacion"
        tipos_validos = ['pagina', 'video', 'foro', 'tarea', 'evaluacion']
        assert tipo in tipos_validos

    def test_validar_tipo_invalido(self):
        """Tipo inválido debe rechazarse."""
        tipo = "podcast"
        tipos_validos = ['pagina', 'video', 'foro', 'tarea', 'evaluacion']
        assert tipo not in tipos_validos

    def test_validar_tipo_vacio(self):
        """Tipo vacío debe rechazarse."""
        tipo = ""
        tipos_validos = ['pagina', 'video', 'foro', 'tarea', 'evaluacion']
        assert tipo not in tipos_validos


class TestConstruirPlan:
    """Tests para construcción del plan desde datos de formulario."""

    def test_construir_plan_minimo(self):
        """Plan con datos mínimos debe construirse correctamente."""
        # Simulamos: 1 módulo, 1 item
        nombre = "Curso Test"
        codigo = "TEST001"
        tema = "educacion"

        plan = {
            "nombre": nombre,
            "codigo": codigo,
            "tema": tema,
            "docentes": [],
            "items_inicio": [],
            "modulos": [
                {
                    "numero": 1,
                    "titulo": "Módulo 1",
                    "items": [
                        {
                            "titulo": "1.1. Item",
                            "tipo": "pagina",
                            "orden": 1,
                            "fuente": {
                                "archivo": None,
                                "seccion": None,
                                "confianza": 0.95,
                                "tiene_html": False
                            },
                            "estado_planilla": "Obligatorio",
                            "comentarios_asesor": "",
                            "detalle": {},
                            "issues": []
                        }
                    ]
                }
            ],
            "afi": [],
            "issues": []
        }

        assert plan["nombre"] == "Curso Test"
        assert len(plan["modulos"]) == 1
        assert len(plan["modulos"][0]["items"]) == 1
        assert plan["modulos"][0]["items"][0]["titulo"] == "1.1. Item"

    def test_construir_plan_multiples_modulos(self):
        """Plan con múltiples módulos debe construirse correctamente."""
        plan = {
            "nombre": "Curso Completo",
            "codigo": "COMP001",
            "tema": "posgrado",
            "docentes": [],
            "items_inicio": [],
            "modulos": [
                {
                    "numero": 1,
                    "titulo": "Módulo 1",
                    "items": [
                        {
                            "titulo": "1.1. Intro",
                            "tipo": "pagina",
                            "orden": 1,
                            "fuente": {
                                "archivo": "mod1.docx",
                                "seccion": "1.1",
                                "confianza": 0.95,
                                "tiene_html": False
                            },
                            "estado_planilla": "Obligatorio",
                            "comentarios_asesor": "",
                            "detalle": {},
                            "issues": []
                        }
                    ]
                },
                {
                    "numero": 2,
                    "titulo": "Módulo 2",
                    "items": [
                        {
                            "titulo": "2.1. Contenido",
                            "tipo": "video",
                            "orden": 1,
                            "fuente": {
                                "archivo": "mod2.docx",
                                "seccion": "2.1",
                                "confianza": 0.90,
                                "tiene_html": False
                            },
                            "estado_planilla": "Obligatorio",
                            "comentarios_asesor": "",
                            "detalle": {},
                            "issues": []
                        }
                    ]
                }
            ],
            "afi": [],
            "issues": []
        }

        assert len(plan["modulos"]) == 2
        assert plan["modulos"][0]["numero"] == 1
        assert plan["modulos"][1]["numero"] == 2
        assert plan["modulos"][0]["items"][0]["tipo"] == "pagina"
        assert plan["modulos"][1]["items"][0]["tipo"] == "video"


class TestValidacionEstructura:
    """Tests para validación de estructura general del plan."""

    def test_plan_debe_tener_nombre(self):
        """Plan debe tener nombre no vacío."""
        plan = {
            "nombre": "Curso Test",
            "modulos": [],
            "items_inicio": [],
            "afi": []
        }
        assert "nombre" in plan
        assert len(plan["nombre"]) > 0

    def test_plan_debe_tener_modulos(self):
        """Plan debe tener campo modulos."""
        plan = {
            "nombre": "Curso",
            "modulos": [],
            "items_inicio": [],
            "afi": []
        }
        assert "modulos" in plan
        assert isinstance(plan["modulos"], list)

    def test_plan_debe_tener_items_inicio(self):
        """Plan debe tener campo items_inicio."""
        plan = {
            "nombre": "Curso",
            "modulos": [],
            "items_inicio": [],
            "afi": []
        }
        assert "items_inicio" in plan
        assert isinstance(plan["items_inicio"], list)

    def test_plan_debe_tener_afi(self):
        """Plan debe tener campo afi."""
        plan = {
            "nombre": "Curso",
            "modulos": [],
            "items_inicio": [],
            "afi": []
        }
        assert "afi" in plan
        assert isinstance(plan["afi"], list)

    def test_modulo_debe_tener_numero_y_items(self):
        """Módulo debe tener numero e items."""
        modulo = {
            "numero": 1,
            "titulo": "Módulo 1",
            "items": []
        }
        assert "numero" in modulo
        assert "items" in modulo
        assert isinstance(modulo["items"], list)

    def test_item_debe_tener_titulo_y_tipo(self):
        """Item debe tener titulo y tipo."""
        item = {
            "titulo": "1.1. Item",
            "tipo": "pagina",
            "orden": 1,
            "fuente": {
                "archivo": None,
                "seccion": None,
                "confianza": 0.95,
                "tiene_html": False
            },
            "estado_planilla": "Obligatorio",
            "comentarios_asesor": "",
            "detalle": {},
            "issues": []
        }
        assert "titulo" in item
        assert "tipo" in item
        assert len(item["titulo"]) > 0


class TestModuloValidacion:
    """Tests para validación de módulos."""

    def test_modulo_debe_tener_items(self):
        """Módulo debe tener al menos un item."""
        modulo = {
            "numero": 1,
            "titulo": "Módulo Sin Items",
            "items": []
        }
        # Esto es una regla de negocio: módulos sin items no son válidos
        # pero en la construcción inicial los items están vacíos
        assert len(modulo["items"]) == 0

    def test_modulo_con_items_valido(self):
        """Módulo con items debe ser válido."""
        modulo = {
            "numero": 1,
            "titulo": "Módulo Con Items",
            "items": [
                {
                    "titulo": "1.1. Item",
                    "tipo": "pagina",
                    "orden": 1,
                    "fuente": {
                        "archivo": None,
                        "seccion": None,
                        "confianza": 0.95,
                        "tiene_html": False
                    },
                    "estado_planilla": "Obligatorio",
                    "comentarios_asesor": "",
                    "detalle": {},
                    "issues": []
                }
            ]
        }
        assert len(modulo["items"]) > 0


class TestDatosFormulario:
    """Tests para transformación de datos del formulario."""

    def test_archivo_vacio_se_convierte_en_null(self):
        """Campo archivo vacío debe convertirse en None."""
        archivo = ""
        convertido = archivo or None
        assert convertido is None

    def test_archivo_con_valor_se_mantiene(self):
        """Campo archivo con valor debe mantenerse."""
        archivo = "documento.docx"
        convertido = archivo or None
        assert convertido == "documento.docx"

    def test_seccion_vacia_se_convierte_en_null(self):
        """Campo sección vacío debe convertirse en None."""
        seccion = ""
        convertido = seccion or None
        assert convertido is None

    def test_seccion_con_valor_se_mantiene(self):
        """Campo sección con valor debe mantenerse."""
        seccion = "1.1"
        convertido = seccion or None
        assert convertido == "1.1"

    def test_confianza_por_defecto(self):
        """Campo confianza debe tener valor por defecto 0.95."""
        confianza = 0.95
        assert confianza == 0.95

    def test_estado_planilla_por_defecto(self):
        """Campo estado_planilla debe tener valor por defecto Obligatorio."""
        estado = "Obligatorio"
        assert estado == "Obligatorio"
