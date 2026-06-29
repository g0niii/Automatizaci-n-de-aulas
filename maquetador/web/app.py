# -*- coding: utf-8 -*-
"""Web interna del Maquetador UCC.

Flujo: subir la carpeta del curso (ZIP tal como llega de asesoría) →
elegir el aula base → revisar el plan de maquetación → generar y
descargar el .imscc.

Ejecutar:  python -m maquetador.web.app   (luego abrir http://localhost:5000)
"""

import io
import json
import re
import shutil
import sys
import unicodedata
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from flask import (Flask, render_template, request, redirect, url_for,
                   send_file, flash, jsonify, session)

from maquetador.cli import analizar_curso
from maquetador.extract.extractor import extraer_contenido
from maquetador.models import (Severidad, TipoItem, CourseSpec, ModuloCurso,
                               ItemCurso, FuenteContenido, Issue)
from maquetador.plan import guardar_plan, TEMAS_DISPONIBLES
from maquetador.web.api import guardar_cambios_plan

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

def _cargar_cursos() -> list:
    """Lee todas las aulas procesadas desde output/planes/*.json."""
    planes_dir = OUTPUT_DIR / 'planes'
    cursos = []
    if planes_dir.exists():
        for archivo_plan in sorted(planes_dir.glob('plan_*.json')):
            try:
                with open(archivo_plan, 'r', encoding='utf-8') as f:
                    plan = json.load(f)
                    cursos.append({
                        'nombre': plan.get('nombre', 'Sin nombre'),
                        'codigo': plan.get('codigo', ''),
                        'tema': plan.get('tema', 'educacion'),
                        'plan_id': archivo_plan.stem,
                        'modulos': plan.get('modulos', []),
                        'items_count': sum(len(m.get('items', [])) for m in plan.get('modulos', [])),
                    })
            except Exception as e:
                app.logger.error(f"Error cargando {archivo_plan}: {e}")
    return cursos


@app.route('/')
def index():
    """Dashboard: subir aulas + ver las procesadas."""
    return render_template('dashboard.html', courses=_cargar_cursos())


@app.route('/cursos')
def cursos():
    """Registro completo de aulas con búsqueda y filtros."""
    return render_template('cursos.html', courses=_cargar_cursos())


@app.route('/api/set-tema', methods=['POST'])
def set_tema():
    """Guardar preferencia de tema en la sesión."""
    try:
        data = request.get_json() or {}
        session['tema'] = data.get('tema', 'educacion')
        return jsonify({'success': True})
    except Exception as e:
        app.logger.error(f"Error in set_tema: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/api/course/<course_id>', methods=['DELETE'])
def delete_course(course_id):
    """Eliminar un curso y sus archivos generados."""
    try:
        planes_dir = OUTPUT_DIR / 'planes'

        # Buscar y eliminar JSON del plan
        archivo_plan = planes_dir / f"plan_{course_id}.json"
        if archivo_plan.exists():
            archivo_plan.unlink()

        # Eliminar IMSCC si existe
        archivo_imscc = OUTPUT_DIR / f"{course_id}.imscc"
        if archivo_imscc.exists():
            archivo_imscc.unlink()

        return jsonify({'success': True, 'mensaje': 'Curso eliminado'})
    except Exception as e:
        app.logger.error(f"Error eliminando curso {course_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


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


def _plan_dict_a_coursespec(plan_dict: dict) -> tuple[CourseSpec, list[str]]:
    """Convierte un plan dict (del JSON) a un CourseSpec.

    Args:
        plan_dict: Dict con estructura del plan (de JSON)

    Returns:
        (spec, errores) donde errores es lista de mensajes de error (vacía si OK)
    """
    errores = []

    # Validar campos obligatorios
    requeridos = ["nombre", "modulos", "items_inicio", "afi"]
    for campo in requeridos:
        if campo not in plan_dict:
            errores.append(f"Falta campo requerido: {campo}")

    if errores:
        return None, errores

    try:
        # Crear CourseSpec
        spec = CourseSpec(
            nombre=plan_dict.get("nombre", "Sin nombre"),
            codigo=plan_dict.get("codigo", ""),
            tema=plan_dict.get("tema", "educacion"),
            docentes=plan_dict.get("docentes", []),
        )

        # Reconstructo módulos
        for mod_dict in plan_dict.get("modulos", []):
            items = []
            for item_dict in mod_dict.get("items", []):
                # Reconstruir FuenteContenido
                fuente_dict = item_dict.get("fuente", {})
                fuente = FuenteContenido(
                    archivo=Path(fuente_dict.get("archivo"))
                           if fuente_dict.get("archivo") else None,
                    seccion=fuente_dict.get("seccion"),
                    confianza=fuente_dict.get("confianza", 0.95)
                )

                # Reconstruir Issue list
                issues = []
                for issue_dict in item_dict.get("issues", []):
                    sev = issue_dict.get("severidad", "info")
                    try:
                        sev = Severidad(sev)
                    except ValueError:
                        sev = Severidad.INFO
                    issues.append(Issue(
                        severidad=sev,
                        mensaje=issue_dict.get("mensaje", ""),
                        contexto=issue_dict.get("contexto", "")
                    ))

                # Reconstruir ItemCurso
                tipo_str = item_dict.get("tipo", "pagina")
                try:
                    tipo = TipoItem(tipo_str)
                except ValueError:
                    tipo = TipoItem.PAGINA

                item = ItemCurso(
                    titulo=item_dict.get("titulo", ""),
                    tipo=tipo,
                    orden=item_dict.get("orden", 0),
                    fuente=fuente,
                    estado_planilla=item_dict.get("estado_planilla", ""),
                    comentarios_asesor=item_dict.get("comentarios_asesor", ""),
                    detalle=item_dict.get("detalle", {}),
                    issues=issues
                )
                items.append(item)

            # Crear ModuloCurso
            modulo = ModuloCurso(
                numero=mod_dict.get("numero", 0),
                titulo=mod_dict.get("titulo", ""),
                items=items
            )
            spec.modulos.append(modulo)

        # Reconstruir items_inicio
        for item_dict in plan_dict.get("items_inicio", []):
            fuente_dict = item_dict.get("fuente", {})
            fuente = FuenteContenido(
                archivo=Path(fuente_dict.get("archivo"))
                       if fuente_dict.get("archivo") else None,
                seccion=fuente_dict.get("seccion"),
                confianza=fuente_dict.get("confianza", 0.95)
            )
            tipo_str = item_dict.get("tipo", "pagina")
            try:
                tipo = TipoItem(tipo_str)
            except ValueError:
                tipo = TipoItem.PAGINA
            item = ItemCurso(
                titulo=item_dict.get("titulo", ""),
                tipo=tipo,
                orden=item_dict.get("orden", 0),
                fuente=fuente,
                estado_planilla=item_dict.get("estado_planilla", ""),
                comentarios_asesor=item_dict.get("comentarios_asesor", ""),
                detalle=item_dict.get("detalle", {}),
                issues=[]
            )
            spec.items_inicio.append(item)

        # Reconstruir afi (Actividad Final Integradora)
        for item_dict in plan_dict.get("afi", []):
            fuente_dict = item_dict.get("fuente", {})
            fuente = FuenteContenido(
                archivo=Path(fuente_dict.get("archivo"))
                       if fuente_dict.get("archivo") else None,
                seccion=fuente_dict.get("seccion"),
                confianza=fuente_dict.get("confianza", 0.95)
            )
            tipo_str = item_dict.get("tipo", "pagina")
            try:
                tipo = TipoItem(tipo_str)
            except ValueError:
                tipo = TipoItem.PAGINA
            item = ItemCurso(
                titulo=item_dict.get("titulo", ""),
                tipo=tipo,
                orden=item_dict.get("orden", 0),
                fuente=fuente,
                estado_planilla=item_dict.get("estado_planilla", ""),
                comentarios_asesor=item_dict.get("comentarios_asesor", ""),
                detalle=item_dict.get("detalle", {}),
                issues=[]
            )
            spec.afi.append(item)

        return spec, []

    except Exception as e:
        errores.append(f"Error reconstruyendo CourseSpec: {str(e)}")
        return None, errores


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


@app.route("/plan/<plan_id>/edit", methods=["GET"])
def editar_plan(plan_id):
    """Muestra el formulario para editar un plan.

    Args:
        plan_id: Identificador del plan (ej: plan_001, plan_EP00356)

    Returns:
        Página HTML con formulario de edición del plan.
    """
    # Validar plan_id contra traversal
    if ".." in plan_id or "/" in plan_id:
        flash("plan_id inválido.", "error")
        return redirect(url_for("index"))

    # Buscar plan original
    planes_dir = OUTPUT_DIR / "planes"
    plan_path = (planes_dir / plan_id).with_suffix(".json")

    # Validar que está dentro de OUTPUT_DIR
    try:
        plan_path = plan_path.resolve()
        if not str(plan_path).startswith(str((OUTPUT_DIR / "planes").resolve())):
            flash("Acceso denegado.", "error")
            return redirect(url_for("index"))
    except (OSError, ValueError):
        flash("plan_id inválido.", "error")
        return redirect(url_for("index"))

    if not plan_path.exists():
        flash("Plan no encontrado.", "error")
        return redirect(url_for("index"))

    # Leer plan original
    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            plan = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        flash(f"Error leyendo plan: {e}", "error")
        return redirect(url_for("index"))

    # Extraer curso_id desde el plan o usar uno por defecto
    curso_id = plan.get("curso_id", "")

    return render_template("edit_plan.html", plan=plan, plan_id=plan_id,
                           curso_id=curso_id)


@app.route("/api/plan/<plan_id>/guardar", methods=["POST"])
def guardar_plan_editado(plan_id):
    """API para guardar cambios en un plan.

    POST body:
    {
      "plan": { plan editado como dict }
    }

    Returns:
    {
      "exito": bool,
      "cambios": [...],
      "errores": [...],
      "ruta_guardada": "planes/plan_XXX.json" (si exito=True)
    }
    """
    # Validar plan_id contra traversal
    if ".." in plan_id or "/" in plan_id:
        return jsonify({"exito": False, "cambios": [], "errores": ["plan_id inválido"]}), 400

    # Buscar plan original
    planes_dir = OUTPUT_DIR / "planes"
    plan_path = (planes_dir / plan_id).with_suffix(".json")

    # Validar que está dentro de OUTPUT_DIR
    try:
        plan_path = plan_path.resolve()
        if not str(plan_path).startswith(str((OUTPUT_DIR / "planes").resolve())):
            return jsonify({"exito": False, "cambios": [], "errores": ["Acceso denegado"]}), 403
    except (OSError, ValueError):
        return jsonify({"exito": False, "cambios": [], "errores": ["plan_id inválido"]}), 400

    if not plan_path.exists():
        return jsonify({"exito": False, "cambios": [], "errores": ["Plan no encontrado"]}), 404

    # Leer plan original
    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            plan_original = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        return jsonify({"exito": False, "cambios": [], "errores": [f"Error leyendo plan: {e}"]}), 500

    # Obtener plan editado del request
    try:
        data = request.get_json()
        if not data or "plan" not in data:
            return jsonify({"exito": False, "cambios": [], "errores": ["Request debe incluir 'plan'"]}), 400
        plan_editado = data["plan"]
    except Exception as e:
        return jsonify({"exito": False, "cambios": [], "errores": [f"Error parseando request: {e}"]}), 400

    # Comparar y validar cambios
    resultado = guardar_cambios_plan(plan_original, plan_editado)

    # Si no hay errores, guardar
    if resultado["exito"]:
        try:
            planes_dir.mkdir(parents=True, exist_ok=True)
            with open(plan_path, "w", encoding="utf-8") as f:
                json.dump(plan_editado, f, indent=2, ensure_ascii=False)
            resultado["ruta_guardada"] = f"planes/{plan_path.name}"
        except IOError as e:
            resultado["exito"] = False
            resultado["errores"].append(f"Error guardando: {e}")
            return jsonify(resultado), 500

    return jsonify(resultado), 200


@app.route("/plan/<plan_id>/generar", methods=["GET"])
def generar_desde_plan_editado(plan_id):
    """Genera IMSCC a partir de un plan editado.

    Workflow:
      1. Validar plan_id (contra traversal)
      2. Cargar plan JSON desde OUTPUT_DIR/planes
      3. Reconstruir CourseSpec desde plan dict
      4. Extraer contenido
      5. Generar IMSCC
      6. Redirigir con descarga

    Args:
        plan_id: Identificador del plan (ej: plan_001, plan_EP00356)

    Returns:
        Redirige a /descargar/<archivo.imscc> con flash de éxito
        o a index con flash de error.
    """
    # Validar plan_id contra traversal
    if ".." in plan_id or "/" in plan_id:
        flash("plan_id inválido.", "error")
        return redirect(url_for("index"))

    # Buscar plan
    planes_dir = OUTPUT_DIR / "planes"
    plan_path = (planes_dir / plan_id).with_suffix(".json")

    # Validar que está dentro de OUTPUT_DIR
    try:
        plan_path = plan_path.resolve()
        if not str(plan_path).startswith(str((OUTPUT_DIR / "planes").resolve())):
            flash("Acceso denegado.", "error")
            return redirect(url_for("index"))
    except (OSError, ValueError):
        flash("plan_id inválido.", "error")
        return redirect(url_for("index"))

    if not plan_path.exists():
        flash("Plan no encontrado.", "error")
        return redirect(url_for("index"))

    # Leer plan editado
    try:
        with open(plan_path, "r", encoding="utf-8") as f:
            plan_dict = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        flash(f"Error leyendo plan: {e}", "error")
        return redirect(url_for("index"))

    # Reconstruir CourseSpec
    spec, errores = _plan_dict_a_coursespec(plan_dict)
    if errores:
        flash("Error reconstruyendo especificación: " + "; ".join(errores),
              "error")
        return redirect(url_for("index"))

    # Validar que no hay bloqueantes
    bloqueantes = [s for i in spec.todos_los_items() for s in i.issues
                   if s.severidad == Severidad.BLOQUEANTE]
    bloqueantes += [s for s in spec.issues
                    if s.severidad == Severidad.BLOQUEANTE]

    if bloqueantes:
        flash(f"No se generó el paquete: hay {len(bloqueantes)} problemas "
              "bloqueantes.", "error")
        # Redirigir a editar para que vea los problemas
        return redirect(url_for("editar_plan", plan_id=plan_id))

    # Extraer contenido (buscar archivos originales si existen)
    # Nota: El plan editado no cambia las rutas de archivos fuente,
    # así que buscamos media en los directorios conocidos.
    try:
        media = {}
        # Intentar extraer si hay carpeta_origen en el plan
        if plan_dict.get("carpeta_origen"):
            carpeta = Path(plan_dict["carpeta_origen"])
            if carpeta.exists():
                media = extraer_contenido(spec)
    except Exception as e:
        # Si no hay media, continuamos igual (puede ser plan solo con cambios)
        media = {}

    # Generar IMSCC
    try:
        from maquetador.build.imscc_builder import generar_imscc
        salida = generar_imscc(spec, media, OUTPUT_DIR)
    except Exception as e:
        flash(f"Error generando el paquete: {e}", "error")
        return redirect(url_for("index"))

    # Guardar plan nuevamente (por si acaso)
    guardar_plan(spec, OUTPUT_DIR / "planes")

    flash(f"✅ Paquete regenerado: {salida.name} — descargalo con el botón de abajo.",
          "ok")
    return redirect(url_for("descargar", nombre=salida.name))


if __name__ == "__main__":
    import os
    (BASE_DIR / "cursos_subidos").mkdir(exist_ok=True)
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)),
            debug=False)
