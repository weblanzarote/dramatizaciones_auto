"""
Generación de ideas y nombres de proyectos.
"""
from ..services.openai_service import OpenAIService


def generate_project_name_from_idea(idea_text: str, client: OpenAIService) -> str:
    """
    Genera un nombre corto y descriptivo para un proyecto basado en la idea.

    Args:
        idea_text: Texto de la idea del proyecto
        client: Cliente de OpenAI

    Returns:
        Nombre del proyecto (3-6 palabras)
    """
    system_prompt = """
Eres un asistente que genera nombres cortos y descriptivos para proyectos de video.
Responde SOLO con el nombre del proyecto, sin comillas ni explicaciones.

Reglas:
- Máximo 6 palabras
- Descriptivo y memorable
- En español
- Sin artículos innecesarios al inicio
- Usa sustantivos y adjetivos impactantes
"""

    try:
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Idea del proyecto: {idea_text}"}
            ],
            model="gpt-5.1"
        )
        return response.strip()
    except Exception as e:
        print(f"Error al generar nombre de proyecto: {e}")
        return "Proyecto Sin Nombre"


def generate_automatic_idea(client: OpenAIService, style_name: str = None) -> str:
    """
    Genera automáticamente una idea para un proyecto de terror/misterio.

    Args:
        client: Cliente de OpenAI
        style_name: Nombre del estilo visual (opcional, para adaptar la idea)

    Returns:
        Texto con la idea generada
    """
    # Implementación completa en create_project.py líneas 1790-1950
    # Por simplicidad, aquí una versión básica:

    system_prompt = """
Eres un generador de ideas para historias cortas de terror, misterio y suspenso.
Genera una idea original y concisa (2-3 frases) para una dramatización de audio.

Requisitos:
- Debe ser atmosférica y visual
- Un solo protagonista claro
- Situación intrigante o inquietante
- Ambientación específica y evocadora
"""

    if style_name:
        system_prompt += f"\n\nAdapta la idea al estilo visual: {style_name}"

    try:
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Genera una idea original de terror/misterio"}
            ],
            model="gpt-5.1"
        )
        return response.strip()
    except Exception as e:
        print(f"Error al generar idea automática: {e}")
        return "Un investigador encuentra un objeto misterioso que cambia su percepción de la realidad."
