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
