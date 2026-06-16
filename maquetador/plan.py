# -*- coding: utf-8 -*-
"""Plan de maquetación: el resultado del análisis, listo para revisión humana.

Se materializa como JSON (para la futura web y para regenerar) y como texto
legible (para revisar rápido en consola). El maquetador revisa/ajusta el plan
ANTES de generar el .imscc — el sistema propone, la persona decide.
"""

import json
from datetime import datetime
from pathlib import Path

from maquetador.models import CourseSpec, Severidad, TipoItem

TEMAS_DISPONIBLES = ("educacion", "posgrado")

_ICONO_TIPO = {
    TipoItem.PAGINA: "📄", TipoItem.INTRO_MODULO: "📝", TipoItem.FORO: "💬",
    TipoItem.VIDEO: "🎬", TipoItem.TAREA: "📌", TipoItem.EVALUACION: "✅",
    TipoItem.ARCHIVO: "📎", TipoItem.IMAGEN: "🖼", TipoItem.OTRO: "❔",
}


def _fmt_fuente(item) -> str:
    f = item.fuente
    if f.archivo is None:
        return "(sin fuente)"
    txt = f.archivo.name
    if f.seccion:
        txt += f" → sección {f.seccion}"
    txt += f"  [conf. {f.confianza:.0%}]"
    return txt


def generar_reporte_texto(spec: CourseSpec) -> str:
    L = []
    L.append("=" * 78)
    L.append(f"PLAN DE MAQUETACIÓN — {spec.nombre}")
    if spec.codigo:
        L.append(f"Código: {spec.codigo}")
    if spec.docentes:
        L.append(f"Docente(s): {', '.join(spec.docentes)}")
    L.append(f"Aula base: {spec.tema or '⚠ A ELEGIR (educacion | posgrado)'}")
    L.append(f"Carpeta: {spec.carpeta_origen}")
    L.append("=" * 78)

    def _items(items, indent="  "):
        for it in items:
            L.append(f"{indent}{_ICONO_TIPO.get(it.tipo, '?')} {it.titulo[:70]}")
            L.append(f"{indent}   fuente: {_fmt_fuente(it)}")
            for iss in it.issues:
                marca = {"info": "ℹ", "aviso": "⚠", "bloqueante": "⛔"}[iss.severidad.value]
                L.append(f"{indent}   {marca} {iss.mensaje}")

    if spec.items_inicio:
        L.append("\n— PÁGINA DE INICIO / PROGRAMA —")
        _items(spec.items_inicio)

    for mod in spec.modulos:
        L.append(f"\n— MÓDULO {mod.numero}: {mod.titulo or '(sin título)'} —")
        _items(mod.items)

    if spec.afi:
        L.append("\n— ACTIVIDAD FINAL INTEGRADORA —")
        _items(spec.afi)

    if spec.issues:
        L.append("\n— ISSUES GENERALES —")
        for iss in spec.issues:
            marca = {"info": "ℹ", "aviso": "⚠", "bloqueante": "⛔"}[iss.severidad.value]
            ctx = f" [{iss.contexto}]" if iss.contexto else ""
            L.append(f"  {marca}{ctx} {iss.mensaje}")

    # Resumen
    todos = list(spec.todos_los_items())
    con_fuente = sum(1 for i in todos if i.fuente.archivo)
    bloqueantes = sum(1 for i in todos for s in i.issues
                      if s.severidad == Severidad.BLOQUEANTE)
    bloqueantes += sum(1 for s in spec.issues if s.severidad == Severidad.BLOQUEANTE)
    avisos = sum(1 for i in todos for s in i.issues if s.severidad == Severidad.AVISO)
    avisos += sum(1 for s in spec.issues if s.severidad == Severidad.AVISO)
    L.append("\n" + "-" * 78)
    L.append(f"RESUMEN: {len(todos)} ítems | {con_fuente} con fuente asignada | "
             f"{avisos} avisos | {bloqueantes} bloqueantes")
    listo = bloqueantes == 0 and spec.tema
    L.append("ESTADO: " + ("✅ listo para generar (revisar avisos)" if listo
                           else "⛔ requiere intervención antes de generar"))
    L.append("-" * 78)
    return "\n".join(L)


def guardar_plan(spec: CourseSpec, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = spec.to_dict()
    data["_generado"] = datetime.now().isoformat(timespec="seconds")
    data["_version_formato"] = 1
    nombre = (spec.codigo or spec.nombre)[:60].strip().replace(" ", "_")
    path = output_dir / f"plan_{nombre}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    return path
