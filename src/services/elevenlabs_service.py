"""
Servicio para interactuar con la API de ElevenLabs (Text-to-Speech).
"""
import requests
from ..config.settings import ELEVEN_API_URL, DEFAULT_VOICE_SETTINGS, ELEVENLABS_API_KEY


class ElevenLabsService:
    """Cliente para ElevenLabs TTS."""

    def __init__(self, api_key: str = None):
        """
        Inicializa el servicio de ElevenLabs.

        Args:
            api_key: Clave API de ElevenLabs. Si no se proporciona, usa la del config.
        """
        self.api_key = api_key or ELEVENLABS_API_KEY
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY no configurada")

    def create_speech(self, text: str, voice_id: str, model_id: str,
                     speed: float = 1.0, accept: str = "audio/mpeg") -> bytes:
        """
        Genera audio a partir de texto.

        Args:
            text: Texto a convertir en audio
            voice_id: ID de la voz a usar
            model_id: ID del modelo (ej: eleven_multilingual_v2)
            speed: Velocidad de habla (0.7 - 1.2)
            accept: Tipo de audio a generar (audio/mpeg, audio/wav, etc.)

        Returns:
            Bytes del archivo de audio generado

        Raises:
            RuntimeError: Si la llamada a la API falla
        """
        url = ELEVEN_API_URL.format(voice_id=voice_id)
        headers = {
            "Accept": accept,
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }

        settings = dict(DEFAULT_VOICE_SETTINGS)
        settings["speed"] = speed

        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": settings
        }

        response = requests.post(url, headers=headers, json=payload, timeout=120)

        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = response.text
            raise RuntimeError(f"ElevenLabs error {response.status_code}: {detail}")

        return response.content
