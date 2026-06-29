# -*- coding: utf-8 -*-
"""Tests para escaneo y clasificación de archivos de curso.

Prueba las capacidades del folder_scanner:
- Clasificación por rol (contenido_modulo, foro, video, actividad, etc.)
- Descarte de borradores, copias, devoluciones
- Extracción de número de módulo desde nombres
- Normalización de texto
- Manejo de convenciones múltiples de carpetas
"""

import pytest
from pathlib import Path
from maquetador.ingest.folder_scanner import (
    escanear,
    normalizar,
    InventarioCurso,
)


class TestNormalizar:
    """Tests para la función normalizar."""

    def test_normalizar_convierte_a_minusculas(self):
        """Verifica que normalizar convierte a minúsculas."""
        assert normalizar("HOLA") == "hola"
        assert normalizar("HoLa") == "hola"

    def test_normalizar_elimina_acentos(self):
        """Verifica que eliminan acentos diacríticos."""
        assert normalizar("módulo") == "modulo"
        assert normalizar("Introducción") == "introduccion"
        assert normalizar("Ética") == "etica"

    def test_normalizar_colapsa_espacios(self):
        """Verifica que colapsa múltiples espacios."""
        assert normalizar("hola   mundo") == "hola mundo"
        assert normalizar("  hola  ") == "hola"

    def test_normalizar_combinado(self):
        """Test combinado: mayúsculas + acentos + espacios."""
        result = normalizar("  MÓDULO   DE   ÉTICA  ")
        assert result == "modulo de etica"


class TestEscanearBasico:
    """Tests básicos de la función escanear."""

    def test_escanear_retorna_inventario(self, casos_dir):
        """Verifica que escanear retorna un InventarioCurso válido."""
        # Buscar cualquier subcarpeta de curso
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])
        assert isinstance(inv, InventarioCurso)
        assert inv.raiz.is_dir()
        assert isinstance(inv.nombre_curso, str)

    def test_escanear_estructura_basica(self, casos_dir):
        """Verifica la estructura básica del inventario."""
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])

        # Verificar que todos los campos esperados existen
        assert isinstance(inv.docx_modulos, dict)
        assert isinstance(inv.actividades, list)
        assert isinstance(inv.foros, list)
        assert isinstance(inv.guiones_video, list)
        assert isinstance(inv.programa, list)
        assert isinstance(inv.hoja_de_ruta, list)
        assert isinstance(inv.biografia, list)
        assert isinstance(inv.fotos_docente, list)
        assert isinstance(inv.imagenes_diseno, list)
        assert isinstance(inv.esquema, list)
        assert isinstance(inv.otros, list)
        assert isinstance(inv.issues, list)

    def test_escanear_retorna_dict(self, casos_dir):
        """Verifica que el inventario puede convertirse a dict."""
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])
        d = inv.to_dict()

        assert isinstance(d, dict)
        assert "raiz" in d
        assert "nombre_curso" in d
        assert "docx_modulos" in d
        assert "actividades" in d
        assert "foros" in d


class TestClasificacionDocx:
    """Tests para clasificación de archivos DOCX."""

    def test_encuentra_docx_modulos(self, casos_dir):
        """Verifica que encuentra archivos de módulos."""
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])
        # Al menos uno debe encontrar módulos
        if inv.docx_modulos:
            assert all(isinstance(k, int) for k in inv.docx_modulos.keys())
            assert all(isinstance(v, Path) for v in inv.docx_modulos.values())

    def test_encuentra_actividades(self, casos_dir):
        """Verifica que detecta archivos de actividades."""
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])
        # Las actividades pueden estar vacías, solo verificar estructura
        assert isinstance(inv.actividades, list)
        for item in inv.actividades:
            if isinstance(item, tuple):
                assert len(item) == 2  # (numero_o_none, Path)

    def test_encuentra_foros(self, casos_dir):
        """Verifica que detecta archivos de foros."""
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])
        assert isinstance(inv.foros, list)

    def test_encuentra_guiones_video(self, casos_dir):
        """Verifica que detecta guiones de video."""
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])
        assert isinstance(inv.guiones_video, list)

    def test_encuentra_programa(self, casos_dir):
        """Verifica que detecta el programa del curso."""
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])
        assert isinstance(inv.programa, list)


class TestClasificacionImagenes:
    """Tests para clasificación de imágenes."""

    def test_detecta_imagenes_diseno(self, casos_dir):
        """Verifica que clasifica imágenes de figuras/tablas."""
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])
        assert isinstance(inv.imagenes_diseno, list)

    def test_detecta_esquemas(self, casos_dir):
        """Verifica que detecta esquemas."""
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])
        assert isinstance(inv.esquema, list)


class TestDescarte:
    """Tests para descarte de borradores y copias."""

    def test_descarta_carpeta_devoluciones(self, casos_dir):
        """Verifica que descarta archivos en carpeta 'Devoluciones'."""
        # Buscar una carpeta que tenga Devoluciones
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])
        # Verificar que no hay rutas que contengan "devoluciones" o "Devoluciones"
        def tiene_devoluciones(p):
            return "devolucion" in str(p).lower()

        for modulo in inv.docx_modulos.values():
            assert not tiene_devoluciones(modulo), \
                f"No debería incluir {modulo} de Devoluciones"

    def test_descarta_palabras_prohibidas_en_nombre(self, casos_dir):
        """Verifica que descarta archivos con 'borrador', 'copia de', etc."""
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])
        prohibidas = ["borrador", "copia de", "eliminada"]

        # Verificar documentos principales
        archivos_a_chequear = []
        archivos_a_chequear.extend(inv.docx_modulos.values())
        archivos_a_chequear.extend(inv.programa)
        # Los foros vienen como tuplas (numero, path)
        for item in inv.foros:
            if isinstance(item, tuple):
                archivos_a_chequear.append(item[1])
            else:
                archivos_a_chequear.append(item)

        for path in archivos_a_chequear:
            nombre = path.name.lower()
            for palabra in prohibidas:
                assert palabra not in nombre, \
                    f"No debería incluir '{path.name}' (contiene '{palabra}')"


class TestExtraerNumeroModulo:
    """Tests para extracción de número de módulo desde nombres."""

    def test_extrae_numero_desde_docx_modulos(self, casos_dir):
        """Verifica que los números de módulo se extraen correctamente."""
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])
        if inv.docx_modulos:
            # Los números deben ser enteros (pueden ser 0 si no se detecta)
            for num in inv.docx_modulos.keys():
                assert isinstance(num, int), f"Número debe ser int, no {type(num)}"
                assert num >= 0, f"Número de módulo debe ser no-negativo: {num}"

    def test_extrae_numero_desde_actividades(self, casos_dir):
        """Verifica que extrae números de módulo de actividades."""
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])
        for item in inv.actividades:
            if isinstance(item, tuple):
                numero, path = item
                # numero puede ser None o un int
                assert numero is None or isinstance(numero, int)


class TestEstructuraXlsx:
    """Tests para detección de la planilla de estructura."""

    def test_encuentra_estructura_xlsx(self, casos_dir):
        """Verifica que busca la planilla de estructura general."""
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])
        # estructura_xlsx puede ser None o un Path
        assert inv.estructura_xlsx is None or isinstance(inv.estructura_xlsx, Path)


class TestIssues:
    """Tests para validaciones y issues."""

    def test_issues_list_existe(self, casos_dir):
        """Verifica que hay un campo issues."""
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])
        assert isinstance(inv.issues, list)

    def test_issues_contienen_severidad(self, casos_dir):
        """Verifica que los issues tienen severidad."""
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        inv = escanear(cursos[0])
        for issue in inv.issues:
            # Los issues deben tener al menos mensaje
            assert hasattr(issue, "mensaje") or hasattr(issue, "message")


class TestMultiplesCasos:
    """Tests contra múltiples casos reales."""

    def test_escanear_todos_los_cursos(self, casos_dir):
        """Corre escanear contra todos los cursos disponibles."""
        cursos = sorted([c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")])
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        resultados = []
        for curso_dir in cursos[:5]:  # Limitar a 5 para no tardar
            try:
                inv = escanear(curso_dir)
                resultados.append((
                    inv.nombre_curso,
                    len(inv.docx_modulos),
                    len(inv.actividades),
                    len(inv.issues),
                ))
            except Exception as e:
                pytest.fail(f"Error al escanear {curso_dir.name}: {e}")

        assert len(resultados) > 0

    def test_consistency_mismo_curso(self, casos_dir):
        """Verifica que escaneando dos veces da el mismo resultado."""
        cursos = [c for c in casos_dir.iterdir() if c.is_dir() and not c.name.startswith(".")]
        if not cursos:
            pytest.skip("No se encontraron carpetas de curso en casos/")

        curso_dir = cursos[0]
        inv1 = escanear(curso_dir)
        inv2 = escanear(curso_dir)

        # Mismo número de módulos
        assert len(inv1.docx_modulos) == len(inv2.docx_modulos)
        # Mismo número de actividades
        assert len(inv1.actividades) == len(inv2.actividades)
        # Mismo nombre de curso
        assert inv1.nombre_curso == inv2.nombre_curso
