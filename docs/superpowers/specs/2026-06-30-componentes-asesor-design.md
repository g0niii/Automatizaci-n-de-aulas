# Auto-construcción de componentes de maquetación (Subsistema A)

> **Objetivo:** que el sistema **arme** los componentes de maquetación que pide el asesor en los comentarios del DOCX (cita, tooltip, acordeón, tabs, expander, flip card), en vez de solo listarlos como avisos. Output en HTML CidiLabs real (igual al aula modelo).

**Alcance:** Subsistema A — los 6 componentes que viven **dentro de una página** (transformación de HTML). El subsistema B ("página aparte" — cortar contenido y crear páginas nuevas) queda fuera, para un spec propio.

**Tech stack:** Python + BeautifulSoup (igual que el resto del pipeline). Sin dependencias nuevas.

---

## Principio rector: best-effort con fallback seguro

Cada componente intenta construirse con una heurística. Si la estructura se detecta con confianza → se arma. Si no → se **deja el contenido como hoy + se mantiene el aviso** actual. **Nunca produce basura silenciosa.** En el peor caso, el resultado es igual al de hoy.

Cada acción reporta qué hizo:
- ✅ "Acordeón armado (4 paneles) en M2"
- ⚠ "Pedido de flip card sobre 'X' — no detecté estructura clara, revisar a mano"

---

## Estructuras de salida (HTML real, extraído del aula modelo)

Verificadas en `Elementos de las aulas/aula-modelo-asesores-export.imscc`.

### Acordeón / Tabs / Expander (comparten estructura)
```html
<div class="dp-panels-wrapper {VARIANTE}">
  <div class="dp-panel-group">
    <h3 class="dp-panel-heading">TÍTULO</h3>
    <div class="dp-panel-content">CONTENIDO</div>
  </div>
  <!-- un dp-panel-group por par (título, contenido) -->
</div>
```
- `{VARIANTE}` = `dp-expander-default dp-panel-color-dp-secondary dp-panel-active-color-dp-primary` (acordeón/expander)
- `{VARIANTE}` = `dp-tabs dp-panel-color-dp-secondary dp-panel-active-color-dp-primary` (tabs)

### Flip card
```html
<div class="row justify-content-center">
  <div class="dp-flip-card">
    <div class="dp-flip-card-inner">
      <div class="dp-front-card">
        <div class="dp-card card h-100 dp-shadow-b3 text-center">
          <p><strong>TÍTULO (FRENTE)</strong></p>
        </div>
      </div>
      <div class="dp-back-card">
        <div class="dp-card card h-100 text-center dp-shadow-b3" style="padding: 16px;">
          <p style="text-align: left;">CONTENIDO (DORSO)</p>
        </div>
      </div>
    </div>
  </div>
  <!-- un dp-flip-card por par -->
</div>
```

### Tooltip / Popover
```html
<a class="dp-popover-trigger" href="#dpPopup{N}Content" id="dpPopup{N}"
   aria-describedby="dpPopup{N}Content">PALABRA ANCLADA</a>
...
<div class="dp-popover-content dp-popup-content" id="dpPopup{N}Content"
     style="border: 1px solid #A9A9A9; background: #f7f7f7; padding: 10px;
            width: 600px; max-width: 100%; margin: auto; border-radius: 3px;">
  <p>CONTENIDO DEL POPOVER</p>
</div>
```
- `{N}` = índice incremental único por página (dpPopup0, dpPopup1, …).

### Cita
- El párrafo anclado con **sangría**: se le agrega `style="margin-left: 40px;"` (o clase equivalente). Sin caja ni comillas — pedido explícito del usuario.

---

## El extractor de pares (corazón unificado)

`extraer_pares(region) -> list[(titulo, contenido)]`

Alimenta a acordeón, tabs, expander y flip card. Prueba dos estrategias en orden:

1. **Tabla de 1 columna con celdas alternadas** (convención del asesor):
   celda 1 = título, celda 2 = contenido, celda 3 = título, celda 4 = contenido, …
   Cada par de celdas consecutivas → un par `(titulo, contenido)`.

2. **Texto "Nombre: contenido"** (sin tabla, p.ej. flip cards en texto suelto):
   cada párrafo/línea que matchee `^<nombre corto>: <contenido>` →
   par `(nombre, contenido)`. El nombre es la parte antes del primer `:`.

**Criterio de éxito:** ≥2 pares. Si <2 → la función devuelve `[]` y el componente cae al **fallback** (aviso de hoy).

---

## Disparadores (clasificación de comentarios)

Extiende `_clasificar()` en `docx_comments.py`. Hoy clasifica acordeon/flip_card y otros, pero solo auto-aplica `_AUTO = {subtitulo, recuadro_simple, lectura, video, sin_recuadro}`. Se agregan al set de auto-aplicables (o a un nuevo flujo) estas acciones:

| Acción | Señal en el comentario | Componente |
|--------|------------------------|-----------|
| `cita` | "es una cita", "esto es una cita" | Cita (sangría) |
| `tooltip` | "al hacer clic ... emerja/aparezca", "tooltip" | Popover |
| `acordeon` | "acordeón" | Acordeón |
| `tabs` | "tabs", "pestañas" | Tabs |
| `expander` | "expander", "expandible" | Expander |
| `flip_card` | "flip card", "tarjetas que se dan vuelta" | Flip card |

---

## Arquitectura y archivos

**Crear:** `maquetador/build/componentes_asesor.py`
- `extraer_pares(region_soup) -> list[(str, str)]` — extractor unificado (tabla + texto)
- `construir_panels(pares, variante) -> str` — acordeón/tabs/expander
- `construir_flipcards(pares) -> str` — flip cards
- `construir_popover(palabra, contenido, n) -> (trigger_html, content_html)`
- `aplicar_cita(elemento)` — sangra el párrafo
- Cada `construir_*` usa las plantillas HTML de arriba (CidiLabs real).

**Modificar:** `maquetador/ingest/docx_comments.py`
- `_clasificar()`: agregar `tabs`, `expander`, `tooltip`, `cita` (acordeon/flip_card ya existen).
- `aplicar_comentarios()`: para las 6 acciones, ubicar la región anclada, intentar construir; si falla, marcar para fallback (no `_aplicado`).
- Mantener el aviso actual SOLO para los que no se pudieron construir.

**Corregir:** `maquetador/build/snippets.py`
- `_tabla_a_flipcards`: usa clases viejas (`dp-flip-card-front card`) que NO matchean CidiLabs. Alinear a `dp-front-card`/`dp-back-card`. (O reusar `componentes_asesor.construir_flipcards`.)

**Tests:** `tests/test_componentes_asesor.py`
- `extraer_pares`: tabla alternada, texto "Nombre: contenido", <2 pares → [].
- Cada `construir_*`: verifica clases CidiLabs reales en el output.
- Fallback: comentario sin estructura → devuelve aviso, no rompe.

---

## Flujo de datos

```
DOCX comment (anclado a texto)
  → _clasificar() → acción
  → aplicar_comentarios():
       cita     → aplicar_cita(párrafo)
       tooltip  → construir_popover(palabra, contenido_del_comentario, n)
       acordeon ┐
       tabs     ├→ extraer_pares(region)
       expander ┘     ├ ≥2 pares → construir_panels(pares, variante) → reemplazar región
       flip     ┘     └ <2 pares → fallback (aviso de hoy)
```

---

## Manejo de errores / casos límite

- **Región no encontrada** (el texto anclado no aparece en la sección cortada): fallback aviso.
- **Tabla con celdas impares** (último título sin contenido): el último par usa contenido `&nbsp;`.
- **Tooltip sin contenido en el comentario** (no hay texto después de "emerja:"): fallback aviso.
- **Popover ids**: contador por página para evitar colisiones de `dpPopupN`.
- **Doble aplicación**: marcar `_aplicado` para no procesar el mismo comentario dos veces (patrón ya existente).

---

## Criterios de éxito

✅ En el curso "Desempeño y Rendimiento", los pedidos de acordeón/tabs/flip que tengan estructura clara se arman solos.
✅ El HTML generado matchea las clases CidiLabs del aula modelo (se ve nativo en Canvas).
✅ Lo que no se puede armar con confianza sigue saliendo como aviso (igual que hoy) — cero regresión.
✅ Cada componente reporta ✅ armado o ⚠ no-pudo, con el módulo y el texto anclado.
✅ Tests por componente con HTML real del aula modelo.

---

## Fuera de alcance (para después)

- **Subsistema B: "página aparte"** — cortar contenido y crear páginas nuevas en el plan. Spec propio.
- Componentes no pedidos por los asesores hoy (timelines, carruseles, etc.).
- Edición de los componentes ya armados desde la web F4.
