"""
Renderizador completo de video: orquesta audio, imágenes y composición.
"""
import os
import moviepy
import moviepy.audio.fx.all
from pathlib import Path
from moviepy.editor import (
    ImageClip, VideoFileClip, AudioFileClip, ColorClip, CompositeVideoClip,
    concatenate_videoclips, CompositeAudioClip
)

from .composition import (
    fit_to_canvas, ensure_duration, apply_ken_burns, parse_resolution
)
from .subtitles import generate_srt_subtitles, generate_ass_subtitles
from ..config.settings import VIDEO_EXTS
from ..media.image_proc import parse_color


def render_video_from_frames(
    frames: list,
    turns: list,
    args,
    images_dir: Path,
    audio_refs: list,
    subs_entries: list = None,
    ass_events: list = None
) -> bool:
    """
    Renderiza el video final a partir de frames preparados.

    Args:
        frames: Lista de frames con {img_key, img_file, dur, audio, text, speaker}
        turns: Lista de Turn objects del parser
        args: ArgumentParser args con configuración
        images_dir: Path al directorio de imágenes
        audio_refs: Lista de AudioFileClip para cerrar al final
        subs_entries: Lista de entradas de subtítulos SRT (opcional)
        ass_events: Lista de eventos ASS (opcional)

    Returns:
        True si el renderizado fue exitoso
    """
    W, H = parse_resolution(args.resolution)
    fps = int(args.fps)
    bg_color = parse_color(args.bg_color)

    video_clips = []

    # Renderizar con Ken Burns sticky o normal
    if args.kenburns != "none" and args.kb_sticky:
        # Agrupación sticky por imagen consecutiva
        group = []

        def flush_group(g):
            if not g:
                return
            total_dur = sum(f["dur"] for f in g)
            img_file = g[0]["img_file"]

            # Clip visual base (una sola vez por grupo)
            if img_file and img_file.exists():
                suffix = img_file.suffix.lower()
                if suffix in VIDEO_EXTS:
                    # VIDEO STICKY
                    base = VideoFileClip(str(img_file))
                    if not args.media_keep_audio:
                        base = base.without_audio()
                    base = ensure_duration(base, total_dur, args.video_fill, W=W, H=H, bg_color=bg_color)
                    base = fit_to_canvas(base, W, H, args.fit, bg_color)
                    visual = apply_ken_burns(base, W, H, total_dur, args, key=str(img_file)) if args.kenburns != "none" else base
                else:
                    # IMAGEN STICKY
                    base = ImageClip(str(img_file)).set_duration(total_dur)
                    if args.kenburns != "none":
                        visual = apply_ken_burns(base, W, H, total_dur, args, key=str(img_file))
                    else:
                        visual = fit_to_canvas(base, W, H, args.fit, bg_color)
            else:
                visual = ColorClip(size=(W, H), color=bg_color, duration=total_dur)

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
        # Fallback: clip por parte (sin sticky)
        for f in frames:
            dur = f["dur"]
            img_file = f["img_file"]

            if img_file and img_file.exists():
                suffix = img_file.suffix.lower()
                if suffix in VIDEO_EXTS:
                    # TRATAR COMO VIDEO
                    base_vid = VideoFileClip(str(img_file))
                    if not args.media_keep_audio:
                        base_vid = base_vid.without_audio()
                    base_vid = ensure_duration(base_vid, dur, args.video_fill, W=W, H=H, bg_color=bg_color)
                    base_vid = fit_to_canvas(base_vid, W, H, args.fit, bg_color)

                    if getattr(args, "kenburns", "none") != "none":
                        final_video_clip = apply_ken_burns(base_vid, W, H, dur, args, key=str(img_file))
                    else:
                        final_video_clip = base_vid
                else:
                    # TRATAR COMO IMAGEN
                    base_img = ImageClip(str(img_file)).set_duration(dur)
                    if getattr(args, "kenburns", "none") != "none":
                        final_video_clip = apply_ken_burns(base_img, W, H, dur, args, key=str(img_file))
                    else:
                        if args.fit == "contain":
                            img_resized = base_img.resize(
                                height=H if base_img.h / base_img.w >= H / W else None,
                                width=W if base_img.h / base_img.w < H / W else None
                            ).set_position(("center", "center"))
                            bg = ColorClip(size=(W, H), color=bg_color, duration=dur)
                            final_video_clip = CompositeVideoClip([bg, img_resized])
                        else:
                            scale = max(W / base_img.w, H / base_img.h)
                            final_video_clip = base_img.resize(scale).crop(
                                x_center=base_img.w * scale / 2,
                                y_center=base_img.h * scale / 2,
                                width=W, height=H
                            )
            else:
                final_video_clip = ColorClip(size=(W, H), color=bg_color, duration=dur)

            # Mezcla narración + posible audio del vídeo
            final_audio = f["audio"]
            try:
                if args.media_keep_audio and getattr(final_video_clip, "audio", None) is not None:
                    bg = final_video_clip.audio.volumex(max(0.0, min(1.0, args.media_audio_vol))).set_duration(dur)
                    final_audio = CompositeAudioClip([bg, f["audio"]])
            except Exception:
                pass

            video_clips.append(final_video_clip.set_audio(final_audio))

    # Escribir ASS typing si se solicitó
    if hasattr(args, 'ass_typing_out') and args.ass_typing_out and ass_events:
        generate_ass_subtitles(ass_events, W, H, args, str(args.ass_typing_out))
        print(f"Subtítulos ASS (typing) -> {args.ass_typing_out}")

    # Añadir cierre si existe
    for t in turns:
        if t.speaker == "__CIERRE__":
            cierre_path = images_dir / "cierre.mp4"
            if cierre_path.exists():
                cierre_clip = VideoFileClip(str(cierre_path))
                cierre_clip = fit_to_canvas(cierre_clip, W, H, args.fit, bg_color)
                video_clips.append(cierre_clip)
            else:
                print("⚠️ Aviso: cierre.mp4 no encontrado en /images")

    if not video_clips:
        print("❌ No hay clips de vídeo creados.")
        return False

    # Concatenar clips
    final = concatenate_videoclips(video_clips, method="compose")
    args.video_out.parent.mkdir(parents=True, exist_ok=True)

    # Añadir música de fondo
    if hasattr(args, 'music_audio') and args.music_audio:
        music_path = args.images_dir / "musica.mp3"
        if music_path.exists():
            try:
                bgm = AudioFileClip(str(music_path))
                bgm = moviepy.audio.fx.all.audio_loop(bgm, duration=final.duration)
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

    # Exportar video
    try:
        final.write_videofile(
            str(args.video_out),
            fps=fps,
            codec="libx264",
            audio_codec="aac"
        )
        print(f"✅ Vídeo exportado -> {args.video_out}")
    finally:
        # Cerrar clips y liberar recursos
        try:
            final.close()
        except Exception:
            pass

        for clip in video_clips:
            try:
                clip.close()
            except Exception:
                pass

        for ac in audio_refs:
            try:
                ac.close()
            except Exception:
                pass

    # Escribir SRT si se solicitó
    if hasattr(args, 'subs_out') and args.subs_out and subs_entries:
        generate_srt_subtitles(subs_entries, str(args.subs_out))
        print(f"✅ Subtítulos SRT -> {args.subs_out}")

    return True
