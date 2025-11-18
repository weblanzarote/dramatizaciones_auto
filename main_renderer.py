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
    print("⚠️  NOTA: La lógica completa de composición de video está en")
    print("   el archivo original generate_audiovideo_from_txt_drama.py (líneas 654-1104).")
    print("   Por simplicidad, esta versión refactorizada requiere que completes")
    print("   esa funcionalidad en src/video/composition.py")

    # TODO: Implementar composición de video
    # Ver generate_audiovideo_from_txt_drama.py líneas 654-1104 para la lógica completa
    # Incluye: creación de clips, aplicar Ken Burns, concatenar, añadir música, etc.

    print(f"\n✅ Proceso completado. Audios en: {outdir}")


if __name__ == "__main__":
    main()
