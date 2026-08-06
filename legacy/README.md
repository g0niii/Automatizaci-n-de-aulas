# legacy/

Código de la **versión anterior** del proyecto (previa al paquete `maquetador/`).

**No lo usa el tool actual** — se conserva archivado por referencia histórica.
Confirmado que ni `maquetador/`, ni `tests/`, ni `processors/cidilabs_builder.py`
importan nada de acá.

Contenido:

- `main*.py`, `analizar_casos.py`, `analyze_bases.py`, `create_example.py`,
  `config.py` — entradas y experimentos por asignatura (Feldman, Conti, UCC…).
- `builders/`, `readers/`, `templates/`, `input/` — estructura vieja de generación.
- `processors/` — módulos viejos de procesamiento (el único vivo,
  `cidilabs_builder.py`, quedó en `../processors/`).
- `elementos_viejos/` — planillas y DOCX de prueba de cursos viejos.

Sus imports pueden estar rotos (apuntan a rutas de la estructura vieja): es código
archivado, no ejecutable tal cual.
