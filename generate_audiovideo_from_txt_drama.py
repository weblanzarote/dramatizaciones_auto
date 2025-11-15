#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Genera audios con ElevenLabs a partir de un guion con [ETIQUETAS] y crea un VIDEO .mp4
sincronizando cada bloque con su [imagen:archivo].

Requisitos:
  pip install requests pydub moviepy
  (y tener ffmpeg instalado y en PATH)

Ejemplo:
  python generate_audiovideo_from_txt_drama.py "dracula_1.txt" \
      --outdir "./Out/Dracula_P1" \
      --images-dir "./images" \
      --model "eleven_multilingual_v2" \
      --ext ".mp3" \
      --video-out "./Out/Dracula_P1_video.mp4" \
      --resolution "1920x1080" \
      --fps 30 \
      --silence-ms 250 \
      --pad-ms 200

Notas:
- [imagen:2png] y [imagen:2.png] son válidos. Si no hay imagen, usa un color de fondo.
- Las etiquetas meta como [Ambiente: ...] se ignoran (no cambian el hablante).
"""
import argparse
import json
import os
import re
import sys
import time
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import timedelta

import requests

# Audio merge helper
try:
    from pydub import AudioSegment
except Exception:
    AudioSegment = None  # solo requerido si quisieras además exportar audio combinado

# Vídeo
import moviepy  # para log de versión
import moviepy.video.fx.all as vfx
from moviepy.editor import (
    ImageClip, VideoFileClip, AudioFileClip, ColorClip, CompositeVideoClip,
    concatenate_videoclips, CompositeAudioClip
)

# ================== ✨ VOCES POR PERSONAJE (ajusta a tu mapa) ✨ ==================
VOICE_SETTINGS_MAP: Dict[str, dict] = {
    "NARRADOR":           {"voice_id": "Nh2zY9kknu6z4pZy6FhD", "speed": 1.10},
    "CHICO10":            {"voice_id": "1tDEBGOo8EqEPApM49eJ", "speed": 1.03},    
    "JOVENASUSTADO":      {"voice_id": "PZasrDc3dhEdCVT9i8DU", "speed": 1.05},
    "HOMBRE25":     {"voice_id": "1MxuWc12WPRxDkgfT3kj", "speed": 1.09},    
    "HOMBRE50":       {"voice_id": "W5JElH3dK1UYYAiHH7uh", "speed": 1.11},
    "HOMBRE40":       {"voice_id": "43h7ymOnaaYdWr3dRbsS", "speed": 1.10},
    "HOMBRE30":  {"voice_id": "851ejYcv2BoNPjrkw93G", "speed": 0.98},    
    "ANCIANO":              {"voice_id": "DNllXe1qtnhKfoIT5C7O", "speed": 1.05},
    "CHICA12":              {"voice_id": "iKQ9dQi0t2d3zpB6iYav", "speed": 1.05},    
    "MUJER20":     {"voice_id": "Ir1QNHvhaJXbAGhT50w3", "speed": 1.04},    
    "MUJER30":             {"voice_id": "UOIqAnmS11Reiei1Ytkc", "speed": 1.01},
    "ANCIANA":             {"voice_id": "M9RTtrzRACmbUzsEMq8p", "speed": 1.01},
    "DUENDEMALVADO":     {"voice_id": "ZCuQxoQ9PJLqhQQnK3RJ", "speed": 1.01},    
    "MONSTER":      {"voice_id": "cPoqAvGWCPfCfyPMwe4z", "speed": 1.15},
    "MUJERASUSTADA":            {"voice_id": "ZSbzc0bfesjWLjV59rru", "speed": 1.04},
    "_default":            {"voice_id": "Nh2zY9kknu6z4pZy6FhD", "speed": 1.00},
}

# Más barato: Flash v2.5 (≈0.5 crédito/char, multilenguaje)
DEFAULT_MODEL_ID = "eleven_multilingual_v2" 
# DEFAULT_MODEL_ID = "eleven_flash_v2_5"
DEFAULT_EXT = ".mp3"
DEFAULT_ACCEPT = "audio/mpeg"
DEFAULT_VOICE_SETTINGS = {
    "stability": 0.30,
    "similarity_boost": 0.30,
    "style": 0.0,
    "use_speaker_boost": True,  # opcional; puedes dejarlo True si te gusta el timbre más “presente”
}


ELEVEN_API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY", "").strip()

META_PREFIXES = ("SFX", "AMB", "AMBIENTE", "FX", "NOTA", "MÚSICA", "MUSICA")
IMAGE_PREFIX = "IMAGEN"

@dataclass
class Turn:
    index: int
    speaker: str
    text: str
    image: Optional[str]  # nombre de archivo de imagen asociado (puede ser None)
    
def _fmt_ts(seconds: float) -> str:
    # SRT usa HH:MM:SS,mmm
    td = timedelta(seconds=max(0, seconds))
    total_ms = int(td.total_seconds() * 1000)
    hh = total_ms // 3600000
    mm = (total_ms % 3600000) // 60000
    ss = (total_ms % 60000) // 1000
    ms = total_ms % 1000
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"    
    
def _fmt_ass_ts(seconds: float) -> str:
    # ASS usa H:MM:SS.cc (centésimas)
    s = max(0.0, float(seconds))
    h = int(s // 3600); s -= h * 3600
    m = int(s // 60);   s -= m * 60
    cs = int(round(s * 100))
    ss = cs // 100
    cc = cs % 100
    return f"{h:d}:{m:02d}:{ss:02d}.{cc:02d}"

def _ass_header(w: int, h: int, args) -> str:
    # &HAABBGGRR  (AA=alpha: 00 opaco, FF transparente)
    primary   = "&H00FFFFFF&"  # Revelado (llenado \kf): blanco opaco -> lo que aparece
    secondary = "&HFFFFFFFF&"  # NO revelado: transparente -> lo que aún no debe verse
    outline   = "&H00000000&"  # Contorno/sombra: negro opaco (necesario para que se vea)
    shadow    = "&H00000000&"  # BackColour (solo útil con BorderStyle=3; lo dejamos negro)

    return (
f"[Script Info]\n"
f"ScriptType: v4.00+\n"
f"PlayResX: {w}\n"
f"PlayResY: {h}\n"
f"ScaledBorderAndShadow: yes\n"
f"\n[V4+ Styles]\n"
f"Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
f"Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
f"Alignment, MarginL, MarginR, MarginV, Encoding\n"
#             BorderStyle=1 (contorno), Outline/Shadow vienen de args
f"Style: {args.ass_style_name},{args.ass_font},{args.ass_fontsize},{primary},{secondary},{outline},{shadow},"
f"0,0,0,0,100,100,0,0,1,{args.ass_outline},{args.ass_shadow},{args.subs_align},30,30,{args.ass_margin_v},0\n"
f"\n[Events]\n"
f"Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    
    
def _tokenize_words(s: str):
    """
    Divide el texto en tokens 'tipo palabra' preservando la puntuación pegada.
    """
    return re.findall(r"\S+", s, flags=re.U)

def _word_weights(words, mode: str):
    """
    Pesa cada palabra para repartir mejor el tiempo.
    - 'uniform': todas pesan 1
    - 'length': pesa la longitud visible (sin puntuación)
    """
    if mode == "uniform":
        return [1.0] * len(words)
    out = []
    for w in words:
        visible = re.sub(r"[^\wáéíóúüñÁÉÍÓÚÜÑ0-9]", "", w, flags=re.U)
        out.append(max(1, len(visible)))
    return out
    

def clamp_speed(v: float) -> float:
    return max(0.7, min(1.2, float(v)))

def pick_voice(speaker: str) -> Tuple[str, float]:
    cfg = VOICE_SETTINGS_MAP.get(speaker.upper(), VOICE_SETTINGS_MAP["_default"])
    return cfg["voice_id"], clamp_speed(cfg.get("speed", 1.0))

def create_speech(text: str, voice_id: str, model_id: str, speed: float, accept: str, api_key: str) -> bytes:
    url = ELEVEN_API_URL.format(voice_id=voice_id)
    headers = {"Accept": accept, "Content-Type": "application/json", "xi-api-key": api_key}
    settings = dict(DEFAULT_VOICE_SETTINGS); settings["speed"] = speed
    payload = {"text": text, "model_id": model_id, "voice_settings": settings}
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    if r.status_code >= 400:
        try:
            detail = r.json()
        except Exception:
            detail = r.text
        raise RuntimeError(f"ElevenLabs error {r.status_code}: {detail}")
    return r.content

def _looks_meta(head: str) -> bool:
    head_up = head.upper()
    return any(head_up.startswith(pfx) for pfx in META_PREFIXES)

def _normalize_speaker(tag_inside: str) -> str:
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
    Devuelve el nombre de archivo si el tag es [imagen:...].
    Acepta '1png' y lo convierte en '1.png'.
    Si el valor es 'clear'/'none'/'off'/'0'/'null' -> devuelve '' para indicar que hay que limpiar la imagen activa.
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
    Reglas:
    - [SPEAKER] fija el hablante (etiqueta en línea sola).
    - [imagen:archivo] ACTIVA esa imagen para ESTE y LOS SIGUIENTES bloques hasta que se cambie.
    - Puedes limpiar con [imagen:clear] / [imagen:none] / [imagen:off].
    - Tags meta tipo [Ambiente: ..] se ignoran.
    - Un bloque = líneas de texto hasta el siguiente [SPEAKER].
    - [CIERRE] añade un bloque especial de cierre que no genera audio y se resuelve más tarde.
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


def safe_basename(text: str, max_len: int = 40) -> str:
    t = re.sub(r"\s+", " ", text).strip()
    t = t[:max_len]
    t = re.sub(r"[^\w\s-]", "", t, flags=re.U)
    t = t.replace(" ", "_") or "clip"
    return t
    
def parse_color(value):
    # Acepta "#rrggbb", "white"/"black", o tupla/lista
    if isinstance(value, (tuple, list)) and len(value) == 3:
        return tuple(int(v) for v in value)
    if isinstance(value, str):
        s = value.strip()
        if s.startswith("#") and len(s) == 7:
            r = int(s[1:3], 16)
            g = int(s[3:5], 16)
            b = int(s[5:7], 16)
            return (r, g, b)
        # como fallback, intenta nombres ("black", "white") si tu versión lo soporta
        return s
    return (0, 0, 0)
    

def parse_res(res_str: str) -> Tuple[int, int]:
    m = re.match(r"^\s*(\d+)\s*[xX]\s*(\d+)\s*$", res_str)
    if not m:
        raise ValueError("resolution debe tener formato WxH, p.ej. 1920x1080")
    return int(m.group(1)), int(m.group(2))

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".avi"}  # NUEVO

def fit_to_canvas(clip, W, H, fit, bg_color):
    # Ajuste tipo imagen pero para vídeo
    ar_clip = clip.h / clip.w
    ar_canvas = H / W
    if fit == "contain":
        resized = clip.resize(height=H if ar_clip >= ar_canvas else None,
                              width=W  if ar_clip <  ar_canvas else None).set_position(("center","center"))
        bg = ColorClip(size=(W, H), color=bg_color, duration=clip.duration)
        return CompositeVideoClip([bg, resized]).set_duration(clip.duration)
    else:  # cover
        scale = max(W / clip.w, H / clip.h)
        return clip.resize(scale).crop(
            x_center=(clip.w * scale) / 2, y_center=(clip.h * scale) / 2, width=W, height=H
        ).set_duration(clip.duration)

def ensure_duration(clip, dur, mode, W=None, H=None, bg_color=(0,0,0)):
    # tolerancia para no disparar "loop" por microdiferencias
    if clip.duration >= dur - 1e-3:
        return clip.subclip(0, dur)
    pad = dur - clip.duration

    if mode == "loop":
        return clip.fx(vfx.loop, duration=dur)
    elif mode == "freeze":
        last = clip.to_ImageClip(t=max(0, clip.duration - 1.0 / max(1, getattr(clip, "fps", 25)))).set_duration(pad)
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

    
import hashlib, random

def apply_ken_burns(img_clip, W, H, dur, args, key=""):
    """
    Versión final (2) de Ken Burns, corrigiendo el error .get_size().
    """
    img_clip = img_clip.set_duration(dur)
    if args.kenburns == "none":
        return img_clip.set_duration(dur)

    # 1. Escala inicial: Asegura que la imagen siempre cubra el cuadro (W,H)
    base_scale = max(W / img_clip.w, H / img_clip.h)
    base_clip = img_clip.resize(base_scale)
    
    # 2. Zoom dinámico: Define la función de zoom a lo largo del tiempo
    if args.kenburns == "in":
        zoom_func = lambda t: 1 + args.kb_zoom * (t / dur)
    elif args.kenburns == "out":
        zoom_func = lambda t: (1 + args.kb_zoom) - args.kb_zoom * (t / dur)
    else: # 'none'
        zoom_func = lambda t: 1
    
    animated_clip = base_clip.resize(zoom_func)

    # 3. Paneo dinámico: Mueve la imagen ampliada "detrás" del cuadro
    def pos_func(t):
        # --- CORRECCIÓN CLAVE ---
        # Calculamos el tamaño del clip en el tiempo 't' manualmente
        # en lugar de usar el método .get_size(t) que no existe.
        current_zoom = zoom_func(t)
        w = base_clip.w * current_zoom
        h = base_clip.h * current_zoom
        
        move_w = w - W
        move_h = h - H

        pan_map = {
            "center": ((0.5, 0.5), (0.5, 0.5)),
            "tl2br":  ((0.0, 0.0), (1.0, 1.0)),
            "tr2bl":  ((1.0, 0.0), (0.0, 1.0)),
            "bl2tr":  ((0.0, 1.0), (1.0, 0.0)),
            "br2tl":  ((1.0, 1.0), (0.0, 0.0)),
        }

        if args.kb_pan in pan_map:
            start_rel, end_rel = pan_map[args.kb_pan]
        else: # random
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
    

def main():
    ap = argparse.ArgumentParser(description="Genera audios ElevenLabs y VIDEO con imágenes por bloque.")
    ap.add_argument("script_txt", type=Path, help="Ruta al .txt (p.ej., dracula_1.txt)")
    ap.add_argument("--outdir", type=Path, default=Path("./Out"), help="Directorio para audios y manifest")
    ap.add_argument("--images-dir", type=Path, default=Path("./images"), help="Directorio donde están las imágenes")
    ap.add_argument("--model", default=DEFAULT_MODEL_ID, help="Modelo ElevenLabs (default: eleven_multilingual_v2)")
    ap.add_argument("--ext", default=DEFAULT_EXT, help="Extensión de audio (.mp3 o .wav)")
    ap.add_argument("--accept", default=DEFAULT_ACCEPT, help="Accept header para TTS")
    ap.add_argument("--api-key", default=None, help="ELEVENLABS_API_KEY (si no, usa variable de entorno)")
    ap.add_argument("--overwrite", action="store_true", help="Sobrescribe audios existentes")
    ap.add_argument("--dry-run", action="store_true", help="Simula sin generar audios ni vídeo")
    ap.add_argument("--max-chars", type=int, default=0, help="Divide bloques largos a ~N chars (0 = no dividir)")
    ap.add_argument("--silence-ms", type=int, default=250, help="Silencio entre clips de audio si unieras audio")
    ap.add_argument("--video-out", type=Path, default=None, help="Ruta de salida del mp4 final")
    ap.add_argument("--resolution", default="1920x1080", help="Resolución vídeo WxH (default 1920x1080)")
    ap.add_argument("--fps", type=int, default=30, help="FPS vídeo (default 30)")
    ap.add_argument("--bg-color", default="#000000", help="Color de fondo si falta imagen (hex o nombre)")
    ap.add_argument("--fit", choices=["contain", "cover"], default="contain",
                    help="Ajuste de imagen al lienzo: contain (letterbox) o cover (recorta)")
    ap.add_argument("--pad-ms", type=int, default=200, help="Padding visual al final de cada clip (ms)")
    ap.add_argument("--subs-out", type=Path, default=None,
                    help="Ruta del archivo SRT a generar (p.ej. ./Out/Dracula_P1/Dracula_P1.srt)")
    ap.add_argument("--subs-with-speaker", action="store_true",
                    help="Anteponer el nombre del personaje en cada línea de subtítulo")
    ap.add_argument("--burn-subs", action="store_true",
                    help="Quema los subtítulos del SRT en un nuevo MP4 (hard-subs).")
    ap.add_argument("--embed-subs-soft", action="store_true",
                    help="Incrusta el SRT como pista de subtítulos (soft-subs mov_text) en un nuevo MP4.")
    ap.add_argument("--subs-font", default="Arial", help="Fuente para burn-in (FFmpeg/libass).")
    ap.add_argument("--subs-fontsize", type=float, default=7.0, help="Fontsize libass (≈6–8 en 1080x1920).")
    ap.add_argument("--subs-margin-v", type=int, default=100, help="Margen vertical inferior (px).")
    ap.add_argument("--subs-outline", type=int, default=2, help="Grosor contorno.")
    ap.add_argument("--subs-shadow", type=int, default=1, help="Sombra.")
    ap.add_argument("--subs-align", type=int, default=2, help="Alineación ASS (2=bottom-center).")
    ap.add_argument("--subs-typing", action="store_true",
                    help="Activa subtítulos acumulativos palabra a palabra dentro de cada párrafo.")
    ap.add_argument("--subs-word-timing", choices=["length", "uniform"], default="length",
                    help="Distribución del tiempo por palabra: 'length' (según longitud) o 'uniform' (todas igual).")
    ap.add_argument("--subs-min-seg-ms", type=int, default=60,
                    help="Mínimo en milisegundos por paso de palabra para evitar parpadeos (default 60ms).")
    ap.add_argument("--ass-typing-out", type=Path, default=None,
                    help="Ruta del .ass a generar con efecto tecleo por palabra (karaoke \\kf).")
    ap.add_argument("--ass-style-name", default="Typing",
                    help="Nombre de estilo ASS para el efecto (default: Typing).")
    ap.add_argument("--ass-font", default="Arial", help="Fuente ASS.")
    ap.add_argument("--ass-fontsize", type=int, default=48, help="Tamaño ASS.")
    ap.add_argument("--ass-margin-v", type=int, default=80, help="Margen inferior ASS (px).")
    ap.add_argument("--ass-outline", type=int, default=2, help="Contorno ASS.")
    ap.add_argument("--ass-shadow", type=int, default=1, help="Sombra ASS.")
    ap.add_argument("--kenburns", choices=["none", "in", "out"], default="none",
                    help="Efecto Ken Burns: none (por defecto), in (zoom in), out (zoom out).")
    ap.add_argument("--kb-zoom", type=float, default=0.10,
                    help="Zoom total relativo (0.10 = 10%).")
    ap.add_argument("--kb-pan", choices=["center", "tl2br", "tr2bl", "bl2tr", "br2tl", "random"],
                    default="center", help="Dirección del paneo.")
    ap.add_argument("--kb-seed", type=int, default=0,
                    help="Semilla para 'random' (0 = derivada del nombre de imagen).")
    ap.add_argument("--remix-audio-out", type=Path, default=None,
                    help="Activa el modo REMIX: solo genera y concatena audios a esta ruta de salida.")                
    ap.add_argument("--kb-sticky", action="store_true",
                    help="No reinicia Ken Burns si la imagen no cambia: agrupa párrafos consecutivos por imagen.")
    ap.add_argument("--subs-uppercase", action="store_true",
                    help="Convierte a MAYÚSCULAS el texto en SRT/ASS.") 
    ap.add_argument("--subs-chunk-size", type=int, default=3,
                    help="Número de palabras por bloque de subtítulo (p. ej. 2 o 3).")
    ap.add_argument("--subs-chunk-hold-ms", type=int, default=0,
                    help="Milisegundos de sostén tras revelar cada bloque (0 = sin sostén).")
    ap.add_argument("--subs-chunk-prefix-all", action="store_true",
                    help="Muestra el prefijo del hablante en todos los bloques; por defecto solo en el primero.")
    ap.add_argument("--video-fill", choices=["loop", "freeze", "black", "slow"], default="loop",
                    help="Si el clip de vídeo es más corto que el audio: loop, congelar último frame o rellenar negro.")
    ap.add_argument("--media-keep-audio", action="store_true",
                    help="Mantiene el audio original de los vídeos; por defecto se silencia.")
    ap.add_argument("--media-audio-vol", type=float, default=0.20,
                    help="Volumen del audio original de los vídeos como fondo (0.0–1.0). Requiere --media-keep-audio.")
    ap.add_argument("--music-audio", action="store_true",
                    help="Activa música de fondo si existe images/musica.mp3")
    ap.add_argument("--music-audio-vol", type=float, default=0.2,
                    help="Volumen de la música de fondo (0.0–1.0)")
                
                
                
                    
                           
    args = ap.parse_args()
    
    print(f"[MoviePy] version={getattr(moviepy, '__version__', 'unknown')}")
    print(f"[KB] kenburns={args.kenburns} kb_zoom={args.kb_zoom} kb_pan={args.kb_pan}")
    
    
    bg_color = parse_color(args.bg_color)

    api_key = (args.api_key or ELEVEN_API_KEY).strip()
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY no configurada. Usa export ELEVENLABS_API_KEY=... o --api-key.", file=sys.stderr)
        sys.exit(2)

    turns = parse_script_with_images(args.script_txt)
    if not turns:
        print("No se han detectado bloques. ¿Hay etiquetas [SPEAKER] y texto?", file=sys.stderr)
        sys.exit(1)

    outdir = args.outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "audio").mkdir(exist_ok=True, parents=True)

    # Guardar manifest con imagen asociada
    manifest = [{"index": t.index, "speaker": t.speaker, "image": t.image, "text": t.text} for t in turns]
    (outdir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    def iter_chunks(text: str, chunk_size: int) -> List[str]:
        if chunk_size <= 0 or len(text) <= chunk_size:
            return [text]
        sentences = re.split(r"(?<=[\.\!\?…])\s+", text)
        chunks, cur = [], ""
        for s in sentences:
            if not cur:
                cur = s
            elif len(cur) + 1 + len(s) <= chunk_size:
                cur = f"{cur} {s}"
            else:
                chunks.append(cur); cur = s
        if cur: chunks.append(cur)
        return chunks

    # === 1) Generar audios
    audio_paths: List[Path] = []
    audio_texts: List[str] = []      # <-- nuevo: texto exacto de cada clip
    audio_speakers: List[str] = []   # <-- nuevo: hablante de cada clip
    results: List[str] = []


    if args.dry_run:
        print(f"DRY-RUN: {len(turns)} bloques detectados. No se generarán audios ni vídeo.")

    for i, t in enumerate(turns, start=1):
        if t.speaker == "__CIERRE__":
            # No genera audio para bloques de cierre
            continue

        voice_id, speed = pick_voice(t.speaker)
        chunks = iter_chunks(t.text, args.max_chars)
        
        for j, chunk in enumerate(chunks, start=1):
            idx_str = f"{i:03d}"
            part = "" if len(chunks) == 1 else f"-{j}"
            fname = f"{idx_str}_{t.speaker}_{safe_basename(chunk, 30)}{part}{args.ext}"
            fpath = outdir / "audio" / fname

            if args.dry_run:
                results.append(f"[{i}] DRY-RUN {fname} -> {t.speaker} ({t.image or 'sin imagen'})")
                audio_paths.append(fpath)
                audio_texts.append(chunk)         # <-- añade
                audio_speakers.append(t.speaker)  # <-- añade
                continue


            if fpath.exists() and not args.overwrite:
                results.append(f"[{i}] SKIP existe {fname}")
                audio_paths.append(fpath)
                audio_texts.append(chunk)         # <-- añade
                audio_speakers.append(t.speaker)  # <-- añade
                continue


            try:
                audio_bytes = create_speech(chunk, voice_id, args.model, speed, args.accept, api_key)
                fpath.write_bytes(audio_bytes)
                results.append(f"[{i}] OK {fname} -> {t.speaker} ({t.image or 'sin imagen'})")
                audio_paths.append(fpath)
                audio_texts.append(chunk)         # <-- añade
                audio_speakers.append(t.speaker)
            except Exception as e:
                results.append(f"[{i}] ERROR {fname}: {e}")
            time.sleep(0.12 if not args.dry_run else 0.0)

    for line in results:
        print(line)

    if args.remix_audio_out:
        if not AudioSegment:
            print("ERROR: Pydub no está instalado (pip install pydub), no se puede hacer el remix.", file=sys.stderr)
            sys.exit(1)

        print("\n>> MODO REMIX: Concatenando audios en una sola pista...")
        
        full_audio = AudioSegment.empty()
        # Usamos el silencio definido en los argumentos para unir los clips
        silence = AudioSegment.silent(duration=args.silence_ms)

        for fpath in audio_paths:
            try:
                segment = AudioSegment.from_file(fpath)
                full_audio += segment + silence
            except Exception as e:
                print(f"  AVISO: No se pudo cargar {fpath.name} para el remix: {e}", file=sys.stderr)

        args.remix_audio_out.parent.mkdir(parents=True, exist_ok=True)
        full_audio.export(str(args.remix_audio_out), format="mp3")
        print(f"✅ Pista de audio para remix generada -> {args.remix_audio_out}")
        return # Salimos del script para no generar el vídeo

    if args.video_out is None:
        print("No se indicó --video-out. Solo se han generado audios y manifest.")
        print(f"Salida: {outdir}")
        return

    if args.dry_run:
        print(f"DRY-RUN: no se generará el vídeo {args.video_out}")
        return

    subs_entries = []  # [(start, end, text)]
    current_time = 0.0
    ass_events = []
    # === 2) Crear vídeo (versión con opción KB 'sticky') ===
    W, H = parse_res(args.resolution)
    fps = int(args.fps)
    images_dir = args.images_dir.resolve()

    # En lugar de crear clips de vídeo al vuelo, primero reunimos TODOS los
    # 'frames' (partes) con su audio y duración, para poder agrupar por imagen.
    frames = []           # cada frame: dict con {img_key, img_file, dur, audio_clip, text, speaker}
    audio_refs = []       # para cerrar al final
    subs_entries = []     # [(start, end, text)]
    ass_events = []
    current_time = 0.0
    ai = 0  # índice en audio_paths

    def resolve_img_file(t_image):
        if not t_image:
            return None
        cand = [images_dir / t_image]
        if not cand[0].exists() and "." in t_image:
            stem, ext = Path(t_image).stem, Path(t_image).suffix
            alts = [images_dir / (stem + alt) for alt in [ext, ".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".m4v", ".webm"]]
            for c in alts:
                if c.exists():
                    cand = [c]; break
        for c in cand:
            if c.exists():
                return c
        return None


    for i, t in enumerate(turns, start=1):
        # Reunir partes de audio del bloque i
        parts_for_block = []
        while ai < len(audio_paths):
            p = audio_paths[ai]
            if p.name.startswith(f"{i:03d}_"):
                parts_for_block.append((p, audio_texts[ai], audio_speakers[ai]))
                ai += 1
            else:
                break
        if not parts_for_block:
            continue

        img_file = resolve_img_file(t.image)
        img_key  = str(img_file.resolve()) if img_file else f"COLOR:{parse_color(args.bg_color)}"

        # Crea 'frames' con audio y tiempos; también genera subtítulos
        for part_path, part_text, part_speaker in parts_for_block:
            audio_clip = AudioFileClip(str(part_path))
            audio_refs.append(audio_clip)
            dur = audio_clip.duration + (args.pad_ms / 1000.0)

            frames.append({
                "img_key":  img_key,
                "img_file": img_file,
                "dur":      dur,
                "audio":    audio_clip,
                "text":     part_text.strip(),
                "speaker":  part_speaker
            })

            # ---- SRT clásico (en bloques)
            if args.subs_out:
                base_text = part_text.strip()
                speaker_prefix = f"{part_speaker.title()}: " if args.subs_with_speaker else ""
                if args.subs_uppercase:
                    base_text = base_text.upper()
                    speaker_prefix = speaker_prefix.upper()

                words = _tokenize_words(base_text)
                if words:
                    # Reutiliza 'segs' calculados arriba si existe; si no, calcúlalo rápido:
                    try:
                        _ = segs
                    except NameError:
                        # cálculo mínimo si no se ha hecho en ASS
                        weights = _word_weights(words, getattr(args, "subs_word_timing", "length"))
                        total_w = float(sum(weights)) if weights else 1.0
                        min_seg = getattr(args, "subs_min_seg_ms", 60) / 1000.0
                        segs, rem = [], (audio_clip.duration)
                        for idx, wgt in enumerate(weights):
                            if idx < len(words) - 1:
                                seg = max(min_seg, audio_clip.duration * (wgt / total_w))
                                reserva = min_seg * (len(words) - 1 - idx)
                                seg = min(seg, max(min_seg, rem - reserva))
                            else:
                                seg = max(min_seg, rem)
                            segs.append(seg); rem -= seg

                    n = max(1, getattr(args, "subs_chunk_size", 3))
                    hold_ms = max(0, getattr(args, "subs_chunk_hold_ms", 0))
                    t = current_time
                    i = 0
                    while i < len(words):
                        ch_words = words[i : i + n]
                        ch_segs  = segs[i  : i + n]
                        ch_dur   = sum(ch_segs)

                        s_text = ((speaker_prefix if (getattr(args, "subs_chunk_prefix_all", False) or i == 0) else "") + " ".join(ch_words)).strip()
                        subs_entries.append((t, t + ch_dur, s_text))

                        if hold_ms > 0:
                            t += ch_dur + (hold_ms / 1000.0)
                        else:
                            t += ch_dur

                        i += n
                else:
                    s_text = (speaker_prefix + base_text).strip()
                    subs_entries.append((current_time, current_time + audio_clip.duration, s_text))


            # ---- ASS typing (opcional), igual que antes
            if args.ass_typing_out:
                start = current_time
                end   = current_time + audio_clip.duration
                dur_block = max(0.01, end - start)

                base_text = part_text.strip()
                if args.subs_uppercase:
                    base_text = base_text.upper()

                words = _tokenize_words(base_text)
                speaker_prefix = f"{part_speaker.title()}: " if args.subs_with_speaker else ""
                if args.subs_uppercase:
                    speaker_prefix = speaker_prefix.upper()

                if not words:
                    ass_events.append((start, end, speaker_prefix + base_text))
                else:
                    weights = _word_weights(words, getattr(args, "subs_word_timing", "length"))
                    total_w = float(sum(weights)) if weights else 1.0
                    min_seg = getattr(args, "subs_min_seg_ms", 60) / 1000.0

                    # Duración por palabra
                    segs, rem = [], dur_block
                    for idx, wgt in enumerate(weights):
                        if idx < len(words) - 1:
                            seg = max(min_seg, dur_block * (wgt / total_w))
                            reserva = min_seg * (len(words) - 1 - idx)
                            seg = min(seg, max(min_seg, rem - reserva))
                        else:
                            seg = max(min_seg, rem)
                        segs.append(seg); rem -= seg

                    # ---- Chunking: bloques de N palabras
                    n = max(1, getattr(args, "subs_chunk_size", 3))
                    hold_ms = max(0, getattr(args, "subs_chunk_hold_ms", 0))
                    t = start
                    i = 0
                    while i < len(words):
                        ch_words = words[i : i + n]
                        ch_segs  = segs[i  : i + n]
                        ch_dur   = sum(ch_segs)

                        kf_parts = []
                        if speaker_prefix and (getattr(args, "subs_chunk_prefix_all", False) or i == 0):
                            kf_parts.append(r"{\kf1}" + speaker_prefix.strip())
                        for w, seg in zip(ch_words, ch_segs):
                            cs = max(1, int(round(seg * 100)))
                            kf_parts.append(rf"{{\kf{cs}}}{w}")
                        ass_text = " ".join(kf_parts)

                        # Evento del bloque: solo este chunk
                        ass_events.append((t, t + ch_dur, ass_text))

                        # Sostén opcional del chunk ya revelado en blanco
                        if hold_ms > 0:
                            hold_end = t + ch_dur + (hold_ms / 1000.0)
                            full_chunk = (
                                (speaker_prefix.strip() + " ") if (speaker_prefix and (getattr(args, "subs_chunk_prefix_all", False) or i == 0)) else ""
                            ) + " ".join(ch_words)
                            ass_events.append((t + ch_dur, hold_end, r"{\1a&H00&\c&HFFFFFF&}" + full_chunk))
                            t = hold_end
                        else:
                            t = t + ch_dur

                        i += n

            current_time += dur

    # Con los 'frames' armados, construimos el vídeo:
    video_clips = []

    if args.kenburns != "none" and args.kb_sticky:
        # --- AGRUPACIÓN 'sticky' por imagen consecutiva ---
        group = []
        def flush_group(g):
            if not g:
                return
            total_dur = sum(f["dur"] for f in g)
            img_file  = g[0]["img_file"]

            # ----- REEMPLAZA DESDE AQUÍ -----
            bg_color = parse_color(args.bg_color)

            # Clip visual base (una sola vez por grupo)
            if img_file and img_file.exists():
                suffix = img_file.suffix.lower()
                if suffix in VIDEO_EXTS:
                    # VíDEO STICKY
                    base = VideoFileClip(str(img_file))
                    if not args.media_keep_audio:
                        base = base.without_audio()
                    base = ensure_duration(base, total_dur, args.video_fill, W=W, H=H, bg_color=bg_color)
                    base = fit_to_canvas(base, W, H, args.fit, bg_color)
                    visual = apply_ken_burns(base, W, H, total_dur, args, key=str(img_file)) if args.kenburns != "none" else base
                else:
                    # IMAGEN STICKY (comportamiento original)
                    base = ImageClip(str(img_file)).set_duration(total_dur)
                    if args.kenburns != "none":
                        visual = apply_ken_burns(base, W, H, total_dur, args, key=str(img_file))
                    else:
                        visual = fit_to_canvas(base, W, H, args.fit, bg_color)
            else:
                visual = ColorClip(size=(W, H), color=bg_color, duration=total_dur)
            # ----- HASTA AQUÍ -----

            # Audio: cada parte con su offset dentro del grupo
            offs = 0.0
            tracks = []
            for f in g:
                tracks.append(f["audio"].set_start(offs))
                offs += f["dur"]
            comp_audio = CompositeAudioClip(tracks)

            # Mezcla con audio de fondo del vídeo si se solicitó
            final_audio = comp_audio
            try:
                if args.media_keep_audio and getattr(visual, "audio", None) is not None:
                    bg = visual.audio.volumex(max(0.0, min(1.0, args.media_audio_vol))).set_duration(total_dur)
                    final_audio = CompositeAudioClip([bg, comp_audio])
            except Exception:
                pass

            video_clips.append(visual.set_audio(final_audio))


        prev_key = None
        for f in frames:
            if prev_key is None or f["img_key"] == prev_key:
                group.append(f)
            else:
                flush_group(group)
                group = [f]
            prev_key = f["img_key"]
        flush_group(group)

    else:
        # --- Fallback: comportamiento original, clip por parte ---
        bg_color = parse_color(args.bg_color)
        for f in frames:
            dur = f["dur"]
            img_file = f["img_file"]

            # ----- REEMPLAZA DESDE AQUÍ -----
            if img_file and img_file.exists():
                suffix = img_file.suffix.lower()
                if suffix in VIDEO_EXTS:  # NUEVO: tratar como vídeo
                    base_vid = VideoFileClip(str(img_file))
                    if not args.media_keep_audio:
                        base_vid = base_vid.without_audio()
                    # 1) iguala duración al audio del bloque
                    base_vid = ensure_duration(base_vid, dur, args.video_fill, W=W, H=H, bg_color=bg_color)
                    # 2) ajusta al lienzo (cover/contain)
                    base_vid = fit_to_canvas(base_vid, W, H, args.fit, bg_color)

                    if getattr(args, "kenburns", "none") != "none":
                        final_video_clip = apply_ken_burns(base_vid, W, H, dur, args, key=str(img_file))
                    else:
                        final_video_clip = base_vid
                else:
                    # (COMPORTAMIENTO ORIGINAL PARA IMÁGENES)
                    base_img = ImageClip(str(img_file)).set_duration(dur)
                    if getattr(args, "kenburns", "none") != "none":
                        final_video_clip = apply_ken_burns(base_img, W, H, dur, args, key=str(img_file))
                    else:
                        if args.fit == "contain":
                            img_resized = base_img.resize(
                                height=H if base_img.h / base_img.w >= H / W else None,
                                width=W  if base_img.h / base_img.w <  H / W else None
                            ).set_position(("center", "center"))
                            bg = ColorClip(size=(W, H), color=bg_color, duration=dur)
                            final_video_clip = CompositeVideoClip([bg, img_resized])
                        else:
                            scale = max(W / base_img.w, H / base_img.h)
                            final_video_clip = base_img.resize(scale).crop(
                                x_center=base_img.w * scale / 2, y_center=base_img.h * scale / 2, width=W, height=H
                            )
            else:
                final_video_clip = ColorClip(size=(W, H), color=bg_color, duration=dur)
            # ----- HASTA AQUÍ -----

            # Mezcla narración + posible audio del vídeo a volumen de fondo
            final_audio = f["audio"]
            try:
                if args.media_keep_audio and getattr(final_video_clip, "audio", None) is not None:
                    bg = final_video_clip.audio.volumex(max(0.0, min(1.0, args.media_audio_vol))).set_duration(dur)
                    final_audio = CompositeAudioClip([bg, f["audio"]])
            except Exception:
                pass

            video_clips.append(final_video_clip.set_audio(final_audio))


            # Avanza el timeline global (incluye el pad visual)
            current_time += dur

    # Escribir ASS typing si se solicitó
    if args.ass_typing_out and ass_events:  # <--- guion_bajo
        W, H = parse_res(args.resolution)
        header = _ass_header(W, H, args)

        lines = [header]
        for (start, end, text) in ass_events:
            lines.append(
                f"Dialogue: 0,{_fmt_ass_ts(start)},{_fmt_ass_ts(end)},"
                f"{args.ass_style_name},,0,0,{args.ass_margin_v},,"
                f"{text}"
            )

        args.ass_typing_out.parent.mkdir(parents=True, exist_ok=True)
        args.ass_typing_out.write_text("\n".join(lines), encoding="utf-8")
        print(f"Subtítulos ASS (typing) -> {args.ass_typing_out}")

    # --- AÑADIR CIERRE SI EXISTE ---
    for t in turns:
        if t.speaker == "__CIERRE__":
            cierre_path = images_dir / "cierre.mp4"
            if cierre_path.exists():
                cierre_clip = VideoFileClip(str(cierre_path))
                cierre_clip = fit_to_canvas(cierre_clip, W, H, args.fit, bg_color)
                # mantiene su audio y duración nativos, sin narración añadida
                video_clips.append(cierre_clip)
            else:
                print("⚠️ Aviso: cierre.mp4 no encontrado en /images")

    if not video_clips:
        print("No hay clips de vídeo creados. ¿Existen los audios generados?", file=sys.stderr)
        sys.exit(5)

    final = concatenate_videoclips(video_clips, method="compose")
    args.video_out.parent.mkdir(parents=True, exist_ok=True)
    
    # --- MÚSICA DE FONDO ---
    if args.music_audio:
        music_path = args.images_dir / "musica.mp3"
        if music_path.exists():
            try:
                bgm = AudioFileClip(str(music_path))
                # loopeamos la música para cubrir todo el vídeo
                bgm = moviepy.audio.fx.all.audio_loop(bgm, duration=final.duration)
                # aplicamos el volumen indicado
                bgm = bgm.volumex(max(0.0, min(1.0, args.music_audio_vol)))

                if final.audio is not None:
                    mixed_audio = CompositeAudioClip([final.audio, bgm])
                else:
                    mixed_audio = bgm

                final = final.set_audio(mixed_audio)
                print(f"✅ Música añadida desde {music_path.name} (vol={args.music_audio_vol})")
            except Exception as e:
                print(f"⚠️ No se pudo añadir música de fondo: {e}")
        else:
            print(f"⚠️ Aviso: musica.mp3 no encontrado en {args.images_dir}")
    

    try:
        # Puedes añadir "threads=4" si quieres limitar/forzar hilos en ffmpeg
        final.write_videofile(
            str(args.video_out),
            fps=fps,
            codec="libx264",
            audio_codec="aac"
        )
        print(f"Vídeo exportado -> {args.video_out}")
    finally:
        # Cerrar el clip final y liberar recursos temporales
        try:
            final.close()
        except Exception:
            pass

        # Cerrar cada subclip (ImageClip/ColorClip con audio asignado)
        for clip in video_clips:
            try:
                clip.close()
            except Exception:
                pass
                
        # <-- NUEVO: cerrar también todos los AudioFileClip usados
        for ac in audio_refs:
            try:
                ac.close()
            except Exception:
                pass                

    # Escribir SRT si se solicitó
    if args.subs_out and subs_entries:
        srt_lines = []
        for idx, (start, end, text) in enumerate(subs_entries, start=1):
            srt_lines.append(str(idx))
            srt_lines.append(f"{_fmt_ts(start)} --> {_fmt_ts(end)}")
            srt_lines.append(text)
            srt_lines.append("")  # línea en blanco
        args.subs_out.parent.mkdir(parents=True, exist_ok=True)
        args.subs_out.write_text("\n".join(srt_lines), encoding="utf-8")
        print(f"Subtítulos SRT -> {args.subs_out}")

    # ----- Integración de subtítulos con FFmpeg (opcional) -----
    if args.subs_out and args.burn_subs:
        burned_path = args.video_out.with_name(args.video_out.stem + "_subs.mp4")
        style = (
            f"FontName={args.subs_font},"
            f"Fontsize={args.subs_fontsize},"
            f"Outline={args.subs_outline},"
            f"Shadow={args.subs_shadow},"
            f"Alignment={args.subs_align},"
            f"MarginV={args.subs_margin_v}"
        )
        cmd = [
            "ffmpeg", "-y",
            "-i", args.video_out.name,
            "-vf", f"subtitles={args.subs_out.name}:force_style='{style}'",
            "-c:a", "copy",
            burned_path.name
        ]
        try:
            subprocess.run(cmd, cwd=str(args.video_out.parent), check=True)
            print(f"Vídeo con subtítulos QUEMADOS -> {burned_path}")
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg (burn-subs) falló: {e}")

    if args.subs_out and args.embed_subs_soft:
        soft_path = args.video_out.with_name(args.video_out.stem + "_softsubs.mp4")
        cmd = [
            "ffmpeg", "-y",
            "-i", args.video_out.name,
            "-i", args.subs_out.name,
            "-map", "0", "-map", "1",
            "-c", "copy",
            "-c:s", "mov_text",
            soft_path.name
        ]
        try:
            subprocess.run(cmd, cwd=str(args.video_out.parent), check=True)
            print(f"Vídeo con subtítulos SOFT (pista mov_text) -> {soft_path}")
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg (embed soft) falló: {e}")
    

if __name__ == "__main__":
    main()