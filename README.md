# 🎓 Generador IMSCC para Canvas LMS

**Automatización de maquetación de aulas virtuales** — Genera paquetes `.imscc` (Common Cartridge 1.1) 100% compatibles con Canvas LMS a partir de archivos DOCX y hojas de cálculo XLSX.

---

## 📋 Descripción

Este proyecto automatiza el proceso de maquetación de aulas virtuales en Canvas LMS. Los asesores pedagógicos y docentes generan contenidos en documentos DOCX e instrucciones de estructura en archivos XLSX. El script toma esos archivos y produce un paquete `.imscc` importable directamente en Canvas, replicando el diseño institucional.

## 🔧 Requisitos

- **Python** 3.10 o superior
- **pip** para instalar dependencias

## 🚀 Instalación

```bash
# 1. Clonar o descargar el proyecto
cd "Proyecto automatización de Maquetación"

# 2. Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt
```

## 📂 Estructura de Archivos de Entrada

Coloca tus archivos en la carpeta `input/`:

```
input/
├── estructura.xlsx         # Hoja de cálculo con la estructura del curso
├── bienvenida.docx         # Archivos DOCX con contenido pedagógico
├── tema1_introduccion.docx
├── actividad1.docx
└── media/                  # Carpeta con archivos multimedia
    ├── banner_curso.png
    ├── video_intro.mp4
    └── guia_actividad.pdf
```

### Formato del archivo `estructura.xlsx`

| modulo | orden | tipo | titulo | archivo_docx | archivo_media | plantilla | url | notas |
|--------|-------|------|--------|--------------|---------------|-----------|-----|-------|
| Módulo 1: Introducción | 1 | pagina | Bienvenida al curso | bienvenida.docx | banner_curso.png | base_page | | |
| Módulo 1: Introducción | 2 | pagina | Tema 1: Conceptos | tema1.docx | | content_block | | |
| Módulo 1: Introducción | 3 | pagina | Actividad 1 | actividad1.docx | guia.pdf | activity_block | | |
| Módulo 1: Introducción | 4 | url_externa | Video complementario | | | | https://youtube.com/... | |
| Módulo 2: Desarrollo | 1 | pagina | Tema 2 | tema2.docx | | content_block | | |

#### Columnas

| Columna | Obligatoria | Descripción |
|---------|:-----------:|-------------|
| `modulo` | ✅ | Nombre del módulo. Ítems con el mismo nombre se agrupan. |
| `orden` | ✅ | Número de orden dentro del módulo. |
| `tipo` | ✅ | Tipo de contenido: `pagina`, `archivo`, `url_externa`, `subencabezado`. |
| `titulo` | ✅ | Título que se mostrará en Canvas. |
| `archivo_docx` | ❌ | Nombre del archivo .docx con el contenido (debe estar en `input/`). |
| `archivo_media` | ❌ | Archivos multimedia asociados, separados por `;`. |
| `plantilla` | ❌ | Plantilla de diseño: `base_page`, `content_block`, `activity_block`. |
| `url` | ❌ | URL externa (obligatoria si `tipo` = `url_externa`). |
| `notas` | ❌ | Notas internas para el equipo. |

## 💻 Uso

### Ejecución básica

```bash
python main.py
```

### Con parámetros

```bash
# Especificar título del curso
python main.py --titulo "Fundamentos de Programación 2025"

# Usar archivos de entrada desde otra carpeta
python main.py --input ./mis_archivos --output ./paquetes

# Especificar nombre del archivo de salida
python main.py --nombre-archivo mi_curso_final

# Modo detallado (debug)
python main.py --verbose
```

### Probar con datos de ejemplo

```bash
python create_example.py    # Genera archivos de ejemplo en input/
python main.py --titulo "Curso de Ejemplo"
```

## 📦 Importar en Canvas LMS

1. Accede a tu curso en Canvas
2. Ve a **Configuración** → **Importar contenido del curso**
3. Selecciona **Common Cartridge 1.x Package**
4. Sube el archivo `.imscc` generado en `output/`
5. Selecciona **Todo el contenido** o elige contenido específico
6. Haz clic en **Importar**

## 🎨 Plantillas de Diseño

El proyecto incluye 3 plantillas institucionales:

| Plantilla | Uso | Descripción |
|-----------|-----|-------------|
| `base_page` | General | Página estándar con cabecera azul gradiente |
| `content_block` | Teoría/Lectura | Bloque de contenido con ícono y caja informativa |
| `activity_block` | Actividades | Diseño naranja para tareas y ejercicios |
| `module_header` | Overview | Página de presentación del módulo con índice |

### Personalizar colores

Edita la paleta en `config.py`:

```python
COLORS = {
    "primary": "#1a365d",         # Color principal
    "primary_light": "#2b6cb0",   # Color principal claro
    "accent": "#dd6b20",          # Color de acento
    # ... más colores
}
```

## 🏗️ Arquitectura

```
├── main.py                 # CLI principal
├── config.py               # Configuración y constantes
├── readers/                # Lectura de archivos de entrada
│   ├── sheets_reader.py    # Lector de XLSX
│   ├── docx_reader.py      # Lector de DOCX
│   └── media_collector.py  # Recolector de multimedia
├── processors/             # Procesamiento y transformación
│   ├── html_renderer.py    # Renderizado HTML con diseño
│   └── structure_builder.py # Constructor de estructura
├── builders/               # Generación del paquete IMSCC
│   ├── manifest_builder.py # Generador de imsmanifest.xml
│   ├── page_builder.py     # Generador de archivos HTML
│   └── package_builder.py  # Empaquetador .imscc (ZIP)
├── templates/              # Plantillas HTML institucionales
└── input/                  # Archivos de entrada del usuario
```

## 📄 Licencia

Uso interno institucional.
