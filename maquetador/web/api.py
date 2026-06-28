# -*- coding: utf-8 -*-
"""API de maquetación — manejo de cambios en el plan."""

from typing import Dict, Any, List, Tuple


def _diff_recursivo(orig: Any, editado: Any, ruta: str = "") -> List[Dict[str, Any]]:
    """Compara orig vs editado recursivamente y retorna lista de cambios.

    Cada cambio es: {"ruta": str, "anterior": value, "nuevo": value}
    """
    cambios = []

    # Si son del mismo tipo, comparar contenido
    if type(orig) != type(editado):
        cambios.append({
            "ruta": ruta or "raiz",
            "anterior": orig,
            "nuevo": editado
        })
        return cambios

    # Dicts — comparar claves y valores
    if isinstance(orig, dict):
        todas_claves = set(orig.keys()) | set(editado.keys())
        for clave in todas_claves:
            ruta_nueva = f"{ruta}.{clave}" if ruta else clave
            if clave not in orig:
                cambios.append({
                    "ruta": ruta_nueva,
                    "anterior": None,
                    "nuevo": editado[clave]
                })
            elif clave not in editado:
                cambios.append({
                    "ruta": ruta_nueva,
                    "anterior": orig[clave],
                    "nuevo": None
                })
            else:
                cambios.extend(_diff_recursivo(orig[clave], editado[clave], ruta_nueva))

    # Listas — comparar elemento a elemento
    elif isinstance(orig, list):
        for i, (o, e) in enumerate(zip(orig, editado)):
            ruta_nueva = f"{ruta}[{i}]"
            cambios.extend(_diff_recursivo(o, e, ruta_nueva))
        # Si cambian de tamaño
        if len(orig) != len(editado):
            cambios.append({
                "ruta": f"{ruta}.length",
                "anterior": len(orig),
                "nuevo": len(editado)
            })

    # Valores primitivos — comparar directamente
    elif orig != editado:
        cambios.append({
            "ruta": ruta or "raiz",
            "anterior": orig,
            "nuevo": editado
        })

    return cambios


def _validar_estructura_plan(plan: Dict[str, Any]) -> List[str]:
    """Valida que el plan tenga la estructura mínima esperada.

    Retorna lista de errores (vacía si es válido).
    """
    errores = []

    # Claves obligatorias
    if not isinstance(plan, dict):
        errores.append("Plan debe ser un diccionario")
        return errores

    claves_requeridas = {"nombre", "modulos", "items_inicio", "afi"}
    faltantes = claves_requeridas - set(plan.keys())
    if faltantes:
        errores.append(f"Faltan claves requeridas: {', '.join(sorted(faltantes))}")

    # Modulos debe ser lista
    if "modulos" in plan:
        if not isinstance(plan["modulos"], list):
            errores.append("'modulos' debe ser una lista")
        else:
            for i, mod in enumerate(plan["modulos"]):
                if not isinstance(mod, dict):
                    errores.append(f"Módulo {i} no es un diccionario")
                elif "numero" not in mod or "items" not in mod:
                    errores.append(f"Módulo {i} falta 'numero' o 'items'")
                elif not isinstance(mod["items"], list):
                    errores.append(f"Módulo {i}: 'items' no es una lista")
                else:
                    for j, item in enumerate(mod["items"]):
                        if not isinstance(item, dict):
                            errores.append(f"Módulo {i}, Item {j} no es diccionario")
                        elif "titulo" not in item or "tipo" not in item:
                            errores.append(f"Módulo {i}, Item {j} falta 'titulo' o 'tipo'")

    # items_inicio debe ser lista
    if "items_inicio" in plan:
        if not isinstance(plan["items_inicio"], list):
            errores.append("'items_inicio' debe ser una lista")

    # afi debe ser lista
    if "afi" in plan:
        if not isinstance(plan["afi"], list):
            errores.append("'afi' debe ser una lista")

    return errores


def guardar_cambios_plan(plan_original: Dict[str, Any], plan_editado: Dict[str, Any]) -> Dict[str, Any]:
    """Compara plan original vs editado.

    Args:
        plan_original: Plan cargado desde JSON (con estructura CourseSpec.to_dict())
        plan_editado: Plan editado por el usuario (mismo formato)

    Returns:
        {
            "exito": bool,
            "cambios": [{"ruta": str, "anterior": Any, "nuevo": Any}, ...],
            "errores": [str, ...]
        }
    """
    # Validar que el plan editado tenga estructura válida
    errores = _validar_estructura_plan(plan_editado)
    if errores:
        return {
            "exito": False,
            "cambios": [],
            "errores": errores
        }

    # Diff profundo
    cambios = _diff_recursivo(plan_original, plan_editado)

    return {
        "exito": True,
        "cambios": cambios,
        "errores": []
    }
