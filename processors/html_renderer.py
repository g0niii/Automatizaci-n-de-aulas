"""
Renderizador HTML con diseño institucional.
Toma contenido extraído de DOCX y lo envuelve en las plantillas HTML
del diseño institucional, con estilos inline compatibles con Canvas.
"""

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from config import TEMPLATES_DIR, COLORS, FONTS
from processors.content_block_processor import process_content_blocks

logger = logging.getLogger(__name__)


class HtmlRenderer:
    """
    Motor de renderizado HTML que aplica el diseño institucional
    al contenido extraído de los documentos DOCX.

    Canvas LMS filtra tags <style> y <link>, por lo que todos los estilos
    se aplican como inline CSS directamente en los elementos HTML.
    """

    def __init__(self, templates_dir: Path = TEMPLATES_DIR, theme: str = "educacion"):
        """
        Inicializa el renderizador con el directorio de plantillas y el tema.

        Args:
            templates_dir: Ruta al directorio con las plantillas Jinja2.
            theme: Nombre del tema ('educacion' o 'posgrado').
        """
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        self.theme = theme if theme in COLORS else "educacion"
        
        # Variables globales disponibles en todas las plantillas
        self.env.globals["colors"] = COLORS[self.theme]
        self.env.globals["theme_name"] = self.theme
        self.env.globals["fonts"] = FONTS

        logger.info(f"HtmlRenderer inicializado con plantillas desde: {templates_dir}")

    def render_page(
        self,
        template_name: str,
        titulo: str,
        contenido_html: str,
        modulo_nombre: str = "",
        numero_pagina: int = 1,
        media_files: list[dict] | None = None,
        extra_context: dict | None = None,
    ) -> str:
        """
        Renderiza una página completa con el diseño institucional.

        Args:
            template_name: Nombre de la plantilla a usar (sin extensión).
            titulo: Título de la página.
            contenido_html: Contenido HTML del cuerpo (ya convertido desde DOCX).
            modulo_nombre: Nombre del módulo al que pertenece.
            numero_pagina: Número de orden de la página.
            media_files: Lista de dicts con info de archivos multimedia.
            extra_context: Variables adicionales para la plantilla.

        Returns:
            HTML completo de la página con estilos inline.
        """
        template_file = f"{template_name}.html"

        try:
            template = self.env.get_template(template_file)
        except Exception:
            logger.warning(
                f"Plantilla '{template_file}' no encontrada, usando 'base_page.html'"
            )
            template = self.env.get_template("base_page.html")

        context = {
            "titulo": titulo,
            "contenido": contenido_html,
            "modulo_nombre": modulo_nombre,
            "numero_pagina": numero_pagina,
            "media_files": media_files or [],
        }

        if extra_context:
            context.update(extra_context)

        # Procesar bloques de contenido (CIDILABS) si la plantilla lo sugiere
        if template_name in ["cidilabs_page", "home_page"]:
            context["contenido"] = process_content_blocks(context["contenido"], self.env.globals["colors"])

        rendered = template.render(**context)

        logger.debug(f"Página renderizada: '{titulo}' ({len(rendered)} chars)")
        return rendered

    def render_module_overview(
        self,
        modulo_nombre: str,
        items_titulos: list[str],
        descripcion: str = "",
    ) -> str:
        """
        Renderiza una página de presentación/overview de un módulo.

        Args:
            modulo_nombre: Nombre del módulo.
            items_titulos: Lista de títulos de los ítems del módulo.
            descripcion: Descripción opcional del módulo.

        Returns:
            HTML del overview del módulo.
        """
        try:
            template = self.env.get_template("module_header.html")
        except Exception:
            template = self.env.get_template("base_page.html")

        context = {
            "titulo": modulo_nombre,
            "contenido": descripcion,
            "modulo_nombre": modulo_nombre,
            "items_titulos": items_titulos,
        }

        return template.render(**context)
