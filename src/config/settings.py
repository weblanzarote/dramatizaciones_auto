"""
Configuración central del proyecto.
Carga variables de entorno y gestiona claves de API.
"""
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# === API Keys ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
RUNWARE_API_KEY = os.getenv("RUNWARE_API_KEY")

# === Validaciones ===
def validate_api_keys(required_keys: list[str] = None):
    """
    Valida que las API keys requeridas estén configuradas.

    Args:
        required_keys: Lista de keys a validar. Si es None, valida las básicas.

    Raises:
        ValueError: Si falta alguna key requerida.
    """
    if required_keys is None:
        required_keys = ["OPENAI_API_KEY", "GEMINI_API_KEY"]

    missing = []
    for key in required_keys:
        if not globals().get(key):
            missing.append(key)

    if missing:
        raise ValueError(
            f"Faltan las siguientes API keys en el archivo .env: {', '.join(missing)}\n"
            f"Por favor, configura tu archivo .env correctamente."
        )

# === Constantes del proyecto ===
NEGATIVE_PROMPT = (
    "(worst quality, low quality, normal quality, plain, boring, blurry, jpeg artifacts, "
    "signature, watermark, text, username, error, poorly drawn, malformed, deformed, "
    "mutated, ugly, duplicate, out of frame, missing items, extra limbs, fused fingers)"
)

# Modelo de Runware económico
QWEN_AIR_ID = "runware:108@1"

# === URLs de servicios ===
ELEVEN_API_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

# === Configuración de audio por defecto ===
DEFAULT_MODEL_ID = "eleven_multilingual_v2"
DEFAULT_EXT = ".mp3"
DEFAULT_ACCEPT = "audio/mpeg"
DEFAULT_VOICE_SETTINGS = {
    "stability": 0.30,
    "similarity_boost": 0.30,
    "style": 0.0,
    "use_speaker_boost": True,
}

# === Etiquetas de metadatos ===
META_PREFIXES = ("SFX", "AMB", "AMBIENTE", "FX", "NOTA", "MÚSICA", "MUSICA")
IMAGE_PREFIX = "IMAGEN"

# === Configuración de video ===
VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".avi"}
