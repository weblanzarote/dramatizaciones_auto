"""
Lógica de consistencia visual entre escenas.
Gestiona el "brief" de personajes, escenarios y atmósfera.
"""
import json
from typing import Dict
from ..services.openai_service import OpenAIService


def extract_visual_consistency_brief(script_text: str, client: OpenAIService,
                                     model_type: str = "gemini") -> dict:
    """
    Analiza el guion completo y extrae un brief visual de consistencia.

    Devuelve siempre un diccionario con estas claves:
    {
        "character": "...",
        "environment": "...",
        "lighting": "...",
        "objects": "..."
    }

    Args:
        script_text: Texto completo del guion
        client: Cliente de OpenAI
        model_type: "gemini" (detallado) o "qwen" (compacto)

    Returns:
        Dict con el brief de consistencia
    """
    print(f"📋 Analizando guión para extraer brief de consistencia (Modo: {model_type})...")

    # Prompt para Gemini (detallado)
    system_prompt_gemini = """
Eres director de arte. Debes crear un 'visual brief' MUY CONCRETO para que un modelo de imágenes
mantenga consistencia visual en toda la historia.

Lee el guion y responde EXCLUSIVAMENTE con un JSON válido de esta forma:

{
  "character": "Descripción del personaje principal (si lo hay). Puede estar vacío si no es relevante.",
  "environment": "Descripción del escenario o ubicación recurrente.",
  "lighting": "Descripción de la iluminación y atmósfera general (paleta, tono).",
  "objects": "Objetos o símbolos que deban ser consistentes."
}

REGLAS IMPORTANTES:
- NO añadas más claves.
- NO añadas comentarios ni texto fuera del JSON.
- Si el guion está narrado en primera persona, asume que esa voz es el personaje principal.
- No uses opciones tipo "o", "/" ni alternativas. Fija una sola versión de cada cosa.
"""

    # Prompt para Qwen (compacto)
    system_prompt_qwen = """
Eres director de arte para un modelo de imágenes con límite de tokens.

Lee el guion y responde SOLO con un JSON válido:

{
  "character": "...",
  "environment": "...",
  "lighting": "...",
  "objects": "..."
}

REGLAS:
- Máxima prioridad: "character" debe describir de forma muy específica al personaje principal
  (edad aproximada, género, rasgos de cara, color y peinado de pelo, ropa FIJA, colores exactos).
- "environment": resume el tipo de lugar principal y su estado (nuevo, gastado, hospital, bosque, etc.).
- "lighting": resume la atmósfera (oscuro, frío, neón, velas, etc.).
- "objects": solo si hay elementos recurrentes (libro, foto, cruz, caja, etc.), si no, pon cadena vacía.
- No escribas nada fuera del JSON.
"""

    final_system_prompt = system_prompt_qwen if model_type == "qwen" else system_prompt_gemini

    if model_type == "qwen":
        print("   (Usando brief corto estructurado para Qwen/Runware)")
    else:
        print("   (Usando brief estructurado para Gemini)")

    try:
        brief_dict = client.chat_completion(
            messages=[
                {"role": "system", "content": final_system_prompt},
                {"role": "user", "content": f"Guion a analizar:\n\n{script_text}"}
            ],
            model="gpt-5.1",
            response_format={"type": "json_object"}
        )
        print(f"✅ Brief visual estructurado ({model_type}) extraído:\n{brief_dict}\n")
        return brief_dict

    except Exception as e:
        print(f"⚠️ No se pudo extraer brief visual estructurado: {e}")
        # Fallback: devolver estructura vacía
        return {
            "character": "",
            "environment": "",
            "lighting": "",
            "objects": ""
        }


def ensure_brief_dict(brief) -> dict:
    """
    Garantiza que el brief sea siempre un dict con las claves esperadas.

    Args:
        brief: Brief que puede ser dict, string o None

    Returns:
        Dict normalizado con todas las claves
    """
    default = {
        "character": "",
        "environment": "",
        "lighting": "",
        "objects": ""
    }

    if not brief:
        return default

    if isinstance(brief, dict):
        merged = default.copy()
        merged.update({k: v for k, v in brief.items() if k in default})
        return merged

    # Si por lo que sea llega un string, lo metemos en 'character' como fallback
    default["character"] = str(brief)
    return default


def classify_scene_for_brief(scene_audio: str) -> dict:
    """
    Dado el TEXTO DE AUDIO asociado a una escena, decide qué partes del brief
    tienen sentido para esa imagen.

    Args:
        scene_audio: Texto de audio de la escena

    Returns:
        Dict de flags: include_character, include_environment, include_objects
    """
    text = (scene_audio or "").lower()

    # Tokens para detectar elementos
    character_tokens = [
        "él ", "ella ", "hombre", "mujer", "niño", "niña", "joven",
        "señor", "señora", "anciano", "anciana", "yo ", "mi ", "me ",
        "narrador", "protagonista"
    ]
    environment_tokens = [
        "habitación", "pasillo", "bosque", "calle", "casa", "piso", "sótano",
        "hospital", "clínica", "escuela", "parque", "cementerio", "iglesia",
        "plaza", "cocina", "salón", "dormitorio", "carretera", "túnel"
    ]
    object_tokens = [
        "foto", "fotografía", "retrato", "caja", "libro", "diario", "llave",
        "puñal", "muñeca", "cajón", "cámara", "teléfono", "cinta",
        "cruz", "medalla", "collar"
    ]

    include_character = any(tok in text for tok in character_tokens)
    include_environment = any(tok in text for tok in environment_tokens)
    include_objects = any(tok in text for tok in object_tokens)

    return {
        "include_character": include_character,
        "include_environment": include_environment,
        "include_objects": include_objects,
    }


def build_consistency_context_for_scene(
    brief_dict: dict,
    include_character: bool,
    include_environment: bool,
    include_objects: bool,
    total_scenes: int
) -> str:
    """
    Construye un BRIEF muy compacto para esta escena.

    Args:
        brief_dict: Brief de consistencia completo
        include_character: ¿Incluir info del personaje?
        include_environment: ¿Incluir info del escenario?
        include_objects: ¿Incluir info de objetos?
        total_scenes: Total de escenas (para contexto)

    Returns:
        String con el contexto de consistencia para esta escena
    """
    parts = []

    if include_character and brief_dict.get("character"):
        parts.append(f"personaje_principal: {brief_dict['character']}")
    if include_environment and brief_dict.get("environment"):
        parts.append(f"escenario: {brief_dict['environment']}")
    if brief_dict.get("lighting"):
        # La iluminación ayuda mucho a la coherencia, la mantenemos siempre
        parts.append(f"iluminacion: {brief_dict['lighting']}")
    if include_objects and brief_dict.get("objects"):
        parts.append(f"objetos_recurrentes: {brief_dict['objects']}")

    # Unimos todo en una sola frase de contexto
    if parts:
        return "contexto_consistencia: " + " | ".join(parts)
    else:
        return ""
