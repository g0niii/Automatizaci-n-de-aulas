"""
Recolector de archivos multimedia.
Inventaría y valida todos los archivos multimedia disponibles en la carpeta
input/media/ y los referenciados en la estructura del curso.
"""

import logging
import shutil
from pathlib import Path
from dataclasses import dataclass, field

from config import (
    MEDIA_DIR,
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    AUDIO_EXTENSIONS,
    DOCUMENT_EXTENSIONS,
    ALL_MEDIA_EXTENSIONS,
)

logger = logging.getLogger(__name__)


@dataclass
class MediaFile:
    """Representa un archivo multimedia inventariado."""
    filename: str           # Nombre del archivo
    source_path: Path       # Ruta absoluta al archivo original
    media_type: str         # "image", "video", "audio", "document"
    size_bytes: int         # Tamaño en bytes
    extension: str          # Extensión del archivo


@dataclass
class MediaInventory:
    """Inventario completo de archivos multimedia disponibles."""
    files: dict[str, MediaFile] = field(default_factory=dict)  # nombre -> MediaFile
    missing: list[str] = field(default_factory=list)           # archivos referenciados pero no encontrados
    total_size: int = 0


def _classify_media(ext: str) -> str:
    """Clasifica un archivo multimedia por su extensión."""
    ext_lower = ext.lower()
    if ext_lower in IMAGE_EXTENSIONS:
        return "image"
    elif ext_lower in VIDEO_EXTENSIONS:
        return "video"
    elif ext_lower in AUDIO_EXTENSIONS:
        return "audio"
    elif ext_lower in DOCUMENT_EXTENSIONS:
        return "document"
    return "unknown"


def collect_media(
    media_dir: Path = MEDIA_DIR,
    referenced_files: list[str] | None = None,
) -> MediaInventory:
    """
    Inventaría todos los archivos multimedia en la carpeta dada.

    Args:
        media_dir: Directorio donde buscar archivos multimedia.
        referenced_files: Lista de nombres de archivo referenciados en la
                         estructura del curso (para validar existencia).

    Returns:
        MediaInventory con los archivos encontrados y los faltantes.
    """
    inventory = MediaInventory()

    if not media_dir.exists():
        logger.warning(f"La carpeta de medios no existe: {media_dir}")
        media_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"  Creada carpeta: {media_dir}")
        if referenced_files:
            inventory.missing = list(referenced_files)
        return inventory

    logger.info(f"Recolectando multimedia desde: {media_dir}")

    # Escanear todos los archivos en la carpeta de medios (recursivo)
    for filepath in sorted(media_dir.rglob("*")):
        if not filepath.is_file():
            continue

        ext = filepath.suffix.lower()
        if ext not in ALL_MEDIA_EXTENSIONS:
            logger.debug(f"  Ignorado (extensión no soportada): {filepath.name}")
            continue

        media_type = _classify_media(ext)
        size = filepath.stat().st_size

        media_file = MediaFile(
            filename=filepath.name,
            source_path=filepath,
            media_type=media_type,
            size_bytes=size,
            extension=ext,
        )

        inventory.files[filepath.name] = media_file
        inventory.total_size += size

        logger.debug(f"  Encontrado [{media_type}]: {filepath.name} ({size:,} bytes)")

    # Verificar archivos referenciados
    if referenced_files:
        for ref_file in referenced_files:
            if ref_file and ref_file not in inventory.files:
                inventory.missing.append(ref_file)
                logger.warning(f"  ⚠ Archivo referenciado no encontrado: {ref_file}")

    logger.info(
        f"Multimedia: {len(inventory.files)} archivos encontrados "
        f"({inventory.total_size / 1024 / 1024:.1f} MB), "
        f"{len(inventory.missing)} faltantes."
    )

    return inventory
