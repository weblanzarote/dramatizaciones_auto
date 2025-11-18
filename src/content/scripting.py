"""
Generación de guiones y prompts visuales.
"""
import json
import re
from ..services.openai_service import OpenAIService


def generate_creative_content(idea: str, client: OpenAIService) -> dict:
    """
    Genera guion y contenido para redes sociales a partir de una idea.

    Args:
        idea: Texto con la idea del proyecto
        client: Cliente de OpenAI

    Returns:
        Dict con keys "script" y "social_post"
    """
    # Esta función es muy larga. Ver create_project.py líneas 68-198
    # Aquí una versión simplificada:

    system_prompt = """
Eres un guionista experto en misterio y terror.
Genera un JSON con dos claves:
{
  "script": "...",
  "social_post": "..."
}

El script debe:
- Tener entre 8 y 14 bloques
- Cada bloque: máximo 15 palabras
- Formato: [SPEAKER]\n[imagen:X.png]\nTEXTO\n
- Terminar con [CIERRE]
- Un solo protagonista principal

El social_post debe:
- Máximo 300 caracteres
- Incluir #RelatosExtraordinarios
"""

    try:
        content = client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Genera el contenido para: {idea}"}
            ],
            model="gpt-5.1",
            response_format={"type": "json_object"}
        )

        # Garantizar que las imágenes se mantengan en PNG
        if "script" in content:
            content["script"] = content["script"].replace(".mp4", ".png")

        return content
    except Exception as e:
        print(f"Error al generar contenido creativo: {e}")
        return None


def generate_visual_prompts_for_script(script_text: str, client: OpenAIService) -> list:
    """
    Analiza un guion y genera prompts visuales cinematográficos para cada escena.

    Args:
        script_text: Texto completo del guion
        client: Cliente de OpenAI

    Returns:
        Lista de prompts visuales (uno por cada [imagen:X.png])
    """
    # Ver implementación completa en create_project.py líneas 201-329

    # Contar cuántas imágenes necesitamos
    scene_tags = re.findall(r'\[imagen:(\d+)\.png\]', script_text)
    num_scenes = len(scene_tags)

    if num_scenes == 0:
        print("No se encontraron etiquetas [imagen:X.png]")
        return []

    system_prompt = f"""
Eres Director de Arte y Fotografía.
Genera {num_scenes} prompts visuales cinematográficos, uno por cada escena [imagen:X.png].

Responde con JSON:
{{
  "visual_prompts": ["prompt 1", "prompt 2", ...]
}}

Cada prompt: 300-600 caracteres, muy cinematográfico y detallado.
"""

    try:
        content = client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Guion:\n\n{script_text}"}
            ],
            model="gpt-5.1",
            response_format={"type": "json_object"}
        )

        prompts_list = content.get("visual_prompts", [])

        if len(prompts_list) != num_scenes:
            print(f"Error: se generaron {len(prompts_list)} prompts, esperados {num_scenes}")
            return []

        return prompts_list
    except Exception as e:
        print(f"Error al generar prompts visuales: {e}")
        return []


def rewrite_prompt_for_safety(prompt_text: str, client: OpenAIService) -> str:
    """
    Reescribe un prompt bloqueado por filtros de seguridad.

    Args:
        prompt_text: Prompt original bloqueado
        client: Cliente de OpenAI

    Returns:
        Prompt reescrito de forma segura
    """
    system_prompt = """
Eres un asistente que reformula prompts para generadores de imágenes.
El siguiente prompt fue bloqueado. Reescríbelo usando lenguaje neutro y seguro,
evitando palabras que impliquen sufrimiento, violencia o contenido sensible.
Responde solo con el prompt reformulado.
"""

    try:
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_text}
            ],
            model="gpt-5.1"
        )
        return response.strip()
    except Exception as e:
        print(f"Error al reescribir prompt: {e}")
        return prompt_text
