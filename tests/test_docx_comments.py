# -*- coding: utf-8 -*-
from maquetador.ingest.docx_comments import _clasificar


class TestClasificarComponentes:
    def test_tabs(self):
        assert _clasificar("Maquetación: tabs al costado") == "tabs"
        assert _clasificar("hacer pestañas con esto") == "tabs"

    def test_expander(self):
        assert _clasificar("Maquetación: expander") == "expander"
        assert _clasificar("esto es un expandible") == "expander"

    def test_tooltip(self):
        assert _clasificar("que al hacer clic aparezca: Gestión por objetivos") == "tooltip"
        assert _clasificar("Maquetación: tooltip --> User Stories") == "tooltip"

    def test_cita(self):
        assert _clasificar("Maquetación: esto es una cita") == "cita"
        assert _clasificar("es una cita") == "cita"

    def test_acordeon_flip_siguen(self):
        assert _clasificar("Maquetación: acordeón") == "acordeon"
        assert _clasificar("tarjetas que se dan vuelta") == "flip_card"

    def test_regresion_tooltip_aparezca_clic(self):
        """Regresión: 'aparezca' sin clic debe auto-aplicar (no ser tooltip)."""
        # "que aparezca como recuadro" → recuadro_simple (no tooltip)
        assert _clasificar("que aparezca como recuadro") == "recuadro_simple"
        # "que aparezca el video de la clase" → video (no tooltip)
        assert _clasificar("que aparezca el video de la clase") == "video"
        # "al hacer clic que aparezca la definicion" → tooltip (CON clic)
        assert _clasificar("al hacer clic que aparezca la definicion") == "tooltip"

    def test_dead_code_acordeon_simple_eliminado(self):
        """Dead code: 'acordeon-simple' era inalcanzable (acordeon lo captura)."""
        # 'acordeon-simple' debe ser capturado por la rama 'acordeon', no 'expander'
        assert _clasificar("acordeon-simple") == "acordeon"
        assert _clasificar("expander") == "expander"
