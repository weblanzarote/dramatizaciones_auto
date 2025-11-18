"""
Composición de video con MoviePy: Ken Burns, ajustes, concatenación.
"""
import hashlib
import random
from typing import Tuple

import moviepy.video.fx.all as vfx
from moviepy.editor import (
    ImageClip, VideoFileClip, ColorClip, CompositeVideoClip,
    concatenate_videoclips
)

from ..config.settings import VIDEO_EXTS


def fit_to_canvas(clip, W: int, H: int, fit: str, bg_color):
    """
    Ajusta un clip (imagen o video) al canvas con el modo especificado.

    Args:
        clip: Clip de MoviePy (ImageClip o VideoFileClip)
        W: Ancho del canvas
        H: Alto del canvas
        fit: Modo de ajuste ("contain" o "cover")
        bg_color: Color de fondo para letterbox

    Returns:
        Clip ajustado al canvas
    """
    ar_clip = clip.h / clip.w
    ar_canvas = H / W

    if fit == "contain":
        resized = clip.resize(
            height=H if ar_clip >= ar_canvas else None,
            width=W if ar_clip < ar_canvas else None
        ).set_position(("center", "center"))
        bg = ColorClip(size=(W, H), color=bg_color, duration=clip.duration)
        return CompositeVideoClip([bg, resized]).set_duration(clip.duration)
    else:  # cover
        scale = max(W / clip.w, H / clip.h)
        return clip.resize(scale).crop(
            x_center=(clip.w * scale) / 2,
            y_center=(clip.h * scale) / 2,
            width=W,
            height=H
        ).set_duration(clip.duration)


def ensure_duration(clip, dur: float, mode: str, W: int = None, H: int = None, bg_color=(0, 0, 0)):
    """
    Asegura que un clip tenga una duración específica.

    Args:
        clip: Clip de video
        dur: Duración deseada en segundos
        mode: Modo de extensión ("loop", "freeze", "slow", "black")
        W, H: Dimensiones del canvas (requeridas para mode="black")
        bg_color: Color de fondo

    Returns:
        Clip con la duración ajustada
    """
    # Tolerancia para no disparar "loop" por microdiferencias
    if clip.duration >= dur - 1e-3:
        return clip.subclip(0, dur)

    pad = dur - clip.duration

    if mode == "loop":
        return clip.fx(vfx.loop, duration=dur)
    elif mode == "freeze":
        last = clip.to_ImageClip(
            t=max(0, clip.duration - 1.0 / max(1, getattr(clip, "fps", 25)))
        ).set_duration(pad)
        return concatenate_videoclips([clip, last])
    elif mode == "slow":
        # Opción A: pedir duración final directamente
        try:
            return clip.fx(vfx.speedx, final_duration=dur)
        except TypeError:
            # Opción B (fallback): factor explícito
            factor = clip.duration / float(dur) if dur > 0 else 1.0
            return clip.fx(vfx.speedx, factor=factor)
    else:  # "black"
        black = ColorClip(size=(W, H), color=bg_color, duration=pad)
        return concatenate_videoclips([clip, black])


def apply_ken_burns(img_clip, W: int, H: int, dur: float, args, key: str = ""):
    """
    Aplica efecto Ken Burns (zoom + pan) a un clip de imagen.

    Args:
        img_clip: ImageClip o VideoFileClip
        W, H: Dimensiones del canvas
        dur: Duración del efecto
        args: Argumentos con configuración (kenburns, kb_zoom, kb_pan, kb_seed)
        key: Key para generar seed si kb_pan es "random"

    Returns:
        CompositeVideoClip con el efecto aplicado
    """
    img_clip = img_clip.set_duration(dur)

    if args.kenburns == "none":
        return img_clip.set_duration(dur)

    # 1. Escala inicial: Asegura que la imagen siempre cubra el cuadro (W,H)
    base_scale = max(W / img_clip.w, H / img_clip.h)
    base_clip = img_clip.resize(base_scale)

    # 2. Zoom dinámico
    if args.kenburns == "in":
        zoom_func = lambda t: 1 + args.kb_zoom * (t / dur)
    elif args.kenburns == "out":
        zoom_func = lambda t: (1 + args.kb_zoom) - args.kb_zoom * (t / dur)
    else:  # 'none'
        zoom_func = lambda t: 1

    animated_clip = base_clip.resize(zoom_func)

    # 3. Paneo dinámico
    def pos_func(t):
        current_zoom = zoom_func(t)
        w = base_clip.w * current_zoom
        h = base_clip.h * current_zoom

        move_w = w - W
        move_h = h - H

        pan_map = {
            "center": ((0.5, 0.5), (0.5, 0.5)),
            "tl2br": ((0.0, 0.0), (1.0, 1.0)),
            "tr2bl": ((1.0, 0.0), (0.0, 1.0)),
            "bl2tr": ((0.0, 1.0), (1.0, 0.0)),
            "br2tl": ((1.0, 1.0), (0.0, 0.0)),
        }

        if args.kb_pan in pan_map:
            start_rel, end_rel = pan_map[args.kb_pan]
        else:  # random
            seed = args.kb_seed or (int(hashlib.sha1((key or "").encode("utf-8")).hexdigest(), 16) % (2**32 - 1))
            rnd = random.Random(seed)
            start_rel = (rnd.uniform(0, 1), rnd.uniform(0, 1))
            end_rel = (rnd.uniform(0, 1), rnd.uniform(0, 1))

        p = t / dur
        rel_x = start_rel[0] * (1 - p) + end_rel[0] * p
        rel_y = start_rel[1] * (1 - p) + end_rel[1] * p

        return (-move_w * rel_x, -move_h * rel_y)

    positioned_clip = animated_clip.set_position(pos_func)

    return CompositeVideoClip([positioned_clip], size=(W, H)).set_duration(dur)


def parse_resolution(res_str: str) -> Tuple[int, int]:
    """
    Parsea una cadena de resolución en formato WxH.

    Args:
        res_str: String como "1920x1080"

    Returns:
        Tupla (ancho, alto)
    """
    import re
    m = re.match(r"^\s*(\d+)\s*[xX]\s*(\d+)\s*$", res_str)
    if not m:
        raise ValueError("resolución debe tener formato WxH, p.ej. 1920x1080")
    return int(m.group(1)), int(m.group(2))
