"""
Generación de ideas y nombres de proyectos.
"""
from pathlib import Path
from ..services.openai_service import OpenAIService
from ..config.styles import STYLE_IDEA_HINTS


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
        print(f"❌ Error al generar nombre de proyecto: {e}")
        return "Proyecto Sin Nombre"


def generate_automatic_idea(
    client: OpenAIService,
    style_name: str = None,
    master_list_path: Path = None
) -> str:
    """
    Genera automáticamente una idea basada en patrones virales de proyectos anteriores.

    Lee el archivo _master_project_top.txt con proyectos virales y medio virales,
    analiza patrones de éxito y genera una nueva idea original.

    Args:
        client: Cliente de OpenAI
        style_name: Nombre del estilo visual (opcional, adapta la idea al estilo)
        master_list_path: Ruta al _master_project_top.txt (default: directorio actual)

    Returns:
        Texto con la idea generada
    """
    print("\n" + "="*70)
    print("🤖 MODO AUTOMÁTICO ACTIVADO")
    print("="*70)

    # Buscar archivo master list
    if master_list_path is None:
        master_list_path = Path.cwd() / "_master_project_top.txt"

    if not master_list_path.exists():
        print(f"⚠️ No se encontró {master_list_path}")
        print("💡 Generando idea básica sin análisis de proyectos anteriores...")
        return _generate_basic_idea(client, style_name)

    # Leer el contenido del master list
    print("📖 Leyendo análisis de proyectos anteriores...")
    try:
        with open(master_list_path, "r", encoding="utf-8") as f:
            master_content = f.read()
    except Exception as e:
        print(f"❌ Error al leer el archivo: {e}")
        print("💡 Generando idea básica sin análisis de proyectos anteriores...")
        return _generate_basic_idea(client, style_name)

    # Hint opcional según el estilo visual escogido
    style_hint = ""
    if style_name:
        hint = STYLE_IDEA_HINTS.get(style_name)
        if hint:
            style_hint = f"\nADAPTACIÓN AL ESTILO VISUAL ELEGIDO:\n- Estilo visual seleccionado: {style_name}.\n- La idea debe ser coherente con este estilo:\n  {hint}\n"

    # Crear el prompt para OpenAI
    print("🧠 Analizando proyectos virales y generando nueva idea...")

    system_prompt = f"""
Eres un analista de contenido viral experto en la cuenta 'Relatos Extraordinarios'.

Tu tarea es:
1. Analizar el índice de proyectos proporcionado, que contiene SOLO los proyectos más relevantes
   (virales y medio virales) en formato resumido.
2. Identificar patrones de tono, atmósfera, tipo de misterio y construcción de gancho inicial.
3. Generar UNA SOLA idea original para un nuevo proyecto que:
   - Siga esos patrones de tensión, atmósfera y misterio.
   - Sea completamente original (no repetir temas ya hechos).
   - Tenga alto potencial viral.
   - Se centre en misterio, paranormal, leyendas españolas, lugares abandonados o historias extraordinarias.

FORMATO DE LA IDEA (MUY IMPORTANTE):
- La idea debe ser BREVE: entre 1 y 3 frases.
- Extensión aproximada: entre 30 y 90 palabras.
- Debe funcionar como una "semilla" potente, no como un relato completo.
- No desarrolles escenas largas: sugiere más de lo que explicas.
- No escribas el guion, solo la semilla de concepto.

RESTRICCIONES TEMÁTICAS (OBLIGATORIAS):
- PROHIBIDO basar la historia en coches, carreteras, autopistas, camioneros, conductores o viajes en vehículo.
- PROHIBIDO que la escena principal sea una carretera o un viaje nocturno.
- La historia debe ocurrir en un LUGAR ESTÁTICO o muy acotado:
  casas, edificios, hospitales, cementerios, bosques, pueblos abandonados, fábricas, túneles, minas, barcos, ruinas, etc.

PROTAGONISTA ÚNICO (OBLIGATORIO):
- La idea debe girar alrededor de UN SOLO protagonista claro.
- Puede haber otros personajes, pero SIEMPRE hay una figura central que lleva el peso de la historia.
- Evita ideas basadas en grupos donde nadie destaque como protagonista.

RESTRICCIONES DE ESTILO (OBLIGATORIAS):
- NO empieces el texto con "Medianoche", "A medianoche", "Eran las doce", "A las doce" ni variaciones.
- Varía los comienzos: puedes empezar por una imagen, un sonido, una sensación, un objeto, una regla extraña, etc.
- No reutilices literalmente nombres de proyectos, lugares o frases completas del índice.
- Inspírate en los patrones del índice, pero combina los elementos de forma nueva y sorprendente.

{style_hint}

IMPORTANTE:
- Responde SOLO con la idea del nuevo proyecto, sin explicaciones adicionales.
- No incluyas títulos ni encabezados, solo el texto de la idea.
- El tono debe ser narrativo y sugerente, como tus ejemplos manuales, pero dejando margen para que otro modelo desarrolle el guion.
""".strip()

    user_prompt = f"""
A continuación tienes un índice curado con los proyectos más exitosos de la cuenta
(virales y medio virales), cada uno con un breve resumen:

{master_content}

Genera UNA idea original para el siguiente proyecto que tenga alto potencial viral y
siga los patrones de misterio y atmósfera de estos ejemplos, sin copiarlos literalmente.
""".strip()

    try:
        last_idea = None

        # Hasta 3 intentos por si el modelo insiste con coches / carreteras / medianoches
        for attempt in range(3):
            response = client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="gpt-5.1"
            )

            new_idea = response.strip()
            last_idea = new_idea

            idea_lower = new_idea.lower()

            # Palabras y temas que queremos evitar en la semilla
            banned_words = [
                "carretera", "autopista", "arcén", "arcen",
                "camión", "camionero", "camioneros",
                "coche", "coches", "volante",
                "conducía", "conduce", "conducir",
                "taxi", "autobús", "autobus",
                "carretera comarcal", "kilómetro", "km"
            ]

            # Arranques que no queremos repetir
            bad_starts = [
                "medianoche", "a medianoche",
                "eran las doce", "a las doce",
                "es medianoche"
            ]

            starts_bad = any(idea_lower.startswith(s) for s in bad_starts)
            contains_banned = any(w in idea_lower for w in banned_words)

            # Chequeo de longitud aproximada
            word_count = len(new_idea.split())
            longitud_ok = 20 <= word_count <= 120

            if not starts_bad and not contains_banned and longitud_ok:
                # ✅ Idea válida
                print("\n" + "="*70)
                print("💡 NUEVA IDEA GENERADA:")
                print("="*70)
                print(new_idea)
                print("="*70 + "\n")
                return new_idea
            else:
                print(f"⚠️ Intento {attempt + 1}/3: Idea con tema o inicio no deseado, o longitud rara. Reintentando...")
                if starts_bad:
                    print("   ↳ Motivo: inicio tipo 'medianoche' o similar.")
                if contains_banned:
                    print("   ↳ Motivo: referencia a coche/carretera/viaje.")
                if not longitud_ok:
                    print(f"   ↳ Motivo: longitud fuera de rango (palabras: {word_count}).")

        # Si después de 3 intentos no conseguimos una idea perfecta, usamos la última pero avisamos
        print("⚠️ No se pudo obtener una idea que cumpla todas las restricciones tras varios intentos.")
        if last_idea:
            print("\n" + "="*70)
            print("💡 ÚLTIMA IDEA GENERADA (se utilizará de todas formas):")
            print("="*70)
            print(last_idea)
            print("="*70 + "\n")
        return last_idea

    except Exception as e:
        print(f"❌ Error al generar idea automática: {e}")
        print("💡 Generando idea básica de respaldo...")
        return _generate_basic_idea(client, style_name)


def _generate_basic_idea(client: OpenAIService, style_name: str = None) -> str:
    """
    Genera una idea básica sin análisis de proyectos anteriores.

    Args:
        client: Cliente de OpenAI
        style_name: Nombre del estilo visual (opcional)

    Returns:
        Texto con idea básica
    """
    system_prompt = """
Eres un generador de ideas para historias cortas de terror, misterio y suspenso.
Genera una idea original y concisa (2-3 frases) para una dramatización de audio.

Requisitos:
- Debe ser atmosférica y visual
- Un solo protagonista claro
- Situación intrigante o inquietante
- Ambientación específica y evocadora
- Entre 30 y 90 palabras
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
        print(f"❌ Error al generar idea básica: {e}")
        return "Un investigador encuentra un objeto misterioso que cambia su percepción de la realidad."
