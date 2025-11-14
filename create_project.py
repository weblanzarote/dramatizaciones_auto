import os
import shutil
import time
import sys
import base64
from dotenv import load_dotenv
import subprocess
import argparse
import json
import re
import requests
import textwrap
from PIL import Image
from openai import OpenAI
import openai
from google import genai
from google.genai import types

# --- CONFIGURACIÓN INICIAL ---
# Cargar claves de API de forma segura desde el archivo .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("No se encontró la OPENAI_API_KEY. Asegúrate de que tu archivo .env está configurado.")

# Inicializamos el cliente de OpenAI que se usará para texto
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    raise RuntimeError(f"Error al inicializar el cliente de OpenAI: {e}")

# Configuración de Google Gemini para generación de imágenes
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("No se encontró la GEMINI_API_KEY. Asegúrate de que tu archivo .env está configurado.")

# Inicializamos el cliente de Gemini para generación de imágenes
try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    print("✅ Cliente de Google Gemini inicializado correctamente")
except Exception as e:
    raise RuntimeError(f"Error al inicializar el cliente de Gemini: {e}")

# Configuración de Runware (opcional, solo si se usa --animate-images)
RUNWARE_API_KEY = os.getenv("RUNWARE_API_KEY")
runware_available = False
if RUNWARE_API_KEY:
    try:
        from runware import Runware, IVideoInference, IFrameImage
        import asyncio
        runware_available = True
    except ImportError:
        print("⚠️  Advertencia: 'runware' no está instalado. Ejecuta: pip install runware")
    except Exception as e:
        print(f"⚠️  Advertencia: Error al inicializar Runware: {e}")


# --- 1. GENERACIÓN DE CONTENIDO CREATIVO CON OPENAI (gpt-5.1) ---
def generate_creative_content(idea: str):
    """Llama a la API de OpenAI (gpt-5.1) para obtener guion, post y texto para redes."""
    print(f"🧠 Generando contenido creativo con OpenAI (gpt-5.1) para la idea: '{idea}'...")

    # Prompt optimizado para GPT-5.1 con énfasis en calidad narrativa y cinematográfica
    system_prompt = """
    Eres un guionista experto especializado en narrativas de misterio, terror y contenido paranormal viral.
    Creas historias cortas pero cinematográficas para 'Relatos Extraordinarios' con estructura de novela gráfica.
    Generarás un objeto JSON con tres claves: "script", "blog_article" y "social_post".

    Reglas para "script" - NARRATIVA CINEMATOGRÁFICA:

    ESTRUCTURA TÉCNICA (MUY ESTRICTA):
    - Cada escena sigue este formato exacto:
      1. Tag de hablante en su propia línea: `[NARRADOR]`
      2. Tag de imagen en la siguiente línea: `[imagen:1.mp4]` (DÍGITOS numéricos: 1, 2, 3...)
      3. Texto descriptivo de la escena (12-15 palabras máximo - CONCISO y PRECISO)
      4. Línea en blanco entre escenas

    Ejemplo correcto:
    [NARRADOR]
    [imagen:1.mp4]
    En los valles más profundos, donde la niebla nunca se disipa, se susurran leyendas.

    PARÁMETROS:
    - Total: 6-10 escenas (flexibilidad narrativa para contar bien la historia)
    - Total de palabras: 80-140 palabras
    - Duración objetivo: ~60 segundos de video final
    - Numeración: Usar DÍGITOS en tags [imagen:1.mp4] NO palabras
    - Números en texto narrativo: Escribir con letras ("mil novecientos cincuenta")
    - Finalizar obligatoriamente con tag `[CIERRE]` en su propia línea

    CALIDAD NARRATIVA (GPT-5.1 - máxima creatividad):

    ESTILO DE ESCRITURA - MUY IMPORTANTE:
    - Usa ORACIONES COMPLETAS con VERBOS CONJUGADOS en tiempo presente o pasado
    - Escribe narración FLUIDA y NATURAL, como si alguien contara una historia en voz alta
    - EVITA estilo telegráfico, fragmentado o técnico (sin punto y coma excesivo)
    - Cada escena debe sonar bien al leerla en voz alta para narración de audio

    Ejemplo CORRECTO de narración fluida:
    "En los valles más profundos, donde la niebla nunca se disipa, se susurran leyendas olvidadas.
    Los ancianos del pueblo hablan en voz baja de lo que vieron aquella noche."

    Ejemplo INCORRECTO (evitar):
    "Plano aéreo de valles profundos, niebla persistente; leyendas susurradas, ancianos narrando en voz baja."

    CONTENIDO NARRATIVO:
    - Construye una progresión dramática clara: presentación → tensión creciente → clímax → resolución/giro
    - Cada escena debe ser VISUALMENTE EVOCADORA pero narrada con naturalidad
    - Mantén UN elemento o personaje central recurrente para coherencia visual
    - Crea atmósfera con detalles sensoriales: texturas, luces, sombras, sonidos
    - Describe lo que SE VE y SE SIENTE, no técnicas de cámara
    - Evita clichés: busca giros originales y detalles inesperados que generen intriga
    - Usa lenguaje evocador pero accesible, no rebuscado ni artificioso
    
    Reglas para "blog_article":
    - Debe expandir la historia del guion con un tono objetivo.
    - El formato debe ser compatible con Google Docs, usando títulos de sección más grandes.
    - Debe finalizar siempre con 5 palabras clave separadas por comas (sin #).

    Reglas para "social_post":
    - Descripción corta e impactante para TikTok (<300 caracteres).
    - No puede empezar con "Te atreves", "Descubre", "Conoces" o "Conocías".
    - Debe incluir siempre el hashtag #RelatosExtraordinarios y hasta 4 hashtags más muy relevantes.
    
    Responde únicamente con el objeto JSON solicitado, sin texto adicional.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-5.1",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Genera el contenido para la siguiente idea: {idea}"}
            ]
        )

        content = json.loads(response.choices[0].message.content)
        print("✅ Contenido creativo generado con éxito.")
        return content

    except Exception as e:
        print(f"❌ Error al generar contenido con OpenAI (gpt-5-mini): {e}")
        return None
        
def rewrite_prompt_for_safety(prompt_text: str, client: OpenAI):
    """Llama a un modelo de texto para reescribir un prompt bloqueado."""
    print("✍️  Reescribiendo el prompt para evitar filtros de seguridad...")
    try:
        response = client.chat.completions.create(
            model="gpt-5-nano", # Usamos un modelo rápido y barato para esta tarea simple
            messages=[
                {"role": "system", "content": (
                    "Eres un asistente que reformula prompts para un generador de imágenes. "
                    "El siguiente prompt fue bloqueado por un filtro de seguridad. "
                    "Tu tarea es reescribirlo para describir una escena visualmente similar, "
                    "pero usando un lenguaje neutro y seguro, evitando palabras que impliquen "
                    "sufrimiento, violencia, 'plagas', 'trastornos' o cualquier contenido sensible. "
                    "Responde únicamente con el prompt reformulado, sin explicaciones."
                )},
                {"role": "user", "content": prompt_text}
            ]
        )
        rewritten_prompt = response.choices[0].message.content.strip()
        print(f"✅ Nuevo prompt generado: '{rewritten_prompt[:80]}...'")
        return rewritten_prompt
    except Exception as e:
        print(f"❌ Error al intentar reescribir el prompt: {e}")
        return None
        
def pixelize_image(path: str, small_edge: int = 256):
    """
    Downscale fuerte y upscale con NEAREST para píxel gordo retro.
    Ajusta small_edge: 256 (suave), 192/160/128 (más “chunky”).
    """
    try:
        im = Image.open(path).convert("RGBA")
        w, h = im.size
        if w < h:
            new_w = small_edge
            new_h = int(h * (small_edge / w))
        else:
            new_h = small_edge
            new_w = int(w * (small_edge / h))
        small = im.resize((max(1, new_w), max(1, new_h)), Image.BILINEAR)
        up = small.resize((w, h), Image.NEAREST)
        try:
            up = up.convert("P", palette=Image.ADAPTIVE, colors=48).convert("RGBA")
        except Exception:
            pass
        up.save(path)
    except Exception as e:
        print(f"  (postproceso pixelize falló: {e})")
        

# --- MENÚ INTERACTIVO PARA SELECCIÓN DE MODELO ---
def interactive_model_selection():
    """Menú interactivo para seleccionar modelo y calidad de imagen."""
    print("\n" + "="*70)
    print("🎨 CONFIGURACIÓN DE GENERACIÓN DE IMÁGENES")
    print("="*70)
    print("\nSelecciona el modelo de generación de imágenes:\n")

    models = [
        {
            "name": "GPT Image 1 Mini - Calidad BAJA",
            "model": "gpt-image-1-mini",
            "quality": "low",
            "cost": "$0.06 por 10 imágenes",
            "note": "Más económico, calidad básica"
        },
        {
            "name": "GPT Image 1 Mini - Calidad MEDIA",
            "model": "gpt-image-1-mini",
            "quality": "medium",
            "cost": "$0.15 por 10 imágenes",
            "note": "Buen balance calidad/precio (RECOMENDADO)"
        },
        {
            "name": "GPT Image 1 - Calidad MEDIA",
            "model": "gpt-image-1",
            "quality": "medium",
            "cost": "$0.63 por 10 imágenes",
            "note": "Mayor calidad GPT Image"
        },
        {
            "name": "GPT Image 1 - Calidad ALTA",
            "model": "gpt-image-1",
            "quality": "high",
            "cost": "$2.50 por 10 imágenes",
            "note": "Máxima calidad GPT Image"
        },
        {
            "name": "DALL-E 2 - Standard",
            "model": "dall-e-2",
            "quality": "standard",
            "cost": "$0.20 por 10 imágenes",
            "note": "Económico, tamaño 1024x1024 (cuadrado)"
        },
        {
            "name": "DALL-E 3 - Standard",
            "model": "dall-e-3",
            "quality": "standard",
            "cost": "$0.80 por 10 imágenes",
            "note": "Alta calidad, garantizado"
        },
        {
            "name": "DALL-E 3 - HD",
            "model": "dall-e-3",
            "quality": "hd",
            "cost": "$1.20 por 10 imágenes",
            "note": "Máxima calidad, más detalle"
        }
    ]

    for i, m in enumerate(models, 1):
        print(f"{i}. {m['name']}")
        print(f"   💰 {m['cost']} | {m['note']}")
        print()

    while True:
        try:
            choice = input("Elige una opción (1-7) [default: 2]: ").strip()
            if choice == "":
                choice = "2"

            idx = int(choice) - 1
            if 0 <= idx < len(models):
                selected = models[idx]
                print(f"\n✅ Seleccionado: {selected['name']}")
                print(f"   Modelo: {selected['model']} | Calidad: {selected['quality']}")
                print(f"   Costo estimado: {selected['cost']}")
                print("="*70 + "\n")
                return selected['model'], selected['quality']
            else:
                print("❌ Opción inválida. Elige un número del 1 al 7.")
        except ValueError:
            print("❌ Por favor, introduce un número válido.")
        except KeyboardInterrupt:
            print("\n\n❌ Cancelado por el usuario.")
            sys.exit(0)


# ===== ESTILOS DE IMAGEN (presets) =====
STYLE_PRESETS = [
    ("Novela Gráfica Oscura (horror gótico cinematográfico)", textwrap.dedent("""\
    Ilustración estilo novela gráfica moderna y cómic de autor, con estética de horror gótico cinematográfico.

    Características visuales esenciales:
    - Estilo de cómic adulto de alta calidad con narrativa visual cinematográfica
    - Composición dramática pensada para encuadres verticales tipo storyboard de película
    - Tonos oscuros y atmosféricos: negros profundos, grises ricos, azules nocturnos, sepias envejecidos
    - Iluminación claroscuro dramática con sombras profundas que resaltan tensión y misterio
    - Alto nivel de detalle en texturas, arquitectura y elementos ambientales
    - Calidad cinematográfica en la composición de cada escena, como fotogramas de una película de terror gótico

    Atmósfera narrativa:
    - Sensación de horror gótico elegante, no gore explícito sino tensión psicológica
    - Personajes definidos con rasgos faciales consistentes, expresiones intensas y emotivas
    - Elementos arquitectónicos detallados (edificios antiguos, calles empedradas, interiores decadentes)
    - Ambiente cargado de niebla, polvo en suspensión, lluvia o nieve según la escena
    - Paleta de color reducida pero sofisticada, con acentos cálidos puntuales (ámbar, rojo sangre, dorado viejo)

    Coherencia visual entre escenas:
    - Los personajes deben mantener exactamente la misma apariencia física, ropa y estilo
    - El tratamiento de luz y sombra debe ser consistente en toda la narrativa
    - La textura gráfica y el nivel de detalle deben permanecer uniformes
    - Todas las imágenes deben sentirse parte del mismo universo visual oscuro
    """).strip()),

    ("Fábulas Nocturnas (animales simbólicos)", textwrap.dedent("""\
    Crea una ilustración con animales antropomorfos que encarnan roles humanos
    (por ejemplo, un cuervo mensajero vigilante, un zorro astuto, un gato errante melancólico).
    Estilo visual:
    - Tonos nocturnos con bruma y luz teatral.
    - Sombras largas y enfoque narrativo en la pose.
    - Paleta reducida con un único color de acento emocional.
    - Sensación de fábula oscura y cuento moderno.
    """).strip()),

    ("Tinta + Acento (monocromo)", textwrap.dedent("""\
    Ilustración monocromática estilo tinta, con un único color de acento que resalte un objeto o emoción.
    Estilo visual:
    - Alto contraste, negros profundos y blancos limpios.
    - Textura de pincel seco, bordes ligeramente irregulares.
    - Sensación de novela negra / cómic adulto.
    - Minimalista y muy gráfico.
    """).strip()),

    ("Pincel Expresionista (pintura digital)", textwrap.dedent("""\
    Pintura digital expresionista con pinceladas visibles.
    Estilo visual:
    - Formas sugeridas más que definidas, bordes suaves.
    - Luces y sombras dramáticas de estilo cinematográfico.
    - Colores ligeramente desaturados con estallidos puntuales de color intenso.
    - Apariencia de concept art de una película.
    """).strip()),

    ("Diorama de Papel (teatro de sombras)", textwrap.dedent("""\
    Ilustración estilo diorama de papel recortado.
    Estilo visual:
    - Planos superpuestos como capas de cartulina.
    - Sombras proyectadas para dar profundidad.
    - Personajes y objetos con bordes nítidos tipo recorte.
    - Iluminación lateral o contraluz, aspecto artesanal teatral.
    """).strip()),

    ("Anime Nocturno (línea + cel shading)", textwrap.dedent("""\
    Ilustración con estética anime japonesa contemporánea.
    Estilo visual:
    - Dibujo de contorno claro (línea limpia) y cel shading en 2–3 niveles.
    - Proporciones estilizadas, ojos expresivos, gestos claros.
    - Colores planos con sombras definidas; brillos de lluvia y neón.
    - Fondo con perspectiva profunda y niebla azulada.
    - Evita textura pictórica; evita pinceladas sueltas; evita realismo fotográfico.
    """).strip()),

    ("Ghibli Melancólico (acuarela suave)", textwrap.dedent("""\
    Ilustración inspirada en estudios Ghibli.
    Estilo visual:
    - Colores suaves, aspecto de acuarela; contornos discretos.
    - Luz cálida envolvente, atmósfera de nostalgia y calma.
    - Detalles naturales (hojas, viento, lluvia delicada) integrados en la escena.
    - Siluetas redondeadas, formas amables y composición contemplativa.
    - Evita texturas agresivas y contrastes extremos; evita noir duro.
    """).strip()),

    ("Pixar Cinemático (3D suave)", textwrap.dedent("""\
    Ilustración con look de animación tipo Pixar.
    Estilo visual:
    - Volúmenes suaves y materiales limpios; sensación 3D con iluminación global suave.
    - Luces volumétricas; reflejos sutiles en suelo mojado.
    - Personajes con proporciones caricaturizadas y expresividad clara.
    - Paleta viva pero controlada: fríos nocturnos con un acento cálido.
    - Evita grano fílmico y brochazos; evita blanco y negro.
    """).strip()),

    ("Pixel Noir (8-bit, 16x16 tiles)", textwrap.dedent("""\
    Ilustración estilo pixel art retro.
    Requisitos de estilo:
    - Píxeles grandes y visiblemente cuadriculados (grid perceptible), sin anti-aliasing.
    - Paleta limitada de 16–32 colores; evita degradados suaves.
    - Sombreado con dithering y rampas de color cortas; contornos 1–2 px.
    - Composición clara pensada para tiles 16x16. Evita brochazos, blur y look fotográfico.
    """).strip()),

    ("Pixel Art Isométrico RPG (16×16 tiles)", textwrap.dedent("""\
    Ilustración en estilo pixel art isométrico (3/4 view) como un RPG clásico.
    - Cámara elevada 3/4; líneas ~30–35°, horizonte alto.
    - Paleta 24–48 colores; píxel grueso, contornos oscuros; bloques planos.
    - Sombreado por bloques y dithering; suelo/objetos en tiles 16×16 (tileable).
    - Objetos alineados a rejilla; proporciones tipo sprite; sin blur ni realismo fotográfico.
    """).strip()),
]
STYLE_NAMES = [n for n, _ in STYLE_PRESETS]

def build_master_prompt(style_block: str, scene_text: str) -> str:
    return (
        style_block.strip() + "\n\n"
        "Dirección visual adicional:\n"
        "- Encuadre cinematográfico pensado para vídeo vertical 9:16.\n"
        "- Sensación de fotograma de una misma historia o universo visual.\n"
        "- Mantén atmósfera evocadora y narrativa.\n\n"
        "Escena específica a ilustrar:\n" + scene_text.strip()
    )

def interactive_style_selection():
    print("\n" + "="*70)
    print("🎨 ESTILO VISUAL")
    print("="*70)
    for i, name in enumerate(STYLE_NAMES, 1):
        print(f"{i}. {name}")
    while True:
        raw = input("\nElige estilo (1-{}). [Enter = 1]: ".format(len(STYLE_NAMES))).strip()
        if raw == "":
            return STYLE_NAMES[0]
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(STYLE_NAMES):
                return STYLE_NAMES[idx]
            else:
                print("❌ Opción inválida.")
        except ValueError:
            print("❌ Introduce un número.")


def extract_visual_consistency_brief(script_text: str, client: OpenAI) -> str:
    """
    Analiza el guión completo y extrae un brief visual de personajes y elementos recurrentes
    para mantener consistencia absoluta entre todas las imágenes.
    """
    print("📋 Analizando guión para extraer brief de consistencia visual...")

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": (
                    "Eres un director de arte que crea 'visual briefs' para mantener consistencia en secuencias de imágenes.\n\n"
                    "TAREA: Analiza el guión y extrae UNA DESCRIPCIÓN VISUAL CONCRETA Y ESPECÍFICA de:\n"
                    "1. PERSONAJE PRINCIPAL (si hay): edad aproximada, género, ropa específica, rasgos físicos distintivos, accesorios\n"
                    "2. VEHÍCULO/UBICACIÓN RECURRENTE (si hay): tipo exacto, características, color, estado\n"
                    "3. ELEMENTOS VISUALES CONSISTENTES: objetos, atmósfera, época\n\n"
                    "IMPORTANTE:\n"
                    "- Sé ESPECÍFICO: 'hombre de 50 años, barba gris corta, gorra de marinero azul oscuro' NO 'un pescador'\n"
                    "- Sé CONSISTENTE: si aparece un barco, especifica 'barca de pesca de 8 metros con motor fuera borda' NO 'barco'\n"
                    "- SI LA HISTORIA ESTÁ EN PRIMERA PERSONA ('yo', 'nosotros', 'salgo', 'ajusté'), DEBES crear una descripción visual del protagonista\n"
                    "- Para protagonistas en primera persona: infiere edad, género y ocupación del contexto, luego crea detalles visuales coherentes\n"
                    "- Ejemplo: si habla un pescador → 'Hombre de 45-55 años, barba gris descuidada, gorra marinera azul, chaqueta impermeable naranja'\n"
                    "- NO pongas 'N/A' en PERSONAJE si la historia tiene narrador en primera persona\n"
                    "- Mantén la descripción en 3-5 líneas, concisa pero específica\n\n"
                    "FORMATO DE RESPUESTA:\n"
                    "PERSONAJE: [descripción específica - OBLIGATORIO si hay narrador en 1ª persona]\n"
                    "ESCENARIO/VEHÍCULO: [descripción específica o 'N/A']\n"
                    "ELEMENTOS CLAVE: [lista breve de elementos visuales recurrentes]"
                )},
                {"role": "user", "content": f"Analiza este guión y extrae el visual brief:\n\n{script_text}"}
            ]
        )

        brief = response.choices[0].message.content.strip()
        print(f"✅ Brief visual extraído:\n{brief}\n")
        return brief

    except Exception as e:
        print(f"⚠️ No se pudo extraer brief visual: {e}")
        return ""


# --- 2. GENERACIÓN DE IMÁGENES CON GOOGLE GEMINI ---
# --- VERSIÓN CON CONSISTENCIA DE PERSONAJES ---
def generate_visuals_for_script(
    script_text: str,
    project_path: str,
    client: OpenAI,  # Mantenemos para compatibilidad (usado para reescrituras)
    overwrite: bool = False,
    image_model: str = "gemini-2.5-flash-image",
    image_quality: str = "standard",
    image_style: str = None,
):
    """
    Genera imágenes para el guion usando Google Gemini con consistencia de personajes.

    La primera imagen establece el estilo visual y personajes base.
    Las imágenes siguientes mantienen automáticamente la consistencia visual.

    Args:
        script_text: El texto del guion con las etiquetas [imagen:N.png]
        project_path: Ruta al directorio del proyecto
        client: Cliente de OpenAI (usado para reescrituras de prompts si es necesario)
        overwrite: Si es True, regenera imágenes existentes. Si es False, las salta.
        image_model: Modelo de Gemini (gemini-2.5-flash-image o gemini-2.0-flash-exp)
        image_quality: No usado en Gemini, mantenido para compatibilidad
        image_style: Nombre del estilo a aplicar (de STYLE_NAMES). Si None, usa el primero.
    """
    print(f"🎨 Generando imágenes con Google Gemini (consistencia de personajes)...")
    print(f"   Modelo: {image_model}")

    # Estilo elegido
    if not image_style:
        image_style = STYLE_NAMES[0]
    style_block = next((b for n, b in STYLE_PRESETS if n == image_style), STYLE_PRESETS[0][1])
    print(f"   Estilo: {image_style}")

    # Extraer escenas
    scenes = re.findall(r'\[imagen:\d+\.png\]\s*(.*?)(?=\n\s*\[|$)', script_text, re.DOTALL)
    if not scenes:
        print("\n❌ ERROR CRÍTICO: No se encontraron descripciones de escenas en el guion.")
        return False

    all_images_successful = True
    MAX_RETRIES = 5  # intentos por imagen

    # PASO 1: Extraer brief visual específico del guión completo
    visual_brief = extract_visual_consistency_brief(script_text, client)

    # PASO 2: Crear instrucción de consistencia REFORZADA con brief específico
    consistency_context = f"""
CONSISTENCIA VISUAL ABSOLUTA - OBLIGATORIO:

Esta imagen es parte de una secuencia de {len(scenes)} escenas. TODOS los elementos visuales recurrentes
deben mantenerse IDÉNTICOS en cada escena.

{visual_brief}

INSTRUCCIONES CRÍTICAS:
- Si el personaje está definido arriba, DEBE aparecer con EXACTAMENTE esa apariencia en TODAS las escenas donde aparezca
- Si el vehículo/escenario está definido arriba, DEBE ser EXACTAMENTE ese en TODAS las escenas
- NO cambies: ropa, accesorios, tipo de barco, edad aparente, rasgos faciales, color de ojos/pelo
- Mantén el mismo estilo visual, iluminación, paleta de colores en toda la secuencia
- Si algo no está especificado en el brief, manténlo coherente con las demás imágenes de la secuencia

Contexto de la historia completa:
{' '.join([s.strip()[:80] for s in scenes[:3]])}...
"""
    print(f"   📖 Brief de consistencia aplicado a {len(scenes)} escenas")

    for i, scene_text in enumerate(scenes, 1):
        clean_text = scene_text.strip()
        if not clean_text:
            continue

        print(f"🖼️  Generando imagen para escena {i}: '{clean_text[:60]}...'")
        image_path = os.path.join(project_path, "images", f"{i}.png")
        os.makedirs(os.path.dirname(image_path), exist_ok=True)

        # Si ya existe y no queremos sobrescribir
        if os.path.exists(image_path) and not overwrite:
            print(f"   ✓ Imagen {i}.png ya existe, saltando generación.")
            continue

        image_generated = False

        for attempt in range(MAX_RETRIES):
            try:
                # Construir prompt con contexto narrativo completo
                # Todas las imágenes reciben el mismo contexto de consistencia
                final_prompt = consistency_context + "\n\n" + build_master_prompt(style_block, clean_text)
                final_prompt += f"\n\nEscena {i} de {len(scenes)} en la narrativa."
                print(f"   → Escena {i}/{len(scenes)} con contexto narrativo completo")

                # Llamar a Gemini API con configuración para generación de imágenes
                response = gemini_client.models.generate_content(
                    model=image_model,
                    contents=[final_prompt],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(
                            aspect_ratio="9:16",  # Vertical para TikTok/Reels
                        ),
                    ),
                )

                # Gemini devuelve imágenes en response.parts
                # Buscar la parte que contiene la imagen
                image_saved = False
                if hasattr(response, 'parts'):
                    for part in response.parts:
                        # Verificar si el part tiene inline_data (imagen)
                        if hasattr(part, 'inline_data') and part.inline_data is not None:
                            # Usar el método as_image() para obtener la imagen PIL
                            pil_image = part.as_image()
                            # Guardar directamente (PIL detecta formato por extensión .png)
                            pil_image.save(image_path)
                            image_saved = True
                            break

                if not image_saved:
                    raise RuntimeError("Gemini no devolvió datos de imagen válidos en response.parts")

                # Postproceso: Pixel Art (si el estilo lo indica)
                if "pixel" in image_style.lower():
                    pixelize_image(image_path, small_edge=256)
                    print("   ↳ postproceso: pixelize aplicado (downscale + NEAREST)")

                print(f"   ✔ Guardada: {image_path}")
                image_generated = True
                break  # éxito → sal del bucle de reintentos

            except Exception as e:
                error_message = str(e)

                # Manejo de errores específicos de Gemini
                if "SAFETY" in error_message or "BLOCKED" in error_message:
                    print(f"⚠️ Prompt bloqueado por seguridad (intento {attempt + 1}). Reescribiendo...")
                    rewritten_prompt = rewrite_prompt_for_safety(clean_text, client)
                    if rewritten_prompt:
                        clean_text = rewritten_prompt
                        continue
                    else:
                        print("❌ No se pudo reescribir el prompt. Abortando esta imagen.")
                        all_images_successful = False
                        break

                elif "RECITATION" in error_message:
                    print(f"⚠️ Contenido bloqueado por recitación (intento {attempt + 1}). Modificando prompt...")
                    clean_text = f"Create an original interpretation of: {clean_text}"
                    continue

                elif attempt < MAX_RETRIES - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"⚠️ Error temporal (intento {attempt + 1}/{MAX_RETRIES}): {error_message[:100]}")
                    print(f"   Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Error después de {MAX_RETRIES} intentos: {error_message}")
                    all_images_successful = False
                    break

        if not image_generated:
            print(f"🚫 Falló la generación de la imagen para la escena {i} después de {MAX_RETRIES} intentos.")
            all_images_successful = False
            break  # detén el proceso si una imagen falla definitivamente

        # Pequeña pausa entre imágenes para no saturar la API
        time.sleep(1)

    if all_images_successful:
        print("✅ Todas las imágenes han sido generadas con éxito con Google Gemini.")
        print("   Las imágenes mantienen consistencia visual entre escenas.")
        return True
    else:
        print("\n🚫 Proceso detenido debido a un error en la generación de imágenes.")
        return False


# --- 2.5. ANIMACIÓN DE IMÁGENES CON RUNWARE ---
async def _animate_single_image_runware(runware_instance, image_path: str, video_path: str, image_number: str):
    """
    Función auxiliar async para animar una imagen con Runware.
    """
    MAX_RETRIES = 3

    for attempt in range(MAX_RETRIES):
        try:
            print(f"🎥 Animando imagen {image_number}...")

            # Leer y procesar la imagen
            from PIL import Image
            import base64
            import io

            img = Image.open(image_path)
            width, height = img.size
            aspect_ratio = width / height

            print(f"   📐 Imagen original: {width}x{height} (ratio: {aspect_ratio:.3f})")

            # Dimensiones soportadas por Seedance 1.0 Pro Fast (bytedance:2@2)
            # Formato: (ancho, alto, ratio, nombre)
            SUPPORTED_DIMENSIONS = [
                (864, 480, 1.800, "16:9 landscape"),
                (736, 544, 1.353, "4:3 landscape"),
                (640, 640, 1.000, "1:1 square"),
                (544, 736, 0.739, "3:4 portrait"),
                (480, 864, 0.556, "9:16 portrait"),
                (416, 960, 0.433, "9:21 portrait"),
                (960, 416, 2.308, "21:9 landscape"),
            ]

            # Encontrar la dimensión soportada más cercana al aspect ratio de la imagen
            best_match = min(SUPPORTED_DIMENSIONS, key=lambda d: abs(d[2] - aspect_ratio))
            output_width, output_height, _, format_name = best_match

            print(f"   → Usando dimensión: {output_width}x{output_height} ({format_name})")

            # Convertir imagen a base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
            image_uri = f"data:image/png;base64,{image_data}"

            # Crear request para Runware usando Seedance 1.0 Pro Fast
            request = IVideoInference(
                positivePrompt="Smooth cinematic camera movement, subtle atmospheric motion, natural dynamics",
                model="bytedance:2@2",  # Seedance 1.0 Pro Fast
                duration=6,  # 6 segundos
                width=output_width,
                height=output_height,
                numberResults=1,
                includeCost=True,
                frameImages=[
                    IFrameImage(
                        inputImage=image_uri,
                        frame="first"
                    )
                ]
            )

            # Generar video
            videos = await runware_instance.videoInference(requestVideo=request)

            if videos and len(videos) > 0:
                video = videos[0]

                # Descargar el video desde la URL proporcionada por Runware
                print(f"   📥 Descargando video desde Runware...")
                response = requests.get(video.videoURL, timeout=120)
                response.raise_for_status()

                with open(video_path, "wb") as video_file:
                    video_file.write(response.content)

                # Mostrar información de costo
                if hasattr(video, 'cost') and video.cost:
                    print(f"   💰 Costo: ${video.cost}")

                print(f"   ✔ Video guardado: {video_path}")
                return True
            else:
                raise RuntimeError("Runware no devolvió videos")

        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait_time = (attempt + 1) * 3
                print(f"   ⚠️  Error (intento {attempt + 1}/{MAX_RETRIES}): {e}")
                print(f"   Reintentando en {wait_time}s...")
                await asyncio.sleep(wait_time)
                continue
            else:
                print(f"   ❌ Error después de {MAX_RETRIES} intentos: {e}")
                return False

    return False


def animate_images_with_runware(project_path: str, overwrite: bool = False):
    """
    Anima las imágenes PNG del proyecto usando Seedance 1.0 Pro Fast en Runware.

    Args:
        project_path: Ruta al directorio del proyecto
        overwrite: Si es True, regenera videos existentes. Si es False, los salta.

    Returns:
        True si todas las animaciones se generaron correctamente, False si hubo errores.
    """
    if not runware_available:
        print("\n❌ Error: Runware no está configurado correctamente.")
        print("   Asegúrate de:")
        print("   1. Tener RUNWARE_API_KEY en tu archivo .env")
        print("   2. Haber instalado: pip install runware")
        return False

    print("\n🎬 Iniciando animación de imágenes con Runware...")
    print("   Modelo: Seedance 1.0 Pro Fast (bytedance:2@2)")
    print("   Duración: 6 segundos por video")
    print("   Resolución: Auto-detecta aspect ratio (480x864 para 9:16, 864x480 para 16:9, etc.)")
    print("   Costo: ~$0.0315 por video → ~$0.19-0.31 por proyecto de 6-10 videos 💰")
    print("   💡 AHORRO: 65% más barato que Replicate\n")

    images_path = os.path.join(project_path, "images")
    if not os.path.exists(images_path):
        print(f"❌ Error: No se encontró la carpeta {images_path}")
        return False

    # Buscar todas las imágenes PNG numeradas (1.png, 2.png, etc.)
    image_files = []
    for filename in os.listdir(images_path):
        if re.match(r'^\d+\.png$', filename):
            image_files.append(filename)

    if not image_files:
        print(f"❌ Error: No se encontraron imágenes PNG numeradas en {images_path}")
        return False

    # Ordenar por número
    image_files.sort(key=lambda x: int(x.split('.')[0]))
    print(f"📁 Encontradas {len(image_files)} imágenes para animar: {', '.join(image_files)}\n")

    # Función async principal que ejecuta todas las animaciones
    async def animate_all():
        # Conectar a Runware
        runware = Runware(api_key=RUNWARE_API_KEY)
        await runware.connect()
        print("✅ Conectado a Runware API\n")

        all_videos_successful = True

        try:
            for image_file in image_files:
                image_number = image_file.split('.')[0]
                image_path = os.path.join(images_path, image_file)
                video_path = os.path.join(images_path, f"{image_number}.mp4")

                # Si ya existe y no queremos sobrescribir
                if os.path.exists(video_path) and not overwrite:
                    print(f"✓ Video {image_number}.mp4 ya existe, saltando animación.")
                    continue

                # Animar imagen
                success = await _animate_single_image_runware(
                    runware, image_path, video_path, image_number
                )

                if not success:
                    print(f"🚫 Falló la animación de {image_file}")
                    all_videos_successful = False
                    # Continuar con las siguientes imágenes

                # Pequeña pausa entre llamadas
                await asyncio.sleep(1)

        finally:
            # Cerrar conexión
            try:
                await runware.disconnect()
            except Exception as e:
                print(f"   ⚠️  Advertencia al cerrar conexión: {e}")

        return all_videos_successful

    # Ejecutar el loop async
    all_successful = asyncio.run(animate_all())

    if all_successful:
        print("\n✅ Todas las imágenes han sido animadas con éxito.")
        print(f"   Los videos están en: {images_path}/")
        print(f"   Archivos: 1.mp4, 2.mp4, 3.mp4, etc.")
        return True
    else:
        print("\n⚠️  Proceso completado con algunos errores en la animación.")
        return False


# --- 3. FUNCIONES PARA MODO AUTOMÁTICO ---
def run_project_indexer():
    """Ejecuta crear_indice_proyectos.py para actualizar el master list."""
    print("📊 Actualizando índice de proyectos...")
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        indexer_path = os.path.join(script_dir, "crear_indice_proyectos.py")

        if not os.path.exists(indexer_path):
            print(f"⚠️ No se encontró crear_indice_proyectos.py en {indexer_path}")
            return False

        result = subprocess.run(
            [sys.executable, indexer_path],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Índice de proyectos actualizado correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar crear_indice_proyectos.py: {e}")
        print(f"Salida: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False


def get_next_project_number():
    """Lee el master list y determina el siguiente número de proyecto."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    master_list_path = os.path.join(script_dir, "_master_project_list.txt")

    if not os.path.exists(master_list_path):
        print("⚠️ No se encontró _master_project_list.txt, usando número 1")
        return 1

    max_number = 0
    try:
        with open(master_list_path, "r", encoding="utf-8") as f:
            for line in f:
                # Buscar líneas que empiecen con número_NOMBRE
                match = re.match(r'^(\d+)_', line)
                if match:
                    num = int(match.group(1))
                    if num > max_number:
                        max_number = num

        next_number = max_number + 1
        print(f"📈 Último proyecto: {max_number}, siguiente: {next_number}")
        return next_number
    except Exception as e:
        print(f"❌ Error al leer _master_project_list.txt: {e}")
        return 1


def generate_project_name_from_idea(idea_text: str, client: OpenAI):
    """Genera un nombre corto de proyecto basado en la idea usando OpenAI."""
    print("🏷️ Generando nombre de proyecto...")

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": (
                    "Eres un asistente creativo que genera nombres únicos y memorables para proyectos de misterio y terror. "
                    "Dado un texto descriptivo, debes crear un nombre corto de 1-3 palabras "
                    "en MAYÚSCULAS que capture la esencia específica del contenido. "
                    "El nombre debe ser ÚNICO, evocador y apropiado para contenido paranormal/misterioso. "
                    "Evita nombres genéricos. Busca algo específico que distinga esta historia. "
                    "RESPONDE SOLO CON EL NOMBRE, SIN EXPLICACIONES. "
                    "Ejemplos: METROMADRID, CASTILLOCARDONA, PALACIOLINARES, HOMBREPEZ, CORTIJOMALDITO"
                )},
                {"role": "user", "content": f"Genera un nombre único de proyecto para: {idea_text}"}
            ]
        )

        project_name = response.choices[0].message.content.strip()
        # Limpiar el nombre (solo letras y números, mayúsculas)
        project_name = re.sub(r'[^A-Z0-9]', '', project_name.upper())

        print(f"✅ Nombre generado: {project_name}")
        return project_name
    except Exception as e:
        print(f"❌ Error al generar nombre de proyecto: {e}")
        # Fallback: generar nombre genérico basado en timestamp
        import datetime
        fallback_name = f"PROYECTO{datetime.datetime.now().strftime('%m%d%H%M')}"
        print(f"⚠️ Usando nombre fallback: {fallback_name}")
        return fallback_name


def generate_automatic_idea(client: OpenAI):
    """Analiza el master list y genera una nueva idea viral usando OpenAI."""
    print("\n" + "="*70)
    print("🤖 MODO AUTOMÁTICO ACTIVADO")
    print("="*70)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    master_list_path = os.path.join(script_dir, "_master_project_list.txt")

    if not os.path.exists(master_list_path):
        print(f"❌ Error: No se encontró {master_list_path}")
        return None

    # Leer el contenido del master list
    print("📖 Leyendo análisis de proyectos anteriores...")
    try:
        with open(master_list_path, "r", encoding="utf-8") as f:
            master_content = f.read()
    except Exception as e:
        print(f"❌ Error al leer el archivo: {e}")
        return None

    # Crear el prompt para OpenAI
    print("🧠 Analizando proyectos virales y generando nueva idea...")

    system_prompt = """
Eres un analista de contenido viral experto en la cuenta 'Relatos Extraordinarios'.

Tu tarea es:
1. Analizar el índice de proyectos proporcionado
2. Identificar patrones en los proyectos VIRALES (_v) y MEDIO VIRALES (_mv)
3. Generar UNA SOLA idea original para un nuevo proyecto que:
   - Siga los patrones de los proyectos virales exitosos
   - Sea completamente original (no repetir temas ya hechos)
   - Tenga potencial viral similar
   - Se centre en misterio, paranormal, leyendas españolas, lugares abandonados o historias extraordinarias
   - Sea específica y detallada (200-300 palabras)

IMPORTANTE:
- Responde SOLO con la idea del nuevo proyecto, sin explicaciones adicionales
- La idea debe ser un texto narrativo listo para usar
- No incluyas títulos ni encabezados, solo el contenido de la idea
- Debe ser similar en tono y estructura a las ideas existentes en el índice
"""

    user_prompt = f"""
Aquí está el índice completo de proyectos con especial atención a los VIRALES y MEDIO VIRALES al final:

{master_content}

Genera UNA idea original para el siguiente proyecto que tenga alto potencial viral.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            # Nota: GPT-5 no admite temperature personalizada, usa el valor por defecto (1)
        )

        new_idea = response.choices[0].message.content.strip()

        print("\n" + "="*70)
        print("💡 NUEVA IDEA GENERADA:")
        print("="*70)
        print(new_idea)
        print("="*70 + "\n")

        return new_idea
    except Exception as e:
        print(f"❌ Error al generar idea automática: {e}")
        return None


# --- 4. FUNCIÓN PRINCIPAL ORQUESTADORA ---
def main():
    parser = argparse.ArgumentParser(description="Automatización para Relatos Extraordinarios")
    parser.add_argument("--idea", required=False, help="La idea principal para el vídeo.")
    parser.add_argument("--project-name", required=False, help="El nombre de la carpeta del proyecto (p.ej. 192_RISA).")
    parser.add_argument("--overwrite-images", action="store_true", help="Regenera todas las imágenes aunque ya existan.")
    parser.add_argument("--force-video", action="store_true", help="Regenera el video aunque ya exista.")
    parser.add_argument("--image-model", default=None,
                        choices=["gemini-2.5-flash-image", "gemini-2.0-flash-exp"],
                        help="Modelo de generación de imágenes Google Gemini. Default: gemini-2.5-flash-image (mejor consistencia)")
    parser.add_argument("--image-quality", default=None,
                        help="Mantenido por compatibilidad, no usado con Gemini.")
    parser.add_argument("--animate-images", action="store_true",
                        help="Anima las imágenes generadas usando Seedance 1.0 Pro Fast en Runware (864x480, 6s, ~$0.0315 por video - 65%% más barato que Replicate).")
    args = parser.parse_args()

    # --- MODO AUTOMÁTICO ---
    # Si no se proporcionó idea ni project-name, activar modo automático
    if args.idea is None and args.project_name is None:
        print("\n🚀 Modo automático detectado (no se proporcionaron --idea ni --project-name)")

        # 1. Ejecutar crear_indice_proyectos.py
        if not run_project_indexer():
            print("❌ Error al actualizar el índice de proyectos. Abortando.")
            return

        # 2. Generar idea automáticamente analizando proyectos virales
        auto_idea = generate_automatic_idea(client)
        if not auto_idea:
            print("❌ Error al generar idea automática. Abortando.")
            return

        # 3. Determinar siguiente número de proyecto
        next_number = get_next_project_number()

        # 4. Generar nombre de proyecto
        project_short_name = generate_project_name_from_idea(auto_idea, client)

        # 5. Construir nombre completo del proyecto
        args.idea = auto_idea
        args.project_name = f"{next_number}_{project_short_name}"

        print(f"\n✅ Proyecto automático configurado:")
        print(f"   📂 Nombre: {args.project_name}")
        print(f"   💡 Idea: {auto_idea[:100]}...")
        print("\n" + "="*70)
        print("Continuando con el flujo normal de generación...")
        print("="*70 + "\n")

    # Verificar que ahora tenemos idea y project-name (manual o automático)
    if not args.idea or not args.project_name:
        print("❌ Error: Se requiere --idea y --project-name (o ninguno para modo automático)")
        parser.print_help()
        return

    # Si no se especificaron modelo y calidad, usar valores por defecto
    if args.image_model is None or args.image_quality is None:
        args.image_model = "gemini-2.5-flash-image"
        args.image_quality = "standard"
        print(f"📸 Usando modelo de imagen por defecto: Google {args.image_model}")

    project_path = args.project_name
    images_path = os.path.join(project_path, "images")

    # --- LÓGICA DE CREACIÓN DE PROYECTO ---
    if not os.path.exists(images_path):
        os.makedirs(images_path)
        print(f"📁 Proyecto creado en: ./{project_path}/")

        # Copiamos los archivos base si existen en la carpeta principal del script
        print("📥 Copiando archivos base (musica.mp3, cierre.mp4)...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for file_name in ["musica.mp3", "cierre.mp4"]:
            source_file = os.path.join(script_dir, file_name)
            if os.path.exists(source_file):
                # Copiar a la carpeta images/
                dest_file = os.path.join(images_path, file_name)
                shutil.copy(source_file, dest_file)
                print(f"   ✓ {file_name} copiado a images/")
            else:
                print(f"⚠️  Aviso: El archivo '{file_name}' no se encontró en {script_dir}. No se copiará.")

    script_file = os.path.join(project_path, "texto.txt")
    social_file = os.path.join(project_path, "redes.txt")
    
    content = None
    if not os.path.exists(script_file):
        content_generated = generate_creative_content(args.idea)
        if not content_generated:
            return

        with open(script_file, "w", encoding="utf-8") as f:
            # Reemplazamos .mp4 por .png desde el momento de la creación
            script_content = content_generated["script"].replace(".mp4", ".png")
            f.write(script_content)
            
        with open(social_file, "w", encoding="utf-8") as f:
            f.write(content_generated["social_post"])
            
        content = {"script": script_content}
            
    else:
        print("📝 Archivos de texto ya existen, saltando generación de contenido.")
        with open(script_file, "r", encoding="utf-8") as f:
            # Nos aseguramos de que el guion que leemos usa .png para la lógica de re-generación
            script_content = f.read().replace(".mp4", ".png")
            content = {"script": script_content}

    # Menú interactivo de estilo visual
    chosen_style = interactive_style_selection()
    print(f"✅ Estilo seleccionado: {chosen_style}\n")

    # Llamada a la función de imágenes pasando el objeto 'client' para las reescrituras
    success = generate_visuals_for_script(
        content["script"],
        project_path,
        client,
        overwrite=args.overwrite_images,
        image_model=args.image_model,
        image_quality=args.image_quality,
        image_style=chosen_style,   # ← añadido
    )

    if not success:
        return

    # Si se especificó --animate-images, animar las imágenes con Runware
    if args.animate_images:
        animate_success = animate_images_with_runware(
            project_path,
            overwrite=args.overwrite_images
        )
        if not animate_success:
            print("\n⚠️  Advertencia: Hubo problemas al animar las imágenes.")
            print("   Puedes intentar nuevamente con --animate-images --overwrite-images")
            # No abortamos, continuamos con el proceso normal
        else:
            # Actualizar texto.txt para usar .mp4 en lugar de .png
            script_file = os.path.join(project_path, "texto.txt")
            if os.path.exists(script_file):
                with open(script_file, "r", encoding="utf-8") as f:
                    script_content = f.read()

                # Reemplazar .png por .mp4
                updated_content = script_content.replace(".png]", ".mp4]")

                with open(script_file, "w", encoding="utf-8") as f:
                    f.write(updated_content)

                print("\n✅ Archivo texto.txt actualizado: .png → .mp4")
    else:
        print("\n💡 Tip: Puedes animar las imágenes agregando --animate-images a tu comando")

    # El bloque que modificaba el guion aquí ya no es necesario,
    # porque nos aseguramos de que siempre trabaje con .png desde el principio.

    # Verificar si el video base ya existe
    video_out_path = os.path.join(project_path, "Out", "video.mp4")
    video_exists = os.path.exists(video_out_path)

    if video_exists and not args.force_video:
        print(f"\n✅ El video base ya existe en '{video_out_path}'")
        print("   Saltando generación de video. Usa --force-video si quieres regenerarlo.")
        print("\n💡 Puedes ejecutar manualmente desde la carpeta del proyecto:")
        print(f"   cd {project_path}")
        print(f"   powershell -ExecutionPolicy Bypass ..\\run.ps1 -NoBurn  (para regenerar solo video)")
        print(f"   powershell -ExecutionPolicy Bypass ..\\run.ps1           (para quemar subtítulos)")
        return

    print("\n🎬 Todo listo. Lanzando el renderizado final con run.ps1...")

    # Obtener la ruta absoluta de run.ps1 (está en el mismo directorio que este script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    run_ps1_path = os.path.join(script_dir, "run.ps1")

    command = [
        "powershell.exe", "-ExecutionPolicy", "Bypass", "-File", run_ps1_path,
        "-Resolution", "1080x1920", "-Fit", "cover", "-KenBurns", "in",
        "-KbZoom", "0.2", "-KbPan", "random", "-KbSticky", "-VideoFill", "slow",
        "-MediaKeepAudio", "-MediaAudioVol", "0.1",
        "-MusicAudio", "-MusicAudioVol", "0.1"
    ]

    try:
        # Ejecutamos el comando desde dentro de la carpeta del proyecto
        subprocess.run(command, cwd=project_path, check=True, shell=True)
        print(f"\n✅ ¡Proceso completado! El vídeo final está en la carpeta '{project_path}/Out'.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar run.ps1: {e}")
    except FileNotFoundError:
        print(f"❌ Error: 'run.ps1' no encontrado en {run_ps1_path}. Revisa la ruta en el script.")


if __name__ == "__main__":
    main()