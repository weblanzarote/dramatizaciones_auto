"""
Procesamiento de audio: mezcla, concatenación, efectos.
"""
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None


def concatenate_audio_files(file_paths: list, silence_ms: int = 250, output_path: str = None):
    """
    Concatena múltiples archivos de audio con silencio entre ellos.

    Args:
        file_paths: Lista de rutas de archivos de audio
        silence_ms: Milisegundos de silencio entre clips
        output_path: Ruta de salida. Si es None, retorna el AudioSegment

    Returns:
        AudioSegment con el audio concatenado (si output_path es None)

    Raises:
        ImportError: Si pydub no está instalado
    """
    if not PYDUB_AVAILABLE:
        raise ImportError("pydub no está instalado. Ejecuta: pip install pydub")

    full_audio = AudioSegment.empty()
    silence = AudioSegment.silent(duration=silence_ms)

    for fpath in file_paths:
        try:
            segment = AudioSegment.from_file(fpath)
            full_audio += segment + silence
        except Exception as e:
            print(f"  AVISO: No se pudo cargar {fpath} para concatenar: {e}")

    if output_path:
        full_audio.export(output_path, format="mp3")
        return None

    return full_audio


def is_pydub_available() -> bool:
    """Verifica si pydub está disponible."""
    return PYDUB_AVAILABLE
