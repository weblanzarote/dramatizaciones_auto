"""
Parsing de scripts de dramatización con etiquetas [SPEAKER] y [imagen:X.png].
"""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from ..config.settings import META_PREFIXES, IMAGE_PREFIX


@dataclass
class Turn:
    """Representa un bloque de diálogo/narración en el guion."""
    index: int
    speaker: str
    text: str
    image: Optional[str]  # nombre de archivo de imagen asociado (puede ser None)


def _looks_meta(head: str) -> bool:
    """Verifica si una etiqueta es metadata (SFX, AMBIENTE, etc.)"""
    head_up = head.upper()
    return any(head_up.startswith(pfx) for pfx in META_PREFIXES)


def _normalize_speaker(tag_inside: str) -> str:
    """
    Normaliza una etiqueta de speaker.

    Args:
        tag_inside: Contenido dentro de los corchetes [...]

    Returns:
        Nombre del speaker en mayúsculas, o "" si es metadata
    """
    t = tag_inside.strip()
    t_dash = t.replace("–", "-").replace("—", "-")

    if ":" in t_dash:
        head = t_dash.split(":", 1)[0].strip()
        if _looks_meta(head) or head.upper().startswith(IMAGE_PREFIX):
            return ""  # no cambia hablante

    t_main = t_dash.split("-", 1)[0].strip()
    if _looks_meta(t_main):
        return ""

    return t_main.upper()


def _extract_image(tag_inside: str) -> Optional[str]:
    """
    Extrae el nombre de archivo de imagen de una etiqueta [imagen:...].

    Acepta '1png' y lo convierte en '1.png'.
    Si el valor es 'clear'/'none'/'off'/'0'/'null' -> devuelve '' para limpiar.

    Args:
        tag_inside: Contenido dentro de los corchetes [...]

    Returns:
        Nombre del archivo de imagen, "" para limpiar, o None si no es etiqueta de imagen
    """
    t = tag_inside.strip()
    t_dash = t.replace("–", "-").replace("—", "-")

    if ":" not in t_dash:
        return None

    head, val = t_dash.split(":", 1)
    if head.strip().upper().startswith(IMAGE_PREFIX):
        val = val.strip()
        if not val:
            # si escribes [imagen:] lo ignoramos (no cambia nada)
            return None

        if val.lower() in {"clear", "none", "off", "0", "null"}:
            return ""  # señal para limpiar imagen activa

        # normaliza 1png -> 1.png
        if "." not in val and len(val) > 3:
            maybe_ext = val[-3:].lower()
            if maybe_ext in {"png", "jpg", "peg"}:
                val = val[:-3] + "." + maybe_ext

        if val.lower().endswith(".peg"):
            val = val[:-4] + ".jpeg"

        return val

    return None


def parse_script_with_images(path: Path) -> List[Turn]:
    """
    Parsea un script con etiquetas [SPEAKER] e [imagen:archivo].

    Reglas:
    - [SPEAKER] fija el hablante (etiqueta en línea sola).
    - [imagen:archivo] ACTIVA esa imagen para ESTE y LOS SIGUIENTES bloques hasta que se cambie.
    - Puedes limpiar con [imagen:clear] / [imagen:none] / [imagen:off].
    - Tags meta tipo [Ambiente: ..] se ignoran.
    - Un bloque = líneas de texto hasta el siguiente [SPEAKER].
    - [CIERRE] añade un bloque especial de cierre.

    Args:
        path: Ruta al archivo de script (.txt)

    Returns:
        Lista de objetos Turn con los bloques parseados
    """
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    turns: List[Turn] = []
    tag_re = re.compile(r"^\s*\[(.+?)\]\s*$")

    current_speaker: Optional[str] = None
    active_image: Optional[str] = None  # <- IMAGEN STICKY
    buffer: List[str] = []
    idx = 0
    last_speaker_before_meta: Optional[str] = None

    def flush():
        nonlocal idx, buffer, current_speaker
        text = "\n".join(buffer).strip()
        if current_speaker and text:
            # usamos SIEMPRE la imagen ACTIVA (no se limpia al publicar el bloque)
            turns.append(Turn(index=idx, speaker=current_speaker, text=text, image=active_image))
            idx += 1
            buffer = []
        else:
            buffer = []

    for raw in lines:
        m = tag_re.match(raw)
        if m:
            inside = m.group(1).strip()

            # ¿cierre?
            if inside.upper() == "CIERRE":
                # cierra cualquier bloque pendiente antes de insertar el cierre
                flush()
                turns.append(Turn(index=idx, speaker="__CIERRE__", text="", image="__CIERRE__"))
                idx += 1
                # no tocamos current_speaker ni active_image
                continue

            # ¿imagen?
            img = _extract_image(inside)
            if img is not None:
                if img == "":
                    active_image = None        # limpiar imagen activa
                else:
                    active_image = img        # activar nueva imagen
                if current_speaker:
                    last_speaker_before_meta = current_speaker
                continue

            # ¿speaker?
            norm = _normalize_speaker(inside)
            if norm:
                flush()
                current_speaker = norm
                last_speaker_before_meta = norm
            else:
                if current_speaker:
                    last_speaker_before_meta = current_speaker
                continue
        else:
            if current_speaker is None and last_speaker_before_meta:
                current_speaker = last_speaker_before_meta
            buffer.append(raw)

    flush()
    return turns
