"""
Generación de subtítulos en formatos SRT y ASS.
"""
import re
from datetime import timedelta
from typing import List, Tuple


def _fmt_ts(seconds: float) -> str:
    """
    Formatea tiempo en formato SRT (HH:MM:SS,mmm).

    Args:
        seconds: Tiempo en segundos

    Returns:
        String formateado para SRT
    """
    td = timedelta(seconds=max(0, seconds))
    total_ms = int(td.total_seconds() * 1000)
    hh = total_ms // 3600000
    mm = (total_ms % 3600000) // 60000
    ss = (total_ms % 60000) // 1000
    ms = total_ms % 1000
    return f"{hh:02d}:{mm:02d}:{ss:02d},{ms:03d}"


def _fmt_ass_ts(seconds: float) -> str:
    """
    Formatea tiempo en formato ASS (H:MM:SS.cc).

    Args:
        seconds: Tiempo en segundos

    Returns:
        String formateado para ASS
    """
    s = max(0.0, float(seconds))
    h = int(s // 3600)
    s -= h * 3600
    m = int(s // 60)
    s -= m * 60
    cs = int(round(s * 100))
    ss = cs // 100
    cc = cs % 100
    return f"{h:d}:{m:02d}:{ss:02d}.{cc:02d}"


def _tokenize_words(s: str) -> List[str]:
    """
    Divide el texto en tokens tipo palabra preservando puntuación.

    Args:
        s: Texto a tokenizar

    Returns:
        Lista de palabras/tokens
    """
    return re.findall(r"\S+", s, flags=re.U)


def _word_weights(words: List[str], mode: str) -> List[float]:
    """
    Pesa cada palabra para repartir mejor el tiempo.

    Args:
        words: Lista de palabras
        mode: Modo de peso ("uniform" o "length")

    Returns:
        Lista de pesos
    """
    if mode == "uniform":
        return [1.0] * len(words)

    out = []
    for w in words:
        visible = re.sub(r"[^\wáéíóúüñÁÉÍÓÚÜÑ0-9]", "", w, flags=re.U)
        out.append(max(1, len(visible)))
    return out


def generate_srt_subtitles(entries: List[Tuple[float, float, str]], output_path: str):
    """
    Genera un archivo SRT a partir de entradas de subtítulos.

    Args:
        entries: Lista de tuplas (start_time, end_time, text)
        output_path: Ruta donde guardar el archivo SRT
    """
    srt_lines = []
    for idx, (start, end, text) in enumerate(entries, start=1):
        srt_lines.append(str(idx))
        srt_lines.append(f"{_fmt_ts(start)} --> {_fmt_ts(end)}")
        srt_lines.append(text)
        srt_lines.append("")  # línea en blanco

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))


def _ass_header(w: int, h: int, args) -> str:
    """
    Genera el header de un archivo ASS.

    Args:
        w, h: Dimensiones del video
        args: Argumentos con configuración de estilo

    Returns:
        String con el header ASS
    """
    # &HAABBGGRR  (AA=alpha: 00 opaco, FF transparente)
    primary = "&H00FFFFFF&"  # Revelado (llenado \kf): blanco opaco
    secondary = "&HFFFFFFFF&"  # NO revelado: transparente
    outline = "&H00000000&"  # Contorno/sombra: negro opaco
    shadow = "&H00000000&"  # BackColour

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
        f"Style: {args.ass_style_name},{args.ass_font},{args.ass_fontsize},{primary},{secondary},{outline},{shadow},"
        f"0,0,0,0,100,100,0,0,1,{args.ass_outline},{args.ass_shadow},{args.subs_align},30,30,{args.ass_margin_v},0\n"
        f"\n[Events]\n"
        f"Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )


def generate_ass_subtitles(events: List[Tuple[float, float, str]], w: int, h: int,
                          args, output_path: str):
    """
    Genera un archivo ASS con efectos de karaoke/typing.

    Args:
        events: Lista de tuplas (start_time, end_time, ass_text_with_effects)
        w, h: Dimensiones del video
        args: Argumentos con configuración de estilo
        output_path: Ruta donde guardar el archivo ASS
    """
    header = _ass_header(w, h, args)

    lines = [header]
    for (start, end, text) in events:
        lines.append(
            f"Dialogue: 0,{_fmt_ass_ts(start)},{_fmt_ass_ts(end)},"
            f"{args.ass_style_name},,0,0,{args.ass_margin_v},,"
            f"{text}"
        )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
