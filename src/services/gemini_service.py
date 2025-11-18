"""
Servicio para interactuar con Google Gemini (generación de imágenes).
"""
from google import genai
from google.genai import types
from ..config.settings import GEMINI_API_KEY


class GeminiService:
    """Cliente para Google Gemini."""

    def __init__(self, api_key: str = None):
        """
        Inicializa el cliente de Gemini.

        Args:
            api_key: Clave API de Gemini. Si no se proporciona, usa la del config.
        """
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY no configurada")

        self.client = genai.Client(api_key=self.api_key)

    def generate_image(self, prompt: str, aspect_ratio: str = "9:16",
                      number_of_images: int = 1, **kwargs):
        """
        Genera imágenes con Gemini.

        Args:
            prompt: Descripción de la imagen
            aspect_ratio: Ratio de aspecto (ej: "9:16", "1:1")
            number_of_images: Número de imágenes a generar
            **kwargs: Argumentos adicionales

        Returns:
            Respuesta de la API con las imágenes generadas
        """
        try:
            response = self.client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config=types.GenerateImageConfig(
                    aspect_ratio=aspect_ratio,
                    number_of_images=number_of_images,
                    **kwargs
                )
            )
            return response
        except Exception as e:
            raise RuntimeError(f"Error al generar imagen con Gemini: {e}")

    # Nota: Para la lógica compleja de consistencia visual y brief,
    # consulta el archivo original create_project.py líneas 926-1358
