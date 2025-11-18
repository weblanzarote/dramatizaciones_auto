"""
Servicio para interactuar con Runware (generación y animación de imágenes).
"""
from ..config.settings import RUNWARE_API_KEY, QWEN_AIR_ID

# Intentar importar Runware
try:
    from runware import Runware, IVideoInference, IFrameImage, IImageInference
    import asyncio
    RUNWARE_AVAILABLE = True
except ImportError:
    RUNWARE_AVAILABLE = False
    Runware = None


class RunwareService:
    """Cliente para Runware."""

    def __init__(self, api_key: str = None):
        """
        Inicializa el servicio de Runware.

        Args:
            api_key: Clave API de Runware. Si no se proporciona, usa la del config.
        """
        if not RUNWARE_AVAILABLE:
            raise ImportError(
                "Runware no está instalado. Ejecuta: pip install runware"
            )

        self.api_key = api_key or RUNWARE_API_KEY
        if not self.api_key:
            raise ValueError("RUNWARE_API_KEY no configurada")

    async def generate_image(self, prompt: str, negative_prompt: str = "",
                           model_id: str = QWEN_AIR_ID, **kwargs):
        """
        Genera una imagen con Runware (async).

        Args:
            prompt: Descripción de la imagen
            negative_prompt: Prompt negativo
            model_id: ID del modelo a usar
            **kwargs: Argumentos adicionales

        Returns:
            Respuesta de la API con la imagen generada
        """
        # Implementación completa en create_project.py líneas 1359-1599
        raise NotImplementedError(
            "Ver create_project.py::generate_visuals_for_script para implementación completa"
        )

    async def animate_image(self, image_path: str, **kwargs):
        """
        Anima una imagen estática (async).

        Args:
            image_path: Ruta a la imagen
            **kwargs: Argumentos adicionales

        Returns:
            Path al video generado
        """
        # Implementación completa en create_project.py líneas 1600-1698
        raise NotImplementedError(
            "Ver create_project.py::animate_images_with_runware para implementación completa"
        )


def is_runware_available() -> bool:
    """Verifica si Runware está disponible."""
    return RUNWARE_AVAILABLE
