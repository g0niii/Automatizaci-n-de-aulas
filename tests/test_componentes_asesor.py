# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from maquetador.build.componentes_asesor import (
    pares_de_tabla, pares_de_texto, extraer_pares, construir_panels,
    construir_flipcards, construir_popover, aplicar_cita,
)


def _soup(html):
    return BeautifulSoup(html, "html.parser")


class TestParesDeTabla:
    def test_celdas_alternadas(self):
        html = ("<table><tr><td><p>Título A</p></td></tr>"
                "<tr><td><p>Contenido A</p></td></tr>"
                "<tr><td><p>Título B</p></td></tr>"
                "<tr><td><p>Contenido B</p></td></tr></table>")
        tabla = _soup(html).find("table")
        pares = pares_de_tabla(tabla)
        assert len(pares) == 2
        assert pares[0][0] == "Título A"
        assert "Contenido A" in pares[0][1]
        assert pares[1][0] == "Título B"

    def test_celda_impar_usa_nbsp(self):
        html = ("<table><tr><td>Solo título</td></tr></table>")
        tabla = _soup(html).find("table")
        # un solo título sin contenido → 0 pares completos
        assert pares_de_tabla(tabla) == []


class TestParesDeTexto:
    def test_nombre_dos_puntos_contenido(self):
        parrafos = _soup(
            "<div><p>Vigor: alto nivel de energía y resistencia.</p>"
            "<p>Dedicación: sentido y entusiasmo en el trabajo.</p></div>"
        ).find_all("p")
        pares = pares_de_texto(parrafos)
        assert len(pares) == 2
        assert pares[0] == ("Vigor", "alto nivel de energía y resistencia.")
        assert pares[1][0] == "Dedicación"

    def test_parrafo_sin_dos_puntos_se_ignora(self):
        parrafos = _soup("<div><p>Un párrafo normal sin estructura.</p></div>").find_all("p")
        assert pares_de_texto(parrafos) == []


class TestExtraerPares:
    def test_menos_de_dos_pares_devuelve_vacio(self):
        el = _soup("<p>Solo: uno</p>").find("p")
        assert extraer_pares(el) == ([], [])

    def test_texto_dos_items(self):
        soup = _soup("<div><p>Primero: uno</p><p>Segundo: dos</p></div>")
        el = soup.find("p")
        pares, consumidos = extraer_pares(el)
        assert len(pares) == 2
        assert len(consumidos) == 2          # ambos párrafos se consumen


class TestConstruirPanels:
    def test_acordeon_estructura_cidilabs(self):
        html = construir_panels([("T1", "<p>C1</p>"), ("T2", "<p>C2</p>")])
        assert "dp-panels-wrapper dp-expander-default" in html
        assert html.count('class="dp-panel-group"') == 2
        assert '<h3 class="dp-panel-heading">T1</h3>' in html
        assert '<div class="dp-panel-content"><p>C1</p></div>' in html

    def test_tabs_variante(self):
        html = construir_panels([("T1", "x"), ("T2", "y")], variante="dp-tabs")
        assert "dp-panels-wrapper dp-tabs" in html


class TestConstruirFlipcards:
    def test_estructura_cidilabs(self):
        html = construir_flipcards([("Frente1", "Dorso1"), ("Frente2", "Dorso2")])
        assert 'class="row justify-content-center"' in html
        assert html.count('class="dp-flip-card"') == 2
        assert '<div class="dp-front-card">' in html
        assert '<div class="dp-back-card">' in html
        assert "<strong>Frente1</strong>" in html
        assert "Dorso1" in html


class TestConstruirPopover:
    def test_trigger_y_content_enlazados(self):
        trigger, content = construir_popover("stakeholders", "Toda parte interesada", 0)
        assert 'class="dp-popover-trigger"' in trigger
        assert 'href="#dpPopup0Content"' in trigger
        assert 'id="dpPopup0"' in trigger
        assert ">stakeholders</a>" in trigger
        assert 'id="dpPopup0Content"' in content
        assert "dp-popover-content dp-popup-content" in content
        assert "Toda parte interesada" in content


class TestAplicarCita:
    def test_agrega_sangria(self):
        el = BeautifulSoup("<p>Una cita textual.</p>", "html.parser").find("p")
        aplicar_cita(el)
        assert "margin-left: 40px" in el.get("style", "")
