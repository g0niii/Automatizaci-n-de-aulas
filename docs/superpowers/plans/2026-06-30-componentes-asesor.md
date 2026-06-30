# Auto-construcción de componentes de maquetación — Plan de Implementación

> **Para trabajadores autónomos:** REQUERIDO: Usar superpowers:subagent-driven-development (recomendado) o superpowers:executing-plans para implementar tarea por tarea. Los pasos usan checkbox (`- [ ]`).

**Goal:** El sistema arma solo los componentes que pide el asesor en los comentarios del DOCX (cita, tooltip, acordeón, tabs, expander, flip card), con HTML CidiLabs real; lo que no puede armar con confianza sigue saliendo como aviso (igual que hoy).

**Architecture:** Un módulo nuevo `componentes_asesor.py` con un extractor de pares unificado (tabla alternada o texto "Nombre: contenido") y builders que emiten el HTML CidiLabs exacto. El cableado va en `aplicar_comentarios()` de `docx_comments.py`: cada acción intenta construir y marca `_aplicado=True` solo si lo logra. El fallback es automático: `segmenter.py` ya filtra los no-aplicados como avisos.

**Tech Stack:** Python 3, BeautifulSoup4, pytest. Sin dependencias nuevas.

## Global Constraints

- HTML de salida = clases CidiLabs reales del aula modelo (verbatim, ver spec):
  - Acordeón/expander: `dp-panels-wrapper dp-expander-default dp-panel-color-dp-secondary dp-panel-active-color-dp-primary`
  - Tabs: `dp-panels-wrapper dp-tabs dp-panel-color-dp-secondary dp-panel-active-color-dp-primary`
  - Paneles: `dp-panel-group` > `h3.dp-panel-heading` + `div.dp-panel-content`
  - Flip card: `row justify-content-center` > `dp-flip-card` > `dp-flip-card-inner` > `dp-front-card`/`dp-back-card`
  - Popover: `a.dp-popover-trigger` (href `#dpPopup{N}Content`, id `dpPopup{N}`) + `div.dp-popover-content.dp-popup-content` (id `dpPopup{N}Content`)
  - Cita: sangría `margin-left: 40px` en el párrafo (sin caja)
- Best-effort con fallback seguro: construir solo si hay ≥2 pares; si no, dejar como hoy (no marcar `_aplicado`).
- TDD, commits frecuentes. Tests con HTML real.

---

## Estructura de archivos

**Crear:**
- `maquetador/build/componentes_asesor.py` — extractor de pares + builders CidiLabs
- `tests/test_componentes_asesor.py` — tests por unidad

**Modificar:**
- `maquetador/ingest/docx_comments.py` — `_clasificar()` (nuevas acciones) + `aplicar_comentarios()` (cableado)

**No tocar (el fallback ya funciona):**
- `maquetador/extract/segmenter.py` — ya filtra `comentarios_pendientes`
- `maquetador/extract/extractor.py` — ya emite avisos de los no-aplicados

---

### Task 1: Clasificar las nuevas acciones de componentes

**Files:**
- Modify: `maquetador/ingest/docx_comments.py` (función `_clasificar`, ~líneas 36-70)
- Test: `tests/test_docx_comments.py`

**Interfaces:**
- Produces: `_clasificar(instruccion: str) -> str | None` ahora devuelve también `"tabs"`, `"expander"`, `"tooltip"`, `"cita"` (ya devuelve `"acordeon"`, `"flip_card"`).

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/test_docx_comments.py`:

```python
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
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `python -m pytest tests/test_docx_comments.py -q`
Expected: FAIL (tabs/expander/tooltip/cita devuelven None hoy).

- [ ] **Step 3: Implementar la clasificación**

En `maquetador/ingest/docx_comments.py`, dentro de `_clasificar`, ANTES del bloque `if "acordeon" in n:` agregar tabs; y antes del return final agregar tooltip/cita/expander. Resultado del cuerpo (reemplazar desde `if "subtitulo" in n:` hasta el `return None` final):

```python
    if "subtitulo" in n:
        return "subtitulo"
    if "acordeon" in n:
        return "acordeon"
    if any(k in n for k in ("tab ", "tabs", "pestana", "pestanas", "solapa")):
        return "tabs"
    if any(k in n for k in ("expander", "expandible", "expandir", "acordeon-simple")):
        return "expander"
    if any(k in n for k in ("flip card", "flipcard", "flip-card", "tarjeta",
                            "se dan vuelta", "se da vuelta")):
        return "flip_card"
    if any(k in n for k in ("tooltip", "al hacer clic", "al hacer click",
                            "emerja", "emerge", "aparezca", "popover", "globo")):
        return "tooltip"
    if any(k in n for k in ("es una cita", "esto es una cita", "es cita", "como cita")):
        return "cita"
    if any(k in n for k in ("quitar", "sacar", "eliminar", "borrar")):
        return "quitar"
    if "recuadro" in n or "resalta" in n:
        return "recuadro_simple"
    if "lectura" in n:
        return "lectura"
    if re.search(r"\bvideo\b", n):
        return "video"
    if any(k in n for k in ("falta", "faltante", "pendiente", "hace falta",
                            "no se pudo", "a definir", "queda pendiente",
                            "sin terminar", "incompleto", "no esta disponible",
                            "esperando")):
        return "faltante"
    if n.startswith(("para maquetacion", "para el maquetado", "para diseno",
                     "para diseño", "maquetacion")):
        return "revisar"
    return None
```

(Nota: las señales negativas "sin recuadro…" que ya estaban al inicio se mantienen sin cambios.)

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `python -m pytest tests/test_docx_comments.py -q`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add maquetador/ingest/docx_comments.py tests/test_docx_comments.py
git commit -m "feat: clasificar comentarios de tabs/expander/tooltip/cita"
```

---

### Task 2: Extractor de pares (tabla alternada + texto "Nombre: contenido")

**Files:**
- Create: `maquetador/build/componentes_asesor.py`
- Test: `tests/test_componentes_asesor.py`

**Interfaces:**
- Produces:
  - `pares_de_tabla(tabla) -> list[tuple[str, str]]` — tabla 1 columna, celdas alternadas (título, contenido).
  - `pares_de_texto(parrafos: list) -> list[tuple[str, str]]` — párrafos "Nombre: contenido".
  - `extraer_pares(el) -> tuple[list[tuple[str,str]], list]` — orquestador: devuelve `(pares, consumidos)`. `pares`=[(título,contenido)], `consumidos`=elementos del soup a remover/reemplazar. `([], [])` si <2 pares.

- [ ] **Step 1: Escribir los tests que fallan**

Crear `tests/test_componentes_asesor.py`:

```python
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
        soup = _soup("<div><p>A: uno</p><p>B: dos</p></div>")
        el = soup.find("p")
        pares, consumidos = extraer_pares(el)
        assert len(pares) == 2
        assert len(consumidos) == 2          # ambos párrafos se consumen
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python -m pytest tests/test_componentes_asesor.py -q`
Expected: FAIL (módulo no existe).

- [ ] **Step 3: Implementar `componentes_asesor.py` (extractor)**

Crear `maquetador/build/componentes_asesor.py`:

```python
# -*- coding: utf-8 -*-
"""Construcción de componentes CidiLabs a partir de los pedidos del asesor.

Un extractor de pares (título, contenido) unificado alimenta a acordeón, tabs,
expander y flip card. Dos fuentes: una tabla de 1 columna con celdas alternadas
(título/contenido/título/contenido…) o párrafos "Nombre: contenido".
"""

import re

from bs4 import BeautifulSoup

_RE_NOMBRE_CONTENIDO = re.compile(r"^(.{2,60}?):\s+(.+)$", re.DOTALL)


def pares_de_tabla(tabla) -> list:
    """Tabla de 1 columna con celdas alternadas → [(titulo, contenido_html)]."""
    celdas = tabla.find_all(["td", "th"])
    plano = []
    for c in celdas:
        texto = c.get_text(" ", strip=True)
        inner = "".join(str(x) for x in c.children).strip()
        if texto:
            plano.append((texto, inner))
    pares = []
    for i in range(0, len(plano) - 1, 2):
        titulo = plano[i][0]
        contenido = plano[i + 1][1] or "&nbsp;"
        pares.append((titulo, contenido))
    return pares


def pares_de_texto(parrafos: list) -> list:
    """Párrafos 'Nombre: contenido' → [(nombre, contenido)]."""
    pares = []
    for p in parrafos:
        txt = p.get_text(" ", strip=True)
        m = _RE_NOMBRE_CONTENIDO.match(txt)
        if m:
            pares.append((m.group(1).strip(), m.group(2).strip()))
    return pares


def extraer_pares(el):
    """Desde el elemento anclado → (pares, consumidos). ([], []) si <2 pares.

    `consumidos` son los elementos del soup que el componente reemplaza: el
    primero se sustituye por el componente y el resto se elimina (así no quedan
    párrafos duplicados cuando el componente se arma desde varios párrafos).

    1) Tabla asociada (el mismo, o su hermano <table> siguiente).
    2) Si no, el elemento + hermanos <p>/<li> consecutivos con 'Nombre: contenido'.
    """
    # 1) Tabla
    if el.name == "table":
        tabla, consumidos_tabla = el, [el]
    else:
        t = el.find_next_sibling("table")
        tabla, consumidos_tabla = (t, [el, t]) if t is not None else (None, None)
    if tabla is not None:
        pares = pares_de_tabla(tabla)
        if len(pares) >= 2:
            return pares, consumidos_tabla

    # 2) Texto
    parrafos, actual = [], el
    while actual is not None and getattr(actual, "name", None) in ("p", "li"):
        parrafos.append(actual)
        actual = actual.find_next_sibling()
    pares = pares_de_texto(parrafos)
    if len(pares) >= 2:
        consumidos = [p for p in parrafos
                      if _RE_NOMBRE_CONTENIDO.match(p.get_text(" ", strip=True))]
        return pares, consumidos
    return [], []
```

- [ ] **Step 4: Correr y verificar que pasa**

Run: `python -m pytest tests/test_componentes_asesor.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add maquetador/build/componentes_asesor.py tests/test_componentes_asesor.py
git commit -m "feat: extractor de pares para componentes (tabla + texto)"
```

---

### Task 3: Builder de paneles (acordeón / tabs / expander)

**Files:**
- Modify: `maquetador/build/componentes_asesor.py`
- Test: `tests/test_componentes_asesor.py`

**Interfaces:**
- Consumes: `extraer_pares` (Task 2).
- Produces: `construir_panels(pares, variante: str = "dp-expander-default") -> str`.

- [ ] **Step 1: Test que falla**

Agregar a `tests/test_componentes_asesor.py`:

```python
from maquetador.build.componentes_asesor import construir_panels


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
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python -m pytest tests/test_componentes_asesor.py::TestConstruirPanels -q`
Expected: FAIL.

- [ ] **Step 3: Implementar `construir_panels`**

Agregar a `componentes_asesor.py`:

```python
def construir_panels(pares: list, variante: str = "dp-expander-default") -> str:
    """Acordeón (dp-expander-default) / tabs (dp-tabs) / expander. Misma
    estructura; cambia la clase del wrapper."""
    grupos = "\n".join(
        '<div class="dp-panel-group">\n'
        f'<h3 class="dp-panel-heading">{t}</h3>\n'
        f'<div class="dp-panel-content">{c}</div>\n</div>'
        for t, c in pares)
    return (f'<div class="dp-panels-wrapper {variante} '
            'dp-panel-color-dp-secondary dp-panel-active-color-dp-primary" '
            f'title="contenido insertado">\n{grupos}\n</div>')
```

- [ ] **Step 4: Correr y verificar que pasa**

Run: `python -m pytest tests/test_componentes_asesor.py::TestConstruirPanels -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add maquetador/build/componentes_asesor.py tests/test_componentes_asesor.py
git commit -m "feat: builder de paneles (acordeon/tabs/expander) CidiLabs"
```

---

### Task 4: Builder de flip cards + builder de popover + cita

**Files:**
- Modify: `maquetador/build/componentes_asesor.py`
- Test: `tests/test_componentes_asesor.py`

**Interfaces:**
- Produces:
  - `construir_flipcards(pares) -> str`
  - `construir_popover(palabra: str, contenido: str, n: int) -> tuple[str, str]` (trigger_html, content_html)
  - `aplicar_cita(el) -> None` (muta el elemento: agrega `margin-left: 40px`)

- [ ] **Step 1: Tests que fallan**

Agregar a `tests/test_componentes_asesor.py`:

```python
from bs4 import BeautifulSoup
from maquetador.build.componentes_asesor import (
    construir_flipcards, construir_popover, aplicar_cita,
)


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
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python -m pytest tests/test_componentes_asesor.py -k "Flipcards or Popover or Cita" -q`
Expected: FAIL.

- [ ] **Step 3: Implementar los tres builders**

Agregar a `componentes_asesor.py`:

```python
def construir_flipcards(pares: list) -> str:
    """Flip cards CidiLabs: frente = título (negrita), dorso = contenido."""
    cards = "\n".join(
        '<div class="dp-flip-card">\n<div class="dp-flip-card-inner">\n'
        '<div class="dp-front-card">'
        '<div class="dp-card card h-100 dp-shadow-b3 text-center">'
        f'<p><strong>{t}</strong></p></div></div>\n'
        '<div class="dp-back-card">'
        '<div class="dp-card card h-100 text-center dp-shadow-b3" style="padding: 16px;">'
        f'<p style="text-align: left;">{c}</p></div></div>\n'
        '</div>\n</div>'
        for t, c in pares)
    return f'<div class="row justify-content-center">\n{cards}\n</div>'


def construir_popover(palabra: str, contenido: str, n: int) -> tuple:
    """Popover CidiLabs: trigger (la palabra) + content (lo que emerge)."""
    trigger = (f'<a class="dp-popover-trigger" href="#dpPopup{n}Content" '
               f'id="dpPopup{n}" aria-describedby="dpPopup{n}Content">{palabra}</a>')
    content = (f'<div class="dp-popover-content dp-popup-content" id="dpPopup{n}Content" '
               'style="border: 1px solid #A9A9A9; background: #f7f7f7; padding: 10px; '
               'width: 600px; max-width: 100%; margin: auto; border-radius: 3px;">'
               f'<p>{contenido}</p></div>')
    return trigger, content


def aplicar_cita(el) -> None:
    """Sangra el párrafo anclado (sin caja, pedido del usuario)."""
    estilo = el.get("style", "").rstrip("; ")
    el["style"] = (estilo + "; " if estilo else "") + "margin-left: 40px;"
```

- [ ] **Step 4: Correr y verificar que pasa**

Run: `python -m pytest tests/test_componentes_asesor.py -q`
Expected: PASS (todos).

- [ ] **Step 5: Commit**

```bash
git add maquetador/build/componentes_asesor.py tests/test_componentes_asesor.py
git commit -m "feat: builders flip card, popover y cita CidiLabs"
```

---

### Task 5: Cablear los componentes en aplicar_comentarios (con fallback)

**Files:**
- Modify: `maquetador/ingest/docx_comments.py` (función `aplicar_comentarios`, ~líneas 135-168; y constante `_AUTO`, línea 33)
- Test: `tests/test_componentes_asesor.py`

**Interfaces:**
- Consumes: `extraer_pares`, `construir_panels`, `construir_flipcards`, `construir_popover`, `aplicar_cita` (Tasks 2-4); `_buscar_elemento` (existente en docx_comments.py).
- Produces: `aplicar_comentarios(soup, comentarios)` ahora también arma componentes; marca `c["_aplicado"]=True` solo si construyó.

- [ ] **Step 1: Test de integración (sobre soup) que falla**

Agregar a `tests/test_componentes_asesor.py`:

```python
from maquetador.ingest.docx_comments import aplicar_comentarios


class TestCableado:
    def test_acordeon_desde_texto_se_arma(self):
        soup = BeautifulSoup(
            "<div><p>Autoevaluación: la persona valora su propio desempeño.</p>"
            "<p>Evaluación por objetivos: mide el grado de cumplimiento.</p></div>",
            "html.parser")
        comentarios = [{
            "instruccion": "Maquetación: acordeón",
            "anclado": "Autoevaluación: la persona valora su propio desempeño.",
            "accion": "acordeon", "autor": "",
        }]
        aplicar_comentarios(soup, comentarios)
        assert "dp-panels-wrapper dp-expander-default" in str(soup)
        assert comentarios[0].get("_aplicado") is True

    def test_sin_estructura_no_se_aplica(self):
        soup = BeautifulSoup("<div><p>Un párrafo cualquiera.</p></div>", "html.parser")
        comentarios = [{
            "instruccion": "Maquetación: acordeón",
            "anclado": "Un párrafo cualquiera.",
            "accion": "acordeon", "autor": "",
        }]
        aplicar_comentarios(soup, comentarios)
        # No hay ≥2 pares → no se arma → queda como aviso (no _aplicado)
        assert "dp-panels-wrapper" not in str(soup)
        assert comentarios[0].get("_aplicado") is not True

    def test_cita_sangra(self):
        soup = BeautifulSoup("<div><p>La GT es una iniciativa estratégica.</p></div>", "html.parser")
        comentarios = [{
            "instruccion": "Maquetación: es una cita",
            "anclado": "La GT es una iniciativa estratégica.",
            "accion": "cita", "autor": "",
        }]
        aplicar_comentarios(soup, comentarios)
        assert "margin-left: 40px" in str(soup)
        assert comentarios[0].get("_aplicado") is True
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python -m pytest tests/test_componentes_asesor.py::TestCableado -q`
Expected: FAIL (acordeon/cita no se aplican hoy).

- [ ] **Step 3: Cablear en `aplicar_comentarios`**

En `maquetador/ingest/docx_comments.py`:

3a. Agregar import al inicio (junto a los otros de `maquetador.build`):

```python
from maquetador.build.componentes_asesor import (
    extraer_pares, construir_panels, construir_flipcards,
    construir_popover, aplicar_cita,
)
```

3b. Debajo de `_AUTO` (línea 33), agregar:

```python
_COMPONENTES = {"acordeon", "tabs", "expander", "flip_card", "tooltip", "cita"}
_VARIANTE_PANEL = {"acordeon": "dp-expander-default",
                   "tabs": "dp-tabs",
                   "expander": "dp-expander-default"}
```

3c. En `aplicar_comentarios`, cambiar la guarda de la línea 142 y agregar el manejo de componentes. Reemplazar el cuerpo del `for c in comentarios:` (líneas 140-168) por:

```python
    contador_popover = 0
    for c in comentarios:
        accion = c["accion"]
        if c.get("_aplicado"):
            continue
        if accion not in _AUTO and accion not in _COMPONENTES:
            continue
        el = _buscar_elemento(soup, c["anclado"])
        if el is None:
            continue

        # --- Componentes de pedido del asesor ---
        if accion in _VARIANTE_PANEL:                 # acordeon / tabs / expander
            pares, consumidos = extraer_pares(el)
            if len(pares) >= 2:
                html = construir_panels(pares, _VARIANTE_PANEL[accion])
                consumidos[0].replace_with(BeautifulSoup(html, "html.parser"))
                for extra in consumidos[1:]:
                    extra.decompose()
                c["_aplicado"] = True
            continue
        if accion == "flip_card":
            pares, consumidos = extraer_pares(el)
            if len(pares) >= 2:
                html = construir_flipcards(pares)
                consumidos[0].replace_with(BeautifulSoup(html, "html.parser"))
                for extra in consumidos[1:]:
                    extra.decompose()
                c["_aplicado"] = True
            continue
        if accion == "tooltip":
            contenido = _texto_tooltip(c["instruccion"])
            palabra = (c["anclado"] or "").strip()
            if contenido and palabra:
                trigger, content = construir_popover(palabra, contenido, contador_popover)
                contador_popover += 1
                nuevo = BeautifulSoup(
                    el.get_text(" ", strip=True).replace(palabra, trigger, 1)
                    + content, "html.parser")
                el.replace_with(nuevo)
                c["_aplicado"] = True
            continue
        if accion == "cita":
            aplicar_cita(el)
            c["_aplicado"] = True
            continue

        # --- Acciones simples existentes ---
        c["_aplicado"] = True
        inner = "".join(str(x) for x in el.children).strip()
        if accion == "subtitulo":
            h3 = soup.new_tag("h3")
            h3.string = el.get_text(" ", strip=True)
            el.replace_with(h3)
        elif accion == "quitar":
            el.decompose()
        elif accion == "recuadro_simple":
            el.replace_with(BeautifulSoup(resaltado_simple(inner), "html.parser"))
        elif accion == "lectura":
            el.replace_with(BeautifulSoup(
                cta_titulo("Lectura", f"<p>{inner}</p>", ICONOS["lectura"]),
                "html.parser"))
        elif accion == "video":
            el.replace_with(BeautifulSoup(
                cta_titulo("Video", f"<p>{inner}</p>", ICONOS["video"]),
                "html.parser"))
        elif accion == "sin_recuadro":
            el["data-keep-plain"] = "1"
```

3d. Agregar el helper `_texto_tooltip` (antes de `aplicar_comentarios`):

```python
def _texto_tooltip(instruccion: str) -> str:
    """Saca el contenido del popover del comentario: lo que va después de
    'emerja:'/'aparezca:'/'tooltip-->'. Si no hay marcador claro, '' (→ fallback)."""
    for sep in ("emerja lo siguiente:", "emerja:", "aparezca:", "emerge:",
                "tooltip-->", "tooltip -->", "tooltip:", "globo:"):
        if sep in instruccion.lower():
            idx = instruccion.lower().index(sep) + len(sep)
            return instruccion[idx:].strip(" .–-")
    return ""
```

- [ ] **Step 4: Correr y verificar que pasa**

Run: `python -m pytest tests/test_componentes_asesor.py -q`
Expected: PASS (todos, incluida TestCableado).

- [ ] **Step 5: Verificar que no rompí lo existente**

Run: `python -m pytest tests/test_docx_comments.py tests/test_folder_scanner.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add maquetador/ingest/docx_comments.py tests/test_componentes_asesor.py
git commit -m "feat: cablear componentes del asesor en aplicar_comentarios con fallback"
```

---

### Task 6: Corregir el flip card viejo de snippets.py

**Files:**
- Modify: `maquetador/build/snippets.py` (función `_tabla_a_flipcards`, ~líneas 586-620)
- Test: `tests/test_componentes_asesor.py`

**Interfaces:**
- Consumes: `construir_flipcards` (Task 4).

- [ ] **Step 1: Test que falla**

Agregar a `tests/test_componentes_asesor.py`:

```python
from bs4 import BeautifulSoup as _BS
from maquetador.build.snippets import _tabla_a_flipcards


class TestFlipcardViejoAlineado:
    def test_usa_clases_cidilabs_reales(self):
        html = ("<table><tr><td>"
                "<p><strong>Frente A</strong> dorso A largo</p>"
                "<p><strong>Frente B</strong> dorso B largo</p>"
                "</td></tr></table>")
        tabla = _BS(html, "html.parser").find("table")
        out = _tabla_a_flipcards(tabla)
        assert out is not None
        assert "dp-front-card" in out          # clase CidiLabs real
        assert "dp-flip-card-front" not in out  # ya NO la clase vieja
```

- [ ] **Step 2: Correr y verificar que falla**

Run: `python -m pytest tests/test_componentes_asesor.py::TestFlipcardViejoAlineado -q`
Expected: FAIL (hoy emite `dp-flip-card-front card`).

- [ ] **Step 3: Reemplazar el render de `_tabla_a_flipcards`**

En `maquetador/build/snippets.py`, en `_tabla_a_flipcards`, reemplazar el bloque que arma `tarjetas`/`return` (desde `tarjetas = "\n".join(` hasta el `return`) por una llamada al builder nuevo. Al inicio del archivo agregar el import:

```python
from maquetador.build.componentes_asesor import construir_flipcards
```

Y el final de la función:

```python
    if len(items) < 2:
        return None
    return construir_flipcards(items)
```

(`items` ya es `[(frente, dorso), …]`, compatible con `construir_flipcards`.)

- [ ] **Step 4: Correr y verificar que pasa**

Run: `python -m pytest tests/test_componentes_asesor.py::TestFlipcardViejoAlineado -q`
Expected: PASS.

- [ ] **Step 5: Verificar que no hay import circular ni tests rotos**

Run: `python -c "import maquetador.build.snippets"` (Expected: sin error)
Run: `python -m pytest tests/ -q` (Expected: PASS)

- [ ] **Step 6: Commit**

```bash
git add maquetador/build/snippets.py tests/test_componentes_asesor.py
git commit -m "fix: flip card de tablas usa clases CidiLabs reales"
```

---

### Task 7: Verificación end-to-end sobre curso real

**Files:**
- Test manual: curso "Desempeño y Rendimiento" (ya en `cursos_subidos/`)

**Interfaces:**
- Consumes: todo el subsistema.

- [ ] **Step 1: Regenerar el aula y revisar avisos vs componentes**

Run:
```bash
python -m maquetador.cli "cursos_subidos/Desempeno y Rendimiento/Desempeno y Rendimiento" --tema posgrado --generar
```
Expected: en la salida, los pedidos de acordeón/tabs/flip con estructura clara YA NO aparecen como aviso (se armaron); los que no tienen estructura siguen como aviso.

- [ ] **Step 2: Verificar el HTML generado tiene componentes CidiLabs**

Run:
```bash
python -c "
import glob, os
wf = sorted(glob.glob('output/working_Desempe*'), key=os.path.getmtime)[-1]
import subprocess
todo=''
for root,_,fs in os.walk(wf):
    for f in fs:
        if f.endswith('.html'):
            todo += open(os.path.join(root,f),encoding='utf-8',errors='ignore').read()
for c in ['dp-panels-wrapper','dp-flip-card','dp-popover-trigger','margin-left: 40px']:
    print(c, todo.count(c))
"
```
Expected: al menos un componente con count > 0.

- [ ] **Step 3: Commit (si hace falta dejar constancia)**

```bash
git add -A
git commit -m "test: verificacion e2e componentes del asesor en curso real" --allow-empty
```

---

## Resumen

**7 tareas:**
1. Clasificar tabs/expander/tooltip/cita
2. Extractor de pares (tabla + texto)
3. Builder de paneles (acordeón/tabs/expander)
4. Builders flip card / popover / cita
5. Cableado en `aplicar_comentarios` (con fallback)
6. Alinear flip card viejo de snippets
7. Verificación end-to-end

**Orden incremental:** 1-2 sientan la base; 3-4 los builders (testeables solos); 5 los conecta; 6 limpia deuda; 7 valida en real. Cada tarea deja tests en verde y un commit.
