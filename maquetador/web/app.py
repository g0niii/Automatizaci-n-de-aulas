# -*- coding: utf-8 -*-
"""Web interna del Maquetador UCC.

Flujo: subir la carpeta del curso (ZIP tal como llega de asesoría) →
elegir el aula base → revisar el plan de maquetación → generar y
descargar el .imscc.

Ejecutar:  python -m maquetador.web.app   (luego abrir http://localhost:5000)
"""

import io
import re
import shutil
import sys
import unicodedata
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from flask import (Flask, render_template, request, redirect, url_for,
                   send_file, flash)

from maquetador.cli import analizar_curso
from maquetador.extract.extractor import extraer_contenido
from maquetador.models import Severidad, TipoItem
from maquetador.plan import guardar_plan, TEMAS_DISPONIBLES

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CURSOS_DIRS = [BASE_DIR / "cursos_subidos", BASE_DIR / "casos"]
OUTPUT_DIR = BASE_DIR / "output"

app = Flask(__name__)
app.secret_key = "maquetador-ucc-interno"
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024  # ZIPs de hasta 500 MB


def _slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-zA-Z0-9]+", "-", t.lower()).strip("-")[:70]


def _cursos_disponibles() -> dict:
    """{slug: Path} de todas las carpetas de curso conocidas."""
    cursos = {}
    for raiz in CURSOS_DIRS:
        if not raiz.is_dir():
            continue
        for d in sorted(raiz.iterdir()):
            if d.is_dir():
                cursos.setdefault(_slug(d.name), d)
    return cursos


def _extraer_zip_seguro(data: bytes, destino: Path):
    """Extrae el ZIP sanitizando nombres (espacios/puntos finales rompen
    en Windows) — los ZIP de Drive suelen traerlos."""
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            partes = [p.strip().rstrip(".") for p in info.filename.split("/")
                      if p.strip() and ".." not in p]
            if not partes:
                continue
            target = destino.joinpath(*partes)
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)


# ------------------------------------------------------------------ #
#  Rutas
# ------------------------------------------------------------------ #

@app.route("/")
def index():
    return render_template("index.html", cursos=_cursos_disponibles())


@app.route("/subir", methods=["POST"])
def subir():
    archivo = request.files.get("zip")
    if not archivo or not archivo.filename.lower().endswith(".zip"):
        flash("Subí un archivo .zip con la carpeta del curso.", "error")
        return redirect(url_for("index"))
    nombre = re.sub(r"-\d{8}T\d{6}Z-\d+-\d+$", "",
                    Path(archivo.filename).stem).strip()
    destino = BASE_DIR / "cursos_subidos" / nombre
    if destino.exists():
        shutil.rmtree(destino)
    try:
        _extraer_zip_seguro(archivo.read(), destino)
    except zipfile.BadZipFile:
        flash("El archivo no es un ZIP válido.", "error")
        return redirect(url_for("index"))
    flash(f"Curso '{nombre}' cargado. Elegí el aula base para analizarlo.", "ok")
    return redirect(url_for("ver_curso", curso_id=_slug(nombre)))


@app.route("/curso/<curso_id>")
def ver_curso(curso_id):
    cursos = _cursos_disponibles()
    carpeta = cursos.get(curso_id)
    if carpeta is None:
        flash("No encuentro ese curso.", "error")
        return redirect(url_for("index"))
    tema = request.args.get("tema", "")
    if tema not in TEMAS_DISPONIBLES:
        tema = ""

    spec = analizar_curso(carpeta, tema)
    if tema:
        extraer_contenido(spec)
        guardar_plan(spec, OUTPUT_DIR / "planes")

    bloqueantes = sum(1 for i in spec.todos_los_items() for s in i.issues
                      if s.severidad == Severidad.BLOQUEANTE)
    bloqueantes += sum(1 for s in spec.issues
                       if s.severidad == Severidad.BLOQUEANTE
                       and not s.mensaje.startswith("Falta elegir"))
    return render_template(
        "plan.html", spec=spec, curso_id=curso_id, tema=tema,
        temas=TEMAS_DISPONIBLES, bloqueantes=bloqueantes,
        TipoItem=TipoItem, Severidad=Severidad,
        ultimo_paquete=_ultimo_paquete_de(spec))


def _ultimo_paquete_de(spec):
    """Nombre del .imscc más reciente generado para este curso."""
    prefijo = (spec.codigo or re.sub(r"[^A-Za-z0-9]+", "_",
                                     spec.nombre)[:40]).strip("_")
    paquetes = sorted(OUTPUT_DIR.glob(f"{prefijo}_*.imscc"),
                      key=lambda p: p.stat().st_mtime, reverse=True)
    return paquetes[0].name if paquetes else None


@app.route("/curso/<curso_id>/generar", methods=["POST"])
def generar(curso_id):
    cursos = _cursos_disponibles()
    carpeta = cursos.get(curso_id)
    tema = request.form.get("tema", "")
    if carpeta is None or tema not in TEMAS_DISPONIBLES:
        flash("Curso o aula base inválidos.", "error")
        return redirect(url_for("index"))

    spec = analizar_curso(carpeta, tema)
    media = extraer_contenido(spec)
    bloqueantes = [s for i in spec.todos_los_items() for s in i.issues
                   if s.severidad == Severidad.BLOQUEANTE]
    bloqueantes += [s for s in spec.issues
                    if s.severidad == Severidad.BLOQUEANTE]
    if bloqueantes:
        flash(f"No se generó el paquete: hay {len(bloqueantes)} problemas "
              "bloqueantes. Revisalos abajo.", "error")
        return redirect(url_for("ver_curso", curso_id=curso_id, tema=tema))

    from maquetador.build.imscc_builder import generar_imscc
    try:
        salida = generar_imscc(spec, media, OUTPUT_DIR)
    except Exception as e:
        flash(f"Error generando el paquete: {e}", "error")
        return redirect(url_for("ver_curso", curso_id=curso_id, tema=tema))
    guardar_plan(spec, OUTPUT_DIR / "planes")
    flash(f"✅ Paquete generado: {salida.name} — descargalo con el botón de abajo.",
          "ok")
    return redirect(url_for("ver_curso", curso_id=curso_id, tema=tema))


@app.route("/descargar/<path:nombre>")
def descargar(nombre):
    path = (OUTPUT_DIR / nombre).resolve()
    if not str(path).startswith(str(OUTPUT_DIR.resolve())) or not path.is_file():
        flash("Archivo no encontrado.", "error")
        return redirect(url_for("index"))
    return send_file(path, as_attachment=True)


if __name__ == "__main__":
    import os
    (BASE_DIR / "cursos_subidos").mkdir(exist_ok=True)
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)),
            debug=False)
