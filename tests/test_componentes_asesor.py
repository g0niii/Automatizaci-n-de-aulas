# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from maquetador.build.componentes_asesor import (
    pares_de_tabla, pares_de_texto, extraer_pares,
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
