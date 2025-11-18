"""
Mapeo de voces de ElevenLabs para diferentes personajes.
"""
from typing import Dict

# Mapa de configuración de voces por personaje
VOICE_SETTINGS_MAP: Dict[str, dict] = {
    "NARRADOR":           {"voice_id": "Nh2zY9kknu6z4pZy6FhD", "speed": 1.10},
    "CHICO10":            {"voice_id": "1tDEBGOo8EqEPApM49eJ", "speed": 1.03},
    "JOVENASUSTADO":      {"voice_id": "PZasrDc3dhEdCVT9i8DU", "speed": 1.05},
    "HOMBRE25":           {"voice_id": "1MxuWc12WPRxDkgfT3kj", "speed": 1.09},
    "HOMBRE50":           {"voice_id": "W5JElH3dK1UYYAiHH7uh", "speed": 1.11},
    "HOMBRE40":           {"voice_id": "43h7ymOnaaYdWr3dRbsS", "speed": 1.10},
    "HOMBRE30":           {"voice_id": "851ejYcv2BoNPjrkw93G", "speed": 0.98},
    "ANCIANO":            {"voice_id": "DNllXe1qtnhKfoIT5C7O", "speed": 1.05},
    "CHICA12":            {"voice_id": "iKQ9dQi0t2d3zpB6iYav", "speed": 1.05},
    "MUJER20":            {"voice_id": "Ir1QNHvhaJXbAGhT50w3", "speed": 1.04},
    "MUJER30":            {"voice_id": "UOIqAnmS11Reiei1Ytkc", "speed": 1.01},
    "ANCIANA":            {"voice_id": "M9RTtrzRACmbUzsEMq8p", "speed": 1.01},
    "DUENDEMALVADO":      {"voice_id": "ZCuQxoQ9PJLqhQQnK3RJ", "speed": 1.01},
    "MONSTER":            {"voice_id": "cPoqAvGWCPfCfyPMwe4z", "speed": 1.15},
    "MUJERASUSTADA":      {"voice_id": "ZSbzc0bfesjWLjV59rru", "speed": 1.04},
    "_default":           {"voice_id": "Nh2zY9kknu6z4pZy6FhD", "speed": 1.00},
}


def clamp_speed(v: float) -> float:
    """Limita la velocidad entre 0.7 y 1.2"""
    return max(0.7, min(1.2, float(v)))


def pick_voice(speaker: str) -> tuple[str, float]:
    """
    Obtiene la configuración de voz para un personaje.

    Args:
        speaker: Nombre del personaje (ej: "NARRADOR", "HOMBRE30")

    Returns:
        Tupla con (voice_id, speed)
    """
    cfg = VOICE_SETTINGS_MAP.get(speaker.upper(), VOICE_SETTINGS_MAP["_default"])
    return cfg["voice_id"], clamp_speed(cfg.get("speed", 1.0))
