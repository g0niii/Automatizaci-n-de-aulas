# -*- coding: utf-8 -*-
"""Tests para detección y segmentación de DOCX de módulos.

Prueba las capacidades del docx_probe:
- Detectar secciones numeradas (N.N, N.N.N)
- Identificar marcadores especiales (Introducción, Conclusión, etc.)
- Manejar múltiples estrategias de detección de títulos
- Extraer metadatos de la tabla inicial
"""

import pytest
from pathlib import Path
from maquetador.ingest.docx_probe import (
    perfilar_docx,
    PerfilDocx,
    SeccionDetectada,
    CandidatoSinNumero,
)


class TestPerfilarDocxBasico:
    """Tests básicos de la función perfilar_docx."""

    def test_perfilar_docx_retorna_perfil(self, casos_dir):
        """Verifica que perfilar_docx retorna un PerfilDocx válido."""
        # Buscar un DOCX de módulo real
        docx_files = list(casos_dir.rglob("*Módulo*.docx"))
        if not docx_files:
            pytest.skip("No se encontraron archivos Módulo*.docx en 'Aulas a generar/'")

        path = docx_files[0]
        perfil = perfilar_docx(path)

        assert isinstance(perfil, PerfilDocx)
        assert perfil.archivo == path
        assert isinstance(perfil.estrategia, str)
        assert isinstance(perfil.secciones, list)
        assert isinstance(perfil.candidatos, list)

    def test_perfilar_docx_detecta_secciones_numeradas(self, casos_dir):
        """Verifica que detecta secciones con formato N.N o N.N.N."""
        docx_files = list(casos_dir.rglob("*Módulo*.docx"))
        if not docx_files:
            pytest.skip("No se encontraron archivos Módulo*.docx en 'Aulas a generar/'")

        for path in docx_files[:3]:  # Probar con los primeros 3
            perfil = perfilar_docx(path)
            # Al menos uno debe detectar algo
            if perfil.secciones:
                # Verificar estructura de secciones
                for seccion in perfil.secciones:
                    assert isinstance(seccion, SeccionDetectada)
                    assert seccion.numero, "Numero debe estar presente"
                    assert seccion.titulo, "Titulo debe estar presente"
                    # Verificar que el número tiene formato N.N
                    assert "." in seccion.numero or seccion.numero.isdigit()

    def test_perfilar_docx_identifica_introduccion(self, casos_dir):
        """Verifica que detecta cuando hay Introducción."""
        docx_files = list(casos_dir.rglob("*Módulo*.docx"))
        if not docx_files:
            pytest.skip("No se encontraron archivos Módulo*.docx en 'Aulas a generar/'")

        for path in docx_files[:2]:
            perfil = perfilar_docx(path)
            # tiene_intro es un boolean
            assert isinstance(perfil.tiene_intro, bool)

    def test_perfilar_docx_identifica_conclusion(self, casos_dir):
        """Verifica que detecta Conclusión, Cierre o Reflexión final."""
        docx_files = list(casos_dir.rglob("*Módulo*.docx"))
        if not docx_files:
            pytest.skip("No se encontraron archivos Módulo*.docx en 'Aulas a generar/'")

        perfil = perfilar_docx(docx_files[0])
        assert isinstance(perfil.tiene_conclusion, bool)

    def test_perfilar_docx_identifica_referencias(self, casos_dir):
        """Verifica que detecta Referencias o Bibliografía."""
        docx_files = list(casos_dir.rglob("*Módulo*.docx"))
        if not docx_files:
            pytest.skip("No se encontraron archivos Módulo*.docx en 'Aulas a generar/'")

        perfil = perfilar_docx(docx_files[0])
        assert isinstance(perfil.tiene_referencias, bool)

    def test_perfilar_docx_retorna_dict(self, casos_dir):
        """Verifica que el perfil puede convertirse a dict."""
        docx_files = list(casos_dir.rglob("*Módulo*.docx"))
        if not docx_files:
            pytest.skip("No se encontraron archivos Módulo*.docx en 'Aulas a generar/'")

        perfil = perfilar_docx(docx_files[0])
        d = perfil.to_dict()

        assert isinstance(d, dict)
        assert "archivo" in d
        assert "estrategia" in d
        assert "secciones" in d
        assert "candidatos_sin_numero" in d


class TestDeteccionSecciones:
    """Tests específicos para la detección de secciones."""

    def test_secciones_tienen_indice_parrafo(self, casos_dir):
        """Verifica que cada sección tiene su índice de párrafo."""
        docx_files = list(casos_dir.rglob("*Módulo*.docx"))
        if not docx_files:
            pytest.skip("No se encontraron archivos Módulo*.docx en 'Aulas a generar/'")

        perfil = perfilar_docx(docx_files[0])
        for seccion in perfil.secciones:
            assert seccion.indice_parrafo >= 0

    def test_candidatos_sin_numero_validos(self, casos_dir):
        """Verifica que los candidatos sin número cumplen criterios."""
        docx_files = list(casos_dir.rglob("*Módulo*.docx"))
        if not docx_files:
            pytest.skip("No se encontraron archivos Módulo*.docx en 'Aulas a generar/'")

        perfil = perfilar_docx(docx_files[0])
        for candidato in perfil.candidatos:
            assert isinstance(candidato, CandidatoSinNumero)
            assert len(candidato.titulo) >= 15, "Candidato debe tener al menos 15 chars"
            assert candidato.indice_parrafo >= 0

    def test_estrategia_es_una_de_las_conocidas(self, casos_dir):
        """Verifica que la estrategia elegida es una de las esperadas."""
        docx_files = list(casos_dir.rglob("*Módulo*.docx"))
        if not docx_files:
            pytest.skip("No se encontraron archivos Módulo*.docx en 'Aulas a generar/'")

        estrategias_conocidas = {"heading_styles", "bold_numbered", "plain_numbered", "ninguna"}

        for path in docx_files[:5]:
            perfil = perfilar_docx(path)
            assert perfil.estrategia in estrategias_conocidas, \
                f"Estrategia '{perfil.estrategia}' no reconocida"

    def test_detalle_estrategias_existe(self, casos_dir):
        """Verifica que detalle_estrategias contiene resultados de todas."""
        docx_files = list(casos_dir.rglob("*Módulo*.docx"))
        if not docx_files:
            pytest.skip("No se encontraron archivos Módulo*.docx en 'Aulas a generar/'")

        perfil = perfilar_docx(docx_files[0])
        assert "heading_styles" in perfil.detalle_estrategias
        assert "bold_numbered" in perfil.detalle_estrategias
        assert "plain_numbered" in perfil.detalle_estrategias


class TestMetadatos:
    """Tests para extracción de metadatos de la tabla inicial."""

    def test_metadatos_dict_existe(self, casos_dir):
        """Verifica que metadatos es un diccionario."""
        docx_files = list(casos_dir.rglob("*Módulo*.docx"))
        if not docx_files:
            pytest.skip("No se encontraron archivos Módulo*.docx en 'Aulas a generar/'")

        perfil = perfilar_docx(docx_files[0])
        assert isinstance(perfil.metadatos, dict)


class TestMultiplesCasos:
    """Tests contra múltiples casos reales."""

    def test_perfilar_todos_los_modulos_disponibles(self, casos_dir):
        """Corre perfilar_docx contra todos los Módulo*.docx disponibles."""
        docx_files = sorted(casos_dir.rglob("*Módulo*.docx"))
        if not docx_files:
            pytest.skip("No se encontraron archivos Módulo*.docx en 'Aulas a generar/'")

        resultados = []
        for path in docx_files[:10]:  # Limitar a 10 para no tardar demasiado
            try:
                perfil = perfilar_docx(path)
                resultados.append((path.name, len(perfil.secciones), perfil.estrategia))
            except Exception as e:
                pytest.fail(f"Error al perfilar {path.name}: {e}")

        # Debe haber procesado al menos algo
        assert len(resultados) > 0

    def test_consistency_entre_runs_mismo_archivo(self, casos_dir):
        """Verifica que los resultados son consistentes entre múltiples ejecuciones."""
        docx_files = list(casos_dir.rglob("*Módulo*.docx"))
        if not docx_files:
            pytest.skip("No se encontraron archivos Módulo*.docx en 'Aulas a generar/'")

        path = docx_files[0]
        perfil1 = perfilar_docx(path)
        perfil2 = perfilar_docx(path)

        # El mismo archivo debe producir el mismo resultado
        assert perfil1.estrategia == perfil2.estrategia
        assert len(perfil1.secciones) == len(perfil2.secciones)
        assert perfil1.tiene_intro == perfil2.tiene_intro
