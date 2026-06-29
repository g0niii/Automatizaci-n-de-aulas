# -*- coding: utf-8 -*-
"""Tests para Task 5: F4 API — guardar cambios del plan."""

import copy
import pytest
from maquetador.web.api import guardar_cambios_plan


@pytest.fixture
def plan_base():
    """Plan base válido con 1 módulo y 2 items."""
    return {
        "nombre": "Curso Test",
        "codigo": "TEST001",
        "tema": "educacion",
        "docentes": [],
        "items_inicio": [],
        "modulos": [
            {
                "numero": 1,
                "titulo": "Módulo 1",
                "items": [
                    {
                        "titulo": "1.1. Introducción",
                        "tipo": "pagina",
                        "orden": 1,
                        "fuente": {
                            "archivo": "modulo1.docx",
                            "seccion": "1.1",
                            "confianza": 0.95,
                            "tiene_html": False
                        },
                        "estado_planilla": "Obligatorio",
                        "comentarios_asesor": "",
                        "detalle": {},
                        "issues": []
                    },
                    {
                        "titulo": "1.2. Contenido",
                        "tipo": "pagina",
                        "orden": 2,
                        "fuente": {
                            "archivo": "modulo1.docx",
                            "seccion": "1.2",
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


class TestGuardarCambiosBasico:
    """Tests para cambios básicos en el plan."""

    def test_guardar_cambios_plan_sin_cambios(self, plan_base):
        """Plan idéntico debe retornar exito=True, cambios=[]."""
        # Arrange
        original = plan_base
        editado = copy.deepcopy(plan_base)

        # Act
        resultado = guardar_cambios_plan(original, editado)

        # Assert
        assert resultado["exito"] is True
        assert resultado["errores"] == []
        assert resultado["cambios"] == []

    def test_guardar_cambios_plan_reasignar_fuente(self, plan_base):
        """Cambiar archivo/sección de una fuente se detecta."""
        # Arrange
        original = plan_base
        editado = copy.deepcopy(plan_base)
        # Cambiar profundamente: módulos[0].items[0].fuente.archivo
        editado["modulos"][0]["items"][0]["fuente"]["archivo"] = "modulo1_nuevo.docx"

        # Act
        resultado = guardar_cambios_plan(original, editado)

        # Assert
        assert resultado["exito"] is True
        assert resultado["errores"] == []
        assert len(resultado["cambios"]) > 0
        # Buscar el cambio específico
        cambios_ruta = [c for c in resultado["cambios"]
                        if "modulos[0].items[0].fuente.archivo" in c["ruta"]]
        assert len(cambios_ruta) > 0
        assert cambios_ruta[0]["anterior"] == "modulo1.docx"
        assert cambios_ruta[0]["nuevo"] == "modulo1_nuevo.docx"

    def test_guardar_cambios_plan_cambiar_tipo_item(self, plan_base):
        """Cambiar tipo de item se detecta."""
        # Arrange
        original = plan_base
        editado = copy.deepcopy(plan_base)
        editado["modulos"][0]["items"][1]["tipo"] = "foro"

        # Act
        resultado = guardar_cambios_plan(original, editado)

        # Assert
        assert resultado["exito"] is True
        assert resultado["errores"] == []
        assert len(resultado["cambios"]) > 0
        cambios_tipo = [c for c in resultado["cambios"]
                        if "modulos[0].items[1].tipo" in c["ruta"]]
        assert len(cambios_tipo) > 0
        assert cambios_tipo[0]["anterior"] == "pagina"
        assert cambios_tipo[0]["nuevo"] == "foro"

    def test_guardar_cambios_plan_cambiar_titulo(self, plan_base):
        """Cambiar título de item se detecta."""
        # Arrange
        original = plan_base
        editado = copy.deepcopy(plan_base)
        editado["modulos"][0]["items"][0]["titulo"] = "1.1. Introducción MODIFICADA"

        # Act
        resultado = guardar_cambios_plan(original, editado)

        # Assert
        assert resultado["exito"] is True
        assert resultado["errores"] == []
        cambios_titulo = [c for c in resultado["cambios"]
                          if "titulo" in c["ruta"]]
        assert any("1.1. Introducci" in str(c["nuevo"]) and "MODIFICADA" in str(c["nuevo"])
                  for c in cambios_titulo)


class TestValidacionEstructura:
    """Tests para validación de estructura del plan."""

    def test_guardar_cambios_plan_json_invalido_no_dict(self):
        """Plan editado que no es dict retorna error."""
        # Arrange
        original = {"nombre": "Test", "modulos": [], "items_inicio": [], "afi": []}
        editado = "no es un dict"

        # Act
        resultado = guardar_cambios_plan(original, editado)

        # Assert
        assert resultado["exito"] is False
        assert len(resultado["errores"]) > 0
        assert "diccionario" in resultado["errores"][0].lower()
        assert resultado["cambios"] == []

    def test_guardar_cambios_plan_json_invalido_faltan_claves(self, plan_base):
        """Plan editado sin claves requeridas retorna error."""
        # Arrange
        original = plan_base
        editado = {"nombre": "Incompleto", "modulos": []}
        # Falta items_inicio y afi

        # Act
        resultado = guardar_cambios_plan(original, editado)

        # Assert
        assert resultado["exito"] is False
        assert len(resultado["errores"]) > 0
        assert "items_inicio" in " ".join(resultado["errores"]) or \
               "afi" in " ".join(resultado["errores"])

    def test_guardar_cambios_plan_json_invalido_modulos_no_lista(self, plan_base):
        """Plan editado con modulos no como lista retorna error."""
        # Arrange
        original = plan_base
        editado = copy.deepcopy(plan_base)
        editado["modulos"] = {"0": "no es lista"}

        # Act
        resultado = guardar_cambios_plan(original, editado)

        # Assert
        assert resultado["exito"] is False
        assert any("modulos" in err.lower() and "lista" in err.lower()
                   for err in resultado["errores"])

    def test_guardar_cambios_plan_json_invalido_item_sin_titulo(self, plan_base):
        """Item sin título retorna error."""
        # Arrange
        original = plan_base
        editado = copy.deepcopy(plan_base)
        editado["modulos"][0]["items"][0] = {"tipo": "pagina"}
        # Falta titulo

        # Act
        resultado = guardar_cambios_plan(original, editado)

        # Assert
        assert resultado["exito"] is False
        assert any("titulo" in err.lower() for err in resultado["errores"])


class TestCambiosComplejos:
    """Tests para cambios más complejos."""

    def test_guardar_cambios_plan_agregar_item(self, plan_base):
        """Agregar un item nuevo se detecta."""
        # Arrange
        original = plan_base
        editado = copy.deepcopy(plan_base)
        nuevo_item = {
            "titulo": "1.3. Nuevo",
            "tipo": "pagina",
            "orden": 3,
            "fuente": {"archivo": None, "seccion": None,
                      "confianza": 0.0, "tiene_html": False},
            "estado_planilla": "",
            "comentarios_asesor": "",
            "detalle": {},
            "issues": []
        }
        editado["modulos"][0]["items"].append(nuevo_item)

        # Act
        resultado = guardar_cambios_plan(original, editado)

        # Assert
        assert resultado["exito"] is True
        assert len(resultado["cambios"]) > 0
        # Cambio de length debe estar presente
        cambios_length = [c for c in resultado["cambios"]
                         if "length" in c["ruta"]]
        assert any(c["anterior"] == 2 and c["nuevo"] == 3
                  for c in cambios_length)

    def test_guardar_cambios_plan_cambiar_docentes(self, plan_base):
        """Cambiar lista de docentes se detecta."""
        # Arrange
        original = plan_base
        editado = copy.deepcopy(plan_base)
        editado["docentes"] = [
            {"nombre": "Dr. García", "foto": "garcia.jpg", "bio": "..."}
        ]

        # Act
        resultado = guardar_cambios_plan(original, editado)

        # Assert
        assert resultado["exito"] is True
        assert len(resultado["cambios"]) > 0
        cambios_docentes = [c for c in resultado["cambios"]
                           if "docentes" in c["ruta"]]
        assert len(cambios_docentes) > 0

    def test_guardar_cambios_plan_cambiar_tema(self, plan_base):
        """Cambiar tema (aula base) se detecta."""
        # Arrange
        original = plan_base
        editado = copy.deepcopy(plan_base)
        editado["tema"] = "posgrado"

        # Act
        resultado = guardar_cambios_plan(original, editado)

        # Assert
        assert resultado["exito"] is True
        cambios_tema = [c for c in resultado["cambios"]
                       if c["ruta"] == "tema"]
        assert len(cambios_tema) == 1
        assert cambios_tema[0]["anterior"] == "educacion"
        assert cambios_tema[0]["nuevo"] == "posgrado"

    def test_guardar_cambios_plan_agregar_modulo(self, plan_base):
        """Agregar módulo nuevo se detecta."""
        # Arrange
        original = plan_base
        editado = copy.deepcopy(plan_base)
        nuevo_modulo = {
            "numero": 2,
            "titulo": "Módulo 2",
            "items": []
        }
        editado["modulos"].append(nuevo_modulo)

        # Act
        resultado = guardar_cambios_plan(original, editado)

        # Assert
        assert resultado["exito"] is True
        cambios_length = [c for c in resultado["cambios"]
                         if "modulos" in c["ruta"] and "length" in c["ruta"]]
        assert any(c["anterior"] == 1 and c["nuevo"] == 2
                  for c in cambios_length)
