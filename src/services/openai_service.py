"""
Servicio para interactuar con la API de OpenAI (GPT-5.1 y modelos de imagen).
"""
import json
from openai import OpenAI
from ..config.settings import OPENAI_API_KEY


class OpenAIService:
    """Cliente para servicios de OpenAI."""

    def __init__(self, api_key: str = None):
        """
        Inicializa el cliente de OpenAI.

        Args:
            api_key: Clave API de OpenAI. Si no se proporciona, usa la del config.
        """
        self.api_key = api_key or OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY no configurada")

        self.client = OpenAI(api_key=self.api_key)

    def chat_completion(self, messages: list, model: str = "gpt-5.1",
                       response_format: dict = None, **kwargs) -> dict:
        """
        Realiza una llamada de chat completion.

        Args:
            messages: Lista de mensajes del chat
            model: Modelo a usar (default: gpt-5.1)
            response_format: Formato de respuesta (ej: {"type": "json_object"})
            **kwargs: Argumentos adicionales para la API

        Returns:
            Contenido de la respuesta parseado como dict (si es JSON) o str
        """
        params = {"model": model, "messages": messages}

        if response_format:
            params["response_format"] = response_format

        params.update(kwargs)

        response = self.client.chat.completions.create(**params)
        content = response.choices[0].message.content

        # Si esperamos JSON, parsearlo
        if response_format and response_format.get("type") == "json_object":
            return json.loads(content)

        return content

    def generate_image(self, prompt: str, model: str = "gpt-image-1-mini",
                      quality: str = "medium", size: str = "1080x1920", **kwargs) -> bytes:
        """
        Genera una imagen con modelos de OpenAI.

        Args:
            prompt: Descripción de la imagen
            model: Modelo a usar (gpt-image-1-mini, gpt-image-1, dall-e-2, dall-e-3)
            quality: Calidad (low, medium, high, standard, hd)
            size: Tamaño de la imagen
            **kwargs: Argumentos adicionales

        Returns:
            Bytes de la imagen generada
        """
        # Nota: Esta es una implementación placeholder
        # Ajusta según la API real de OpenAI para imágenes
        raise NotImplementedError("Implementar generación de imágenes de OpenAI")
