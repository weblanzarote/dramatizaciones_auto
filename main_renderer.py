#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Renderizador de videos de dramatización.
Genera audios con ElevenLabs y crea video sincronizado con imágenes.

Antes: generate_audiovideo_from_txt_drama.py
Ahora: Usa los módulos refactorizados en src/
"""
import argparse
import json
import sys
import time
from pathlib import Path

# Importar configuración
from src.config.settings import (
    validate_api_keys, DEFAULT_MODEL_ID, DEFAULT_EXT, DEFAULT_ACCEPT
)
from src.config.voices import pick_voice

# Importar servicios
from src.services.elevenlabs_service import ElevenLabsService

# Importar procesamiento de media
from src.media.image_proc import parse_color
from src.media.audio_proc import concatenate_audio_files, is_pydub_available

# Importar lógica de video
from src.video.parser import parse_script_with_images
from src.video.composition import parse_resolution
from src.video.subtitles import generate_srt_subtitles

# MoviePy imports
from moviepy.editor import AudioFileClip


def safe_basename(text: str, max_len: int = 40) -> str:
    """Genera un nombre de archivo seguro a partir de texto."""
    import re
    t = re.sub(r"\s+", " ", text).strip()
    t = t[:max_len]
    t = re.sub(r"[^\w\s-]", "", t, flags=re.U)
    t = t.replace(" ", "_") or "clip"
    return t


def iter_chunks(text: str, chunk_size: int):
    """Divide texto en chunks si es muy largo."""
    if chunk_size <= 0 or len(text) <= chunk_size:
        return [text]

    import re
    sentences = re.split(r"(?<=[\.\!\?…])\s+", text)
    chunks, cur = [], ""

    for s in sentences:
        if not cur:
            cur = s
        elif len(cur) + 1 + len(s) <= chunk_size:
            cur = f"{cur} {s}"
        else:
            chunks.append(cur)
            cur = s

    if cur:
        chunks.append(cur)
    return chunks


def main():
    """Función principal del renderizador."""
    parser = argparse.ArgumentParser(
        description="Genera audios con ElevenLabs y VIDEO con imágenes por bloque"
    )
    parser.add_argument("script_txt", type=Path, help="Ruta al .txt con el guion")
    parser.add_argument("--outdir", type=Path, default=Path("./Out"), help="Directorio para audios")
    parser.add_argument("--images-dir", type=Path, default=Path("./images"), help="Directorio de imágenes")
    parser.add_argument("--model", default=DEFAULT_MODEL_ID, help="Modelo ElevenLabs")
    parser.add_argument("--ext", default=DEFAULT_EXT, help="Extensión de audio")
    parser.add_argument("--accept", default=DEFAULT_ACCEPT, help="Accept header para TTS")
    parser.add_argument("--overwrite", action="store_true", help="Sobrescribe audios existentes")
    parser.add_argument("--dry-run", action="store_true", help="Simula sin generar audios ni vídeo")
    parser.add_argument("--max-chars", type=int, default=0, help="Divide bloques largos")
    parser.add_argument("--video-out", type=Path, help="Ruta del mp4 final")
    parser.add_argument("--resolution", default="1920x1080", help="Resolución WxH")
    parser.add_argument("--fps", type=int, default=30, help="FPS del video")
    parser.add_argument("--bg-color", default="#000000", help="Color de fondo")
    parser.add_argument("--fit", choices=["contain", "cover"], default="contain",
                        help="Ajuste de imagen: contain (letterbox) o cover (recorta)")
    parser.add_argument("--pad-ms", type=int, default=200, help="Padding visual al final (ms)")
    parser.add_argument("--kenburns", choices=["none", "in", "out"], default="none",
                        help="Efecto Ken Burns: none, in (zoom in), out (zoom out)")
    parser.add_argument("--kb-zoom", type=float, default=0.10, help="Zoom total relativo (0.10 = 10%)")
    parser.add_argument("--kb-pan", choices=["center", "tl2br", "tr2bl", "bl2tr", "br2tl", "random"],
                        default="center", help="Dirección del paneo")
    parser.add_argument("--kb-seed", type=int, default=0, help="Semilla para 'random' (0 = derivada)")
    parser.add_argument("--kb-sticky", action="store_true",
                        help="No reinicia Ken Burns si la imagen no cambia")
    parser.add_argument("--media-keep-audio", action="store_true",
                        help="Mantiene audio original de videos")
    parser.add_argument("--media-audio-vol", type=float, default=0.20,
                        help="Volumen del audio original de videos (0.0-1.0)")
    parser.add_argument("--music-audio", action="store_true",
                        help="Activa música de fondo si existe images/musica.mp3")
    parser.add_argument("--music-audio-vol", type=float, default=0.2,
                        help="Volumen de la música de fondo (0.0-1.0)")

    args = parser.parse_args()

    # Validar API keys
    try:
        validate_api_keys(["ELEVENLABS_API_KEY"])
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)

    # Inicializar servicio
    print("🚀 Inicializando ElevenLabs...")
    elevenlabs = ElevenLabsService()
    bg_color = parse_color(args.bg_color)

    # 1. Parsear script
    print(f"\n📖 Parseando script: {args.script_txt}")
    turns = parse_script_with_images(args.script_txt)

    if not turns:
        print("❌ No se detectaron bloques. ¿Hay etiquetas [SPEAKER] y texto?")
        sys.exit(1)

    print(f"✅ {len(turns)} bloques detectados")

    # 2. Crear directorios
    outdir = args.outdir.resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "audio").mkdir(exist_ok=True, parents=True)

    # Guardar manifest
    manifest = [{"index": t.index, "speaker": t.speaker, "image": t.image, "text": t.text} for t in turns]
    (outdir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # 3. Generar audios
    print("\n🎤 Generando audios con ElevenLabs...")
    audio_paths = []
    audio_texts = []
    audio_speakers = []
    results = []

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
                results.append(f"[{i}] DRY-RUN {fname} -> {t.speaker}")
                audio_paths.append(fpath)
                audio_texts.append(chunk)
                audio_speakers.append(t.speaker)
                continue

            if fpath.exists() and not args.overwrite:
                results.append(f"[{i}] SKIP existe {fname}")
                audio_paths.append(fpath)
                audio_texts.append(chunk)
                audio_speakers.append(t.speaker)
                continue

            try:
                audio_bytes = elevenlabs.create_speech(
                    text=chunk,
                    voice_id=voice_id,
                    model_id=args.model,
                    speed=speed,
                    accept=args.accept
                )
                fpath.write_bytes(audio_bytes)
                results.append(f"[{i}] OK {fname} -> {t.speaker} ({t.image or 'sin imagen'})")
                audio_paths.append(fpath)
                audio_texts.append(chunk)
                audio_speakers.append(t.speaker)
            except Exception as e:
                results.append(f"[{i}] ERROR {fname}: {e}")

            time.sleep(0.12 if not args.dry_run else 0.0)

    for line in results:
        print(line)

    # 4. Generar video (si se especificó --video-out)
    if args.video_out is None:
        print(f"\n✅ Audios generados en: {outdir}")
        print("ℹ️  No se especificó --video-out. Solo se generaron audios.")
        return

    if args.dry_run:
        print(f"\n✅ DRY-RUN: no se generará el vídeo {args.video_out}")
        return

    print("\n🎬 Generando video...")

    from src.video.renderer import render_video_from_frames
    from src.media.image_proc import parse_color
    from src.video.composition import parse_resolution

    W, H = parse_resolution(args.resolution)
    bg_color = parse_color(args.bg_color)
    images_dir = args.images_dir.resolve()

    # Preparar frames: reunir audio + imagen + duración
    frames = []
    audio_refs = []
    subs_entries = []
    current_time = 0.0
    ai = 0  # índice en audio_paths

    def resolve_img_file(t_image):
        if not t_image:
            return None
        cand = [images_dir / t_image]
        if not cand[0].exists() and "." in t_image:
            from pathlib import Path
            stem, ext = Path(t_image).stem, Path(t_image).suffix
            alts = [images_dir / (stem + alt) for alt in [ext, ".png", ".jpg", ".jpeg", ".webp", ".mp4", ".mov", ".m4v", ".webm"]]
            for c in alts:
                if c.exists():
                    cand = [c]
                    break
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
        img_key = str(img_file.resolve()) if img_file else f"COLOR:{bg_color}"

        # Crear frames con audio y tiempos
        for part_path, part_text, part_speaker in parts_for_block:
            audio_clip = AudioFileClip(str(part_path))
            audio_refs.append(audio_clip)
            dur = audio_clip.duration + (args.pad_ms / 1000.0)

            frames.append({
                "img_key": img_key,
                "img_file": img_file,
                "dur": dur,
                "audio": audio_clip,
                "text": part_text.strip(),
                "speaker": part_speaker
            })

            current_time += dur

    # Renderizar video con frames preparados
    success = render_video_from_frames(
        frames=frames,
        turns=turns,
        args=args,
        images_dir=images_dir,
        audio_refs=audio_refs,
        subs_entries=subs_entries,
        ass_events=[]
    )

    if success:
        print(f"\n✅ Proceso completado exitosamente!")
        print(f"📁 Audios en: {outdir}")
        print(f"🎬 Video en: {args.video_out}")
    else:
        print(f"\n⚠️ Hubo errores en el renderizado del video.")
        print(f"📁 Audios generados en: {outdir}")


if __name__ == "__main__":
    main()
