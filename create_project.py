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
        from runware import Runware, IVideoInference, IFrameImage, IImageInference
        import asyncio
        runware_available = True
    except ImportError:
        print("⚠️  Advertencia: 'runware' no está instalado. Ejecuta: pip install runware")
    except Exception as e:
        print(f"⚠️  Advertencia: Error al inicializar Runware: {e}")

# --- Constantes para los modelos de Runware ---
# (Añadidas para la opción de bajo coste)
QWEN_AIR_ID = "runware:108@1"

NEGATIVE_PROMPT = (
    "(worst quality, low quality, normal quality, plain, boring, blurry, jpeg artifacts, "
    "signature, watermark, text, username, error, poorly drawn, malformed, deformed, "
    "mutated, ugly, duplicate, out of frame, missing items, extra limbs, fused fingers)"
)

# --- 1. GENERACIÓN DE CONTENIDO CREATIVO CON OPENAI (gpt-5.1) ---
def generate_creative_content(idea: str):
    """Llama a la API de OpenAI (gpt-5.1) para obtener guion, post y texto para redes."""
    print(f"🧠 Generando contenido creativo con OpenAI (gpt-5.1) para la idea: '{idea}'...")

    # Prompt optimizado para GPT-5.1 con protagonista único garantizado
    system_prompt = """
Eres un guionista experto en misterio y terror especializado en dramas de audio de corta duración. 
Tu tarea es generar un objeto JSON con DOS claves de primer nivel:

{
  "script": "...",
  "social_post": "..."
}

Debes responder EXCLUSIVAMENTE con ese JSON válido, sin texto antes o después.

=====================================================================
RULES — PRIORIDAD MÁXIMA
=====================================================================
1. Cada bloque del guion debe tener MÁXIMO 15 palabras.
2. El guion debe tener entre 8 y 14 bloques totales.
3. Cada bloque debe seguir EXACTAMENTE este formato:

[ETIQUETA_DE_VOZ]
[imagen:X.png]
TEXTO DE MÁXIMO 15 PALABRAS
(línea en blanco obligatoria)

4. Cada bloque usa un número de imagen único, secuencial:
   [imagen:1.png], [imagen:2.png], [imagen:3.png]...
   No se repiten números.

5. El guion termina SIEMPRE con una línea final:
   [CIERRE]

=====================================================================
PROTAGONISTA ÚNICO (CONDICIÓN OBLIGATORIA)
=====================================================================
- La historia debe girar SIEMPRE alrededor de UN SOLO protagonista principal.
- Puede ser hombre o mujer, pero debe quedar claro quién es.
- Este protagonista es el centro narrativo y emocional de la historia.
- Puede haber personajes secundarios, pero NUNCA debe haber varios protagonistas
  al mismo nivel ni un grupo coral donde nadie destaque claramente.
- Si usas diálogos, el protagonista debe tener SIEMPRE la misma etiqueta de voz
  a lo largo de todo el guion (por ejemplo [HOMBRE30] o [MUJER30]).
- Evita historias donde el foco cambie de un personaje a otro.

=====================================================================
VOCES DISPONIBLES
=====================================================================
[NARRADOR]
[CHICO10], [JOVENASUSTADO], [HOMBRE25], [HOMBRE30], [HOMBRE40], [HOMBRE50], [ANCIANO]
[CHICA12], [MUJER20], [MUJER30], [ANCIANA], [MUJERASUSTADA]
[DUENDEMALVADO], [MONSTER]

=====================================================================
REGLAS DE NARRACIÓN
=====================================================================
OPCIÓN 1 — SOLO [NARRADOR]:
Historia completa narrada sin diálogos, solo bloques del narrador.

OPCIÓN 2 — NARRADOR + DIÁLOGOS (REGLAS ESTRICTAS):
- [NARRADOR] = SOLO para descripciones, pensamientos o acciones.
- OTRAS VOCES = SOLO para palabras habladas en voz alta.
- REGLA DE ORO: PROHIBIDO mezclar acción/descripción y diálogo en el mismo bloque.

- INSTRUCCIÓN CRÍTICA:
  Si un personaje habla Y se describe su acción (ej: "dijo", "susurró", "murmuró"...),
  DEBES separarlo en DOS bloques consecutivos:
  
  1. Un bloque de DIÁLOGO (ej: [HOMBRE30]) con las palabras habladas.
  2. Un bloque de NARRACIÓN (ej: [NARRADOR]) describiendo la acción.

- PERMITIDO:
  - Puedes asignar la MISMA [imagen:X.png] a ambos bloques si ocurren en la misma escena.
  - Máximo 15 palabras.

=====================================================================
NORMAS ADICIONALES
=====================================================================
- Todos los números deben escribirse con letras (no 1, 2, 3).
- El tono debe ser cinematográfico, misterioso e inquietante.
- Cada bloque contiene SOLO un concepto visual claro.
- Mantén coherencia narrativa y progresión dramática.

=====================================================================
SECCIÓN DEL JSON → "script"
=====================================================================
Debe generar un único string que contenga todos los bloques del guion
siguiendo exactamente el formato especificado.

=====================================================================
SECCIÓN DEL JSON → "social_post"
=====================================================================
- Texto único en español, máx. 300 caracteres.
- Directo, intrigante, en tono de misterio.
- No puede empezar con: "Te atreves", "Descubre", "Conoces", "Conocías".
- Debe contener: #RelatosExtraordinarios + entre 1 y 4 hashtags relevantes.

=====================================================================
FORMATO FINAL
=====================================================================
Debes responder SOLO con un JSON válido como:

{"script":"...","social_post":"..."}

Sin explicaciones, sin saltos de línea fuera del JSON, sin texto adicional.
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

        # Garantizar que las imágenes se mantengan en PNG
        if "script" in content:
            content["script"] = content["script"].replace(".mp4", ".png")

        print("✅ Contenido creativo generado con éxito (con protagonista único).")
        return content

    except Exception as e:
        print(f"❌ Error al generar contenido con OpenAI (gpt-5.1): {e}")
        return None


def generate_visual_prompts_for_script(script_text: str, client: OpenAI) -> list:
    """
    Analiza un guion de audio COMPLETO y genera un PROMPT VISUAL
    cinematográfico para CADA escena [imagen:X.png] encontrada.
    Usa la etiqueta [PROTAGONISTA] para marcar cuándo aparece la protagonista.
    """
    print(f"🎬 Generando prompts visuales con gpt-5.1 para el guion...")

    # Contar cuántas imágenes necesitamos
    scene_tags = re.findall(r'\[imagen:(\d+)\.png\]', script_text)
    num_scenes = len(scene_tags)
    if num_scenes == 0:
        print("   ❌ No se encontraron etiquetas [imagen:X.png] en el guion.")
        return []

    print(f"   Encontradas {num_scenes} escenas para describir visualmente.")

    system_prompt = f"""
Eres un Director de Arte y Director de Fotografía de alto nivel.
Has recibido un guion de audio COMPLETO que describe una historia continua.

Tu tarea es generar un objeto JSON con UNA sola clave: "visual_prompts".
Esta clave debe ser una LISTA donde cada elemento es un prompt visual altamente cinematográfico.

=====================================================================
VISIÓN GLOBAL
=====================================================================
Debes concebir TODA la secuencia de imágenes como si fuera una
PELÍCULA cohesiva. No son ilustraciones independientes: son
FOTOGRAMAS de una misma narrativa visual.

- Mantén continuidad visual entre escenas (atmósfera, tono, ritmo).
- Respeta la progresión emocional del guion (tensión, calma, revelación…).
- Si varias escenas ocurren en el mismo lugar, mantén el mismo estilo
  de arquitectura, materiales, colores y tipo de luz.

=====================================================================
USO DE LA ETIQUETA [PROTAGONISTA]
=====================================================================
La historia tiene un o una protagonista principal.

- Si el o la protagonista APARECE VISUALMENTE en la imagen de una escena,
  debes incluir SIEMPRE el marcador exacto [PROTAGONISTA] dentro del texto
  del prompt.

- Cuando uses [PROTAGONISTA]:
  * NO describas su rostro, pelo, color de piel u ojos en detalle.
  * NO describas en detalle su ropa (eso lo controla otro componente).
  * SÍ puedes describir:
    - su postura
    - su gesto general.
    - su posición en el encuadre.
    - su relación con el entorno y con otros personajes.

- Si en la escena NO aparece el o la protagonista visualmente:
  * NO uses el marcador [PROTAGONISTA].
  * Centra el prompt en el entorno, otros personajes, objetos o atmósfera.

=====================================================================
REGLAS DE CREACIÓN POR ESCENA
=====================================================================
Para cada bloque [imagen:X.png] debes:

1. Leer el guion COMPLETO para entender:
   - la historia 
   - el tono general
   - el arco emocional
   - la continuidad espacial

2. Analizar el TEXTO del bloque de audio para decidir qué se ve.
   NO repitas literalmente lo que dice el audio.
   Describe SOLO lo que se VE.

3. Elegir un encuadre cinematográfico claro:
   - Plano general / Plano entero / Plano medio / Primer plano / Detalle
   - y que tenga sentido con el momento emocional del guion.

4. Describir la iluminación con intención narrativa:
   - tipo de luz, dirección, dureza / suavidad
   - color y temperatura
   - sombras (suaves, duras, expresionistas…)

5. Describir el ambiente:
   - clima, atmósfera
   - polvo, niebla, lluvia, viento
   - textura emocional de la escena

=====================================================================
LONGITUD
=====================================================================
Cada prompt visual debe tener APROXIMADAMENTE entre 300 y 600 caracteres.

=====================================================================
FORMATO DE RESPUESTA
=====================================================================
Responde EXCLUSIVAMENTE con el objeto JSON:

{{
  "visual_prompts": [
    "Prompt visual detallado para la escena 1...",
    "Prompt visual detallado para la escena 2...",
    "Prompt visual detallado para la escena {num_scenes}..."
  ]
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-5.1",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Guion a analizar:\n\n{script_text}"}
            ]
        )

        content = json.loads(response.choices[0].message.content)
        prompts_list = content.get("visual_prompts", [])

        if len(prompts_list) != num_scenes:
            print(f"   ❌ ERROR: gpt-5.1 generó {len(prompts_list)} prompts, pero se esperaban {num_scenes}.")
            return []

        print("✅ Lista de prompts visuales generada con éxito.")
        return prompts_list

    except Exception as e:
        print(f"❌ Error al generar prompts visuales con gpt-5.1: {e}")
        return []

        
def rewrite_prompt_for_safety(prompt_text: str, client: OpenAI):
    """Llama a un modelo de texto para reescribir un prompt bloqueado."""
    print("✍️  Reescribiendo el prompt para evitar filtros de seguridad...")
    try:
        response = client.chat.completions.create(
            model="gpt-5.1", 
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


# =========================================================================
# ===== ESTILOS DE IMAGEN (Presets Duales: Gemini y Qwen) =====
# =========================================================================

# --- BIBLIOTECA 1: PRESETS PARA GEMINI (Largos y detallados) ---
STYLE_PRESETS_GEMINI = [
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

    ("Fotorrealismo Cinematográfico (Thriller Moderno)", textwrap.dedent("""\
    Estilo fotorrealista cinematográfico, como un fotograma de una película de thriller contemporáneo (estilo David Fincher o A24).

    Características visuales esenciales:
    - Hiperrealismo con un fino grano de película analógica (film grain)
    - Iluminación de bajo-key (low-key), muy oscura, con sombras profundas y fuentes de luz motivadas (un farol, una pantalla)
    - Paleta de colores fría y desaturada: predominio de azules nocturnos, verdes industriales y grises urbanos
    - Reflejos especulares húmedos: asfalto mojado por la lluvia, sudor en la piel, metal brillante
    - Composición de 'thriller' con encuadres intencionados, a menudo usando espacio negativo
    - Profundidad de campo cinematográfica, con fondos desenfocados (bokeh) que aíslan al sujeto

    Coherencia visual entre escenas:
    - La gradación de color (color grade) específica y la textura del grano deben ser idénticas en todas las imágenes
    - Los personajes deben mantener consistencia fotográfica absoluta
    """).strip()),

    ("Animación Neo-Noir (Estilo 'Arcane')", textwrap.dedent("""\
    Ilustración híbrida 2D/3D con estética 'painterly' oscura, inspirada en series como 'Arcane' (Fortiche).

    Características visuales esenciales:
    - Modelos 3D con texturas de pinceladas pintadas a mano, visibles y expresivas
    - Contornos de tinta negros y angulosos que definen las formas
    - Iluminación volumétrica dramática y teatral, con 'god rays' (rayos de luz) atravesando el humo o el polvo
    - Paleta de colores dual: entornos oscuros y desaturados en contraste con luces de neón vibrantes (rosa, cian, ámbar)
    - Expresiones faciales intensas y poses dinámicas
    - Fondos detallados que mezclan arquitectura 'steampunk' o 'art deco' con decadencia moderna

    Coherencia visual entre escenas:
    - El estilo de textura pintada, el grosor del contorno y la paleta de neón deben ser uniformes
    - Los personajes deben mantener sus rasgos estilizados y ropa
    """).strip()),

    ("Óleo Digital Cinematográfico (Terror Clásico)", textwrap.dedent("""\
    Pintura al óleo digital con una estética de terror gótico clásico, rica en textura y drama.

    Características visuales esenciales:
    - Textura de lienzo visible y pinceladas empastadas (impasto) que dan peso y volumen a las formas
    - Iluminación de claroscuro extremo, inspirada en Caravaggio o Rembrandt, con luz dura y sombras que se funden en negro
    - Paleta de colores profunda y rica: rojos sangre, azules profundos, ocres terrosos y dorados antiguos
    - Composición cinematográfica que enfatiza la escala (personajes pequeños ante arquitecturas opresivas)
    - Atmósfera cargada de polvo en suspensión iluminado por la luz
    - Expresiones faciales emotivas, capturadas con pinceladas realistas pero expresivas

    Coherencia visual entre escenas:
    - La misma paleta de colores y la misma textura de pincel/lienzo deben aplicarse en toda la secuencia
    - La iluminación debe mantener el mismo estilo dramático
    """).strip()),

    ("Grabado Anatómico Victoriano (Códice Maldito)", textwrap.dedent("""\
    Ilustración estilo grabado en cobre o xilografía, como sacada de un códice antiguo o un libro de anatomía victoriano.

    Características visuales esenciales:
    - Estilo de línea fina y detallada (hatching y cross-hatching) para crear sombras y volumen
    - Fondo de papel envejecido, color pergamino o sepia, con manchas y textura visible
    - Paleta de colores estrictamente limitada: negro para las líneas, y opcionalmente un solo color de acento (rojo sangre o azul índigo)
    - Composición centrada, a menudo con elementos simétricos o diagramáticos
    - Sensación de ilustración técnica o científica, pero aplicada a un tema paranormal o macabro
    - Puede incluir anotaciones ilegibles o diagramas fantásticos en los márgenes

    Coherencia visual entre escenas:
    - La textura del papel, el estilo de línea de grabado y la paleta deben ser idénticos
    """).strip()),

    ("Fotografía Antigua Inquietante (Daguerrotipo)", textwrap.dedent("""\
    Simulación de una fotografía analógica antigua, como un daguerrotipo, ferrotipo o una placa de vidrio del siglo XIX.

    Características visuales esenciales:
    - Tono monocromático (sepia, cianotipo azulado o plata fría)
    - Alto grano, imperfecciones de la emulsión, arañazos, manchas y viñeteado pesado en los bordes
    - Luz suave y difusa, típica de los largos tiempos de exposición
    - Poses estáticas, miradas directas a cámara, expresiones serias o inquietantes
    - Profundidad de campo reducida, con fondos borrosos o pictóricos
    - Sensación de artefacto encontrado, un recuerdo perdido de un evento fantasmal

    Coherencia visual entre escenas:
    - El nivel de grano, el tono de color (sepia/plata) y el tipo de artefactos deben ser idénticos en todas las imágenes
    """).strip()),

    ("Acuarela Gótica (Bruma y Tinta)", textwrap.dedent("""\
    Ilustración en acuarela con un estilo oscuro y atmosférico, como las ilustraciones de novelas góticas.

    Características visuales esenciales:
    - Técnica de 'wet-on-wet' (húmedo sobre húmedo) para crear bordes que sangran y se difuminan
    - Paleta de colores 'grisalla' (grises y negros) con lavados de color muy oscuros: índigo, carmesí, verde bosque
    - Textura visible de papel de acuarela de grano grueso
    - Composición dominada por la bruma, la niebla o la lluvia, donde las formas emergen de la oscuridad
    - Contornos de tinta negra sueltos que refuerzan las formas principales
    - Luz que parece emanar desde dentro de la niebla, creando siluetas

    Coherencia visual entre escenas:
    - La textura del papel, la paleta de colores y la técnica de sangrado de color deben ser uniformes
    """).strip()),

    ("Stop-Motion Macabro (Cuento Táctil)", textwrap.dedent("""\
    Estilo que simula una película de animación stop-motion oscura (inspirada en Laika, Tim Burton o los Hermanos Quay).

    Características visuales esenciales:
    - Texturas táctiles y tangibles: arcilla con huellas dactilares, tela de arpillera, madera astillada, metal oxidado
    - Proporciones de personajes exageradas: ojos grandes, miembros largos y delgados, posturas lánguidas
    - Iluminación de estudio teatral: luces duras y direccionales que crean sombras nítidas en un 'set' físico
    - Imperfecciones deliberadas que delatan la naturaleza artesanal de los modelos
    - Atmósfera de cuento de hadas macabro
    - Profundidad de campo reducida (tilt-shift) que simula una miniatura

    Coherencia visual entre escenas:
    - Las texturas de los materiales (arcilla, tela) y el estilo de iluminación de 'set' deben ser uniformes
    """).strip()),

    ("Vitral Gótico (Luz Oscura)", textwrap.dedent("""\
    Ilustración con el estilo de un vitral o vidriera de una catedral gótica, pero con temática oscura.

    Características visuales esenciales:
    - Colores joya profundos y saturados: rubí, zafiro, esmeralda, ámbar
    - Contornos de plomo gruesos, negros y definidos que segmentan todas las formas
    - Diseño estilizado y bidimensional, con poca o ninguna perspectiva realista
    - Fuerte iluminación retroiluminada, como si la luz pasara a través del vidrio
    - Composición formal, a menudo simétrica o encerrada en un marco ornamental
    - Las 'imperfecciones' del vidrio (burbujas, variaciones de color) deben ser visibles

    Coherencia visual entre escenas:
    - El grosor de las líneas de plomo, la paleta de colores joya y la textura del vidrio deben ser constantes
    """).strip()),

    ("Alto Contraste Noir (Siluetas y Sombras)", textwrap.dedent("""\
    Estilo de cómic noir de alto contraste, llevado al extremo (inspirado en 'Sin City' de Frank Miller).

    Características visuales esenciales:
    - Estrictamente blanco y negro. Sin grises. Las sombras son masas de negro absoluto.
    - Uso dramático del espacio negativo; las siluetas definen la escena
    - Composición gráfica y angular, con perspectivas forzadas
    - La luz es un arma: recorta formas de la oscuridad
    - Opcionalmente, un único y diminuto toque de un solo color de acento (un rojo brillante) en alguna escena clave
    - Estética de novela gráfica 'hard-boiled'

    Coherencia visual entre escenas:
    - El tratamiento de la luz y la sombra debe ser radicalmente binario (B/N) y coherente
    - Si se usa un color de acento, debe ser el mismo y usarse con el mismo propósito
    """).strip()),
]

STYLE_PRESETS_QWEN = [
    (
        "Dark Graphic Novel (Cinematic Gothic Horror)",
        textwrap.dedent("""\
        Dark cinematic graphic novel art by Mike Mignola. Heavy inked lines, deep black shadows, gothic horror atmosphere.
        Limited palette: deep blacks, cool grays, midnight blues with blood-red accents.
        Extreme chiaroscuro lighting, deep vignetting, film noir composition, dramatic panel framing.
        """).strip()
    ),

    (
        "Cinematic Photorealism (Modern Thriller)",
        textwrap.dedent("""\
        Shot on ARRI Alexa with 35mm lens, modern thriller cinematography. Low-key lighting with motivated practical lights.
        Desaturated cold palette (industrial blues, urban greens, concrete grays) with wet skin and surface reflections.
        Subtle film grain, shallow DOF, anamorphic lens flares, professional color grading.
        """).strip()
    ),

    (
        "Neo-Noir Animation (Arcane Style)",
        textwrap.dedent("""\
        2D/3D hybrid animation style like Arcane series. Hand-painted brushstroke texture, angular ink outlines.
        Volumetric light rays piercing through smoke and dust, dramatic atmospheric perspective.
        Dual-tone palette: desaturated dark backgrounds vs intense neon lights, cyberpunk noir mood.
        """).strip()
    ),

    (
        "Cinematic Digital Oil (Classic Horror)",
        textwrap.dedent("""\
        Digital oil painting with visible canvas weave and thick impasto technique. Caravaggio-inspired extreme chiaroscuro.
        Rich palette: deep blood reds, intense indigo, earthy ochres, antique golds. Heavy, oppressive atmosphere.
        Visible brushwork, palette knife texture, classical Baroque horror composition.
        """).strip()
    ),

    (
        "Victorian Anatomical Engraving (Cursed Codex)",
        textwrap.dedent("""\
        Precision technical drawing on blueprint paper. 
        White lines on Prussian blue background, measured annotations in Helvetica font. 
        Isometric projection, draftman's pencil texture, registration marks, fold creases visible.
        """).strip()
    ),

    (
        "Unsettling Vintage Photography (Daguerreotype)",
        textwrap.dedent("""\
        19th century daguerreotype simulation. Monochromatic silver-gelatin process with cold metallic tones.
        High grain, glass plate scratches, chemical stains, strong vignetting, reduced depth of field.
        Static pose, direct serious gaze, found photograph aesthetic, corner mounting marks visible.
        """).strip()
    ),

    (
        "Gothic Watercolor (Mist and Ink)",
        textwrap.dedent("""\
        Dark atmospheric watercolor on cold-pressed paper. Wet-on-wet technique with bleeding edges.
        Grisaille palette (blacks, grays) with touches of deep indigo and crimson. Dominant mist effect.
        Visible paper texture, loose ink outlines, gothic literature illustration mood.
        """).strip()
    ),

    (
        "Macabre Stop-Motion (Tactile Tale)",
        textwrap.dedent("""\
        Laika/Tim Burton stop-motion style. Tactile materials: clay fingerprints, fabric texture, aged wood and metal.
        Exaggerated proportions (large eyes, thin limbs), visible armature wire, handcrafted imperfections.
        Theatrical studio lighting, miniature set depth, physical paint brushstroke texture.
        """).strip()
    ),

    (
        "Gothic Stained Glass (Dark Light)",
        textwrap.dedent("""\
        Gothic cathedral stained glass window design. Jewel-toned colors (ruby, sapphire, emerald, amber).
        Thick black lead came lines separating color planes, stylized flat design with formal symmetry.
        Strong backlit illumination, light refraction effects, medieval religious art composition.
        """).strip()
    ),

    (
        "High-Contrast Noir (Silhouettes and Shadows)",
        textwrap.dedent("""\
        Sin City-style graphic novel noir. Pure black and white only, no mid-tones or grays.
        Shadows as solid black masses, extreme negative space defining silhouettes.
        Graphic angular composition, single intense color accent (blood red) for dramatic emphasis.
        """).strip()
    ),
]


# --- NOMBRE DE ESTILOS (Común a ambas listas) ---
STYLE_NAMES = [n for n, _ in STYLE_PRESETS_GEMINI]

# Pistas para adaptar la idea al estilo visual escogido
STYLE_IDEA_HINTS = {
    "Novela Gráfica Oscura (horror gótico cinematográfico)": (
        "La historia debe sentirse como un cómic adulto de terror gótico: escenas muy visuales, "
        "con arquitectura dominante (calles estrechas, edificios antiguos, interiores decadentes) "
        "y momentos congelados en poses potentes. Evita tramas excesivamente intimistas sin "
        "entorno; el lugar debe ser casi un personaje más."
    ),

    "Fotorrealismo Cinematográfico (Thriller Moderno)": (
        "La historia debe situarse en un contexto contemporáneo reconocible: pisos actuales, "
        "hospitales, oficinas, parkings, bloques de viviendas, portales, centros comerciales. "
        "El terror debe apoyarse en detalles cotidianos hiperrealistas (luces de emergencia, "
        "cámaras de seguridad, puertas automáticas, pasillos interminables) y en la sensación "
        "de estar dentro de una película de thriller moderno."
    ),

    "Animación Neo-Noir (Estilo 'Arcane')": (
        "La historia debe encajar en un mundo híbrido entre lo industrial y lo fantástico: "
        "barrios bajos con talleres, tuberías, fábricas, callejones húmedos, pasarelas elevadas, "
        "y quizá algún elemento de tecnología extraña o energía misteriosa. Funciona muy bien "
        "si hay contraste entre zonas ricas y pobres, o entre lo mágico y lo mecánico."
    ),

    "Óleo Digital Cinematográfico (Terror Clásico)": (
        "La historia debe recordar al terror gótico clásico: mansiones antiguas, palacios, "
        "conventos, teatros viejos, cementerios monumentales o salones abarrotados de cuadros. "
        "El misterio tiene que apoyarse en grandes espacios cargados de historia, tradiciones "
        "familiares oscuras, maldiciones antiguas o secretos de linaje."
    ),

    "Grabado Anatómico Victoriano (Códice Maldito)": (
        "La historia debe encajar con un tono de códice antiguo o manual de anatomía victoriano: "
        "laboratorios, gabinetes de curiosidades, hospitales viejos, sanatorios, monasterios, "
        "archivos y bibliotecas polvorientas llenas de láminas, frascos y objetos clasificados. "
        "Idealmente hay documentos, esquemas, disecciones, diagramas o dibujos que escondan el horror."
    ),

    "Fotografía Antigua Inquietante (Daguerrotipo)": (
        "La historia debe ambientarse en una época compatible con fotografías antiguas "
        "(finales del siglo XIX o principios del XX), o bien en el presente pero girando "
        "en torno al hallazgo de viejas fotografías, retratos de familia o placas dañadas. "
        "Evita elementos claramente modernos en la escena principal (móviles, pantallas, redes sociales)."
    ),

    "Acuarela Gótica (Bruma y Tinta)": (
        "La historia debe apoyarse en la niebla, la lluvia, la bruma o la oscuridad suave: "
        "bosques, acantilados, cementerios, pueblos envueltos en niebla, estaciones abandonadas, "
        "ruinas medio ocultas por la lluvia. El miedo debe surgir de siluetas, sombras difusas y "
        "figuras que apenas se distinguen entre las manchas de luz y tinta."
    ),

    "Stop-Motion Macabro (Cuento Táctil)": (
        "La historia debe poder contarse como un cuento macabro con objetos físicos: muñecos, "
        "juguetes, marionetas, casas de muñecas, cementerios diminutos, mercados extraños, "
        "habitaciones llenas de cachivaches. Funciona especialmente bien si hay rituales, "
        "tradiciones familiares raras o maldiciones ligadas a objetos hechos a mano."
    ),

    "Vitral Gótico (Luz Oscura)": (
        "La historia debe funcionar bien como una escena casi iconográfica: composiciones claras, "
        "centradas y simbólicas. Lugares como iglesias, catedrales, ermitas, altares, órdenes "
        "secretas o cultos religiosos encajan muy bien. El misterio puede girar en torno a santos, "
        "milagros, herejías, símbolos repetidos en vidrieras o profecías representadas en cristal."
    ),

    "Alto Contraste Noir (Siluetas y Sombras)": (
        "La historia debe poder leerse en blanco y negro extremos: callejones mojados, azoteas, "
        "despachos con persianas, farolas solitarias, portales, estaciones nocturnas. Ideal para "
        "tramas urbanas de investigación, secretos, chantajes, encuentros clandestinos o persecuciones "
        "en penumbra donde las siluetas y las sombras digan más que los detalles."
    ),
}



def build_master_prompt(style_block: str, scene_text: str) -> str:
    return (
        style_block.strip() + "\n\n"
        "Dirección visual adicional:\n"
        "- Encuadre cinematográfico pensado para vídeo vertical 9:16.\n"
        "- Sensación de fotograma de una misma historia o universo visual.\n"
        "- Mantén atmósfera evocadora y narrativa.\n\n"
        "Escena específica a ilustrar:\n" + scene_text.strip()
    )

def _build_runware_prompt(style_block: str, scene_text: str, consistency_context: str, max_length: int = 1850) -> str:
    """
    Construye el prompt positivo para Runware/Qwen de forma compacta
    y garantiza que no supere max_length caracteres (margen de seguridad
    por debajo del límite de 1900 de Runware).

    Prioridad de preservación:
    1) Texto de la escena (scene_text)
    2) Contexto de consistencia
    3) Estilo visual
    """
    ratio_hint = "9:16 portrait, vertical aspect ratio"

    # Normalizamos textos
    scene_text = scene_text.strip()
    consistency_context = (consistency_context or "").strip()
    style_block = (style_block or "").strip()

    # Construimos en bloques
    header = f"(masterpiece, best quality, ultra-detailed), {ratio_hint}.\n\n"
    body_scene = scene_text + "\n\n"
    body_context = (consistency_context + "\n\n") if consistency_context else ""
    body_style = style_block

    # Ensamblado inicial
    final_prompt = header + body_scene + body_context + body_style

    # Si ya cabe, lo devolvemos tal cual
    if len(final_prompt) <= max_length:
        return final_prompt

    # --- 1) Intentar recortar ESTILO ---
    # No recortamos la escena ni el header.
    # Solo tocamos body_style y, si hace falta, body_context.
    def trim_text_at_sentence(text: str, target_len: int) -> str:
        """
        Recorta aproximadamente al target_len buscando un final de frase
        o espacio cercano, y añade '...'.
        """
        if len(text) <= target_len:
            return text
        cut = text[:target_len]
        # Intentamos cortar en el último punto o espacio
        for sep in [".", "!", "?", " "]:
            pos = cut.rfind(sep)
            if pos > int(target_len * 0.6):  # que no corte demasiado pronto
                cut = cut[:pos+1]
                break
        return cut.rstrip() + "..."

    # Recalculamos longitud y recortamos progresivamente
    def rebuild_prompt(ctx: str, style: str) -> str:
        parts = [header, body_scene]
        if ctx:
            parts.append(ctx + "\n\n")
        if style:
            parts.append(style)
        return "".join(parts)

    # Paso 1: recortar estilo si es largo
    final_prompt = rebuild_prompt(body_context, body_style)
    if len(final_prompt) > max_length and body_style:
        exceso = len(final_prompt) - max_length
        # Dejamos como mínimo unas ~300–400 chars para estilo si era muy largo
        target_len = max(0, len(body_style) - exceso)
        target_len = max(250, target_len)  # nunca bajamos de ~250 chars de estilo
        body_style = trim_text_at_sentence(body_style, target_len)
        final_prompt = rebuild_prompt(body_context, body_style)

    # Paso 2: si aún se pasa, recortar también el contexto
    if len(final_prompt) > max_length and body_context:
        exceso = len(final_prompt) - max_length
        target_len = max(200, len(body_context) - exceso)
        body_context = trim_text_at_sentence(body_context, target_len)
        final_prompt = rebuild_prompt(body_context, body_style)

    # Paso 3: por si acaso, clamp duro (no tocamos scene_text)
    if len(final_prompt) > max_length:
        final_prompt = final_prompt[:max_length].rstrip()

    return final_prompt

    
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


def extract_visual_consistency_brief(script_text: str, client: OpenAI, model_type: str = "gemini"):
    """
    Analiza el guion completo y extrae un brief visual de consistencia,
    DEVOLVIENDO SIEMPRE UN DICCIONARIO con estas claves:

    {
        "character": "...",
        "environment": "...",
        "lighting": "...",
        "objects": "..."
    }

    - Para 'gemini' puede ser algo más largo.
    - Para 'qwen' será muy compacto (pensado para prompts cortos).
    """
    print(f"📋 Analizando guión para extraer brief de consistencia (Modo: {model_type})...")

    # --- PROMPT PARA GEMINI (Detallado, pero estructurado en JSON) ---
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

    # --- PROMPT PARA QWEN (Muy compacto, también en JSON) ---
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

    if model_type == "qwen":
        final_system_prompt = system_prompt_qwen
        print("   (Usando brief corto estructurado para Qwen/Runware)")
    else:
        final_system_prompt = system_prompt_gemini
        print("   (Usando brief estructurado para Gemini)")

    try:
        response = client.chat.completions.create(
            model="gpt-5.1",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": final_system_prompt},
                {"role": "user", "content": f"Guion a analizar:\n\n{script_text}"}
            ]
        )
        brief_dict = json.loads(response.choices[0].message.content)
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
    Si viene como string o vacío, lo convierte a una estructura estándar.
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


def classify_scene_for_brief(scene_audio: str):
    """
    Dado el TEXTO DE AUDIO asociado a una escena, decide qué partes del brief
    tienen sentido para esa imagen.

    Devuelve un dict de flags:
    {
        "include_character": bool,
        "include_environment": bool,
        "include_objects": bool
    }

    'lighting' se aplica SIEMPRE desde el brief (es barato y ayuda a la coherencia).
    """
    text = (scene_audio or "").lower()

    # Muy simple, pero efectivo. Puedes tunearlo luego.
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
    Formato tipo etiqueta: valor, sin títulos largos.
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


# --- 2. GENERACIÓN DE IMÁGENES (Router: Gemini o Runware) ---

async def _generate_visuals_runware_async(
    visual_prompts_list: list,
    audio_scenes_list: list,
    scene_contexts_list: list,  # 🔹 NUEVO
    project_path: str,
    style_block: str,
    overwrite: bool,
    style_slug_for_pixelize: str
):
    """
    Función ASYNC interna para generar imágenes con Runware (Qwen-Image).
    MODIFICADA: Acepta una lista de prompts visuales generados por IA.
    """
    print(f"🎨 Generando imágenes con Runware (Opción ahorro: Qwen-Image)...")
    print(f"   Modelo: Qwen-Image ({QWEN_AIR_ID})")
    print(f"   Parámetros: CFGScale=2.5, Steps=20")

    runware = None
    all_images_successful = True
    
    try:
        # Conectar a Runware
        runware = Runware(api_key=RUNWARE_API_KEY)
        await runware.connect()
        print("\n✅ Conectado a Runware API para generación de imágenes.")

        # --- CAMBIO: Iteramos sobre la lista de prompts visuales ---
        for i, visual_prompt in enumerate(visual_prompts_list):
            
            # Obtenemos datos de la escena para los logs y el nombre de archivo
            image_id = f"{i+1}.png"
            audio_text = audio_scenes_list[i] if i < len(audio_scenes_list) else "" # Texto de audio para el log

            print(f"🖼️  Generando imagen {image_id} (Audio: '{audio_text[:40]}...'):")
            print(f"   Llamando con Visual Prompt: '{visual_prompt[:60]}...'")
            image_path = os.path.join(project_path, "images", image_id)
            os.makedirs(os.path.dirname(image_path), exist_ok=True)

            if os.path.exists(image_path) and not overwrite:
                print(f"   ✓ Imagen {image_id} ya existe, saltando generación.")
                continue

            image_generated = False
            
            try:
                # --- CAMBIO: Usamos el 'visual_prompt' en lugar de 'clean_text' ---
                scene_context = ""
                if scene_contexts_list and i < len(scene_contexts_list):
                    scene_context = scene_contexts_list[i]

                final_prompt = _build_runware_prompt(style_block, visual_prompt, scene_context, max_length=1850)


                # --- INICIO: Log de depuración (Tu código de la L. 1119) ---
                prompt_length = len(final_prompt)
                print("\n" + "="*80)
                print(f"   DEBUG: Preparando prompt para Qwen (Escena {i+1})")
                print(f"   LONGITUD TOTAL: {prompt_length} caracteres (Límite: 1900)")
                if prompt_length > 1900:
                    print("   !!!!!!!!!! ALERTA: EL PROMPT SUPERA EL LÍMITE !!!!!!!!!")
                print("="*80)
                print(final_prompt) # Imprimir el prompt completo
                print("="*80 + "\n")
                # --- FIN: Log de depuración ---

                # Parámetros de Runware
                params = {
                    "positivePrompt": final_prompt,
                    "negativePrompt": NEGATIVE_PROMPT,
                    "model": QWEN_AIR_ID,
                    "width": 768,   # 9:16
                    "height": 1344, # 9:16
                    "numberResults": 1,
                    "includeCost": True,
                    "CFGScale": 2.5,
                    "steps": 20
                }

                request = IImageInference(**params)
                images = await runware.imageInference(requestImage=request)

                if not images:
                    raise RuntimeError("La API de Runware no devolvió imágenes.")

                # Procesar respuesta
                image_res = images[0]
                image_url = image_res.imageURL
                cost = image_res.cost if hasattr(image_res, 'cost') and image_res.cost else "N/A"

                # Descargar y guardar la imagen
                response = requests.get(image_url, timeout=120)
                response.raise_for_status()
                with open(image_path, "wb") as f:
                    f.write(response.content)

                # Postproceso: Pixel Art
                if "pixel" in style_slug_for_pixelize:
                    pixelize_image(image_path, small_edge=256)
                    print("   ↳ postproceso: pixelize aplicado (downscale + NEAREST)")

                cost_str = f" (Coste: ${cost})" if cost != "N/A" else ""
                print(f"   ✔ Guardada: {image_path}{cost_str}")
                image_generated = True

            except Exception as e:
                # --- CAMBIO: Usamos 'i+1' para el log de error ---
                print(f"❌ Error en escena {i+1} (Runware): {e}") 
                if "1900 characters" in str(e):
                    print("   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    print("   ERROR: El prompt ha superado los 1900 caracteres.")
                    print("   Revisa la longitud del brief.txt y de los estilos.")
                    print("   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                all_images_successful = False
                break # Detener en caso de error

            time.sleep(1) # Pausa entre imágenes

    except Exception as e:
        print(f"❌ Error fatal conectando o generando con Runware: {e}")
        all_images_successful = False
    finally:
        if runware:
            await runware.disconnect()
            print("\n🔌 Desconectado de Runware API (imágenes).")

    return all_images_successful


def _generate_visuals_gemini(
    visual_prompts_list: list,
    audio_scenes_list: list,
    scene_contexts_list: list,
    project_path: str,
    client: OpenAI,
    style_block: str,
    overwrite: bool,
    image_model: str,
    style_slug_for_pixelize: str
):
    """
    Genera imágenes con Google Gemini usando:
    - visual_prompts_list: prompts visuales dedicados por escena
    - audio_scenes_list: texto de audio original (solo para logs)
    - scene_contexts_list: brief de consistencia específico por escena
    """
    print(f"🎨 Generando imágenes con Google Gemini (Opción alta calidad)...")
    print(f"   Modelo: {image_model}")
    
    all_images_successful = True
    MAX_RETRIES = 5

    total_scenes = len(visual_prompts_list)

    for idx, visual_prompt in enumerate(visual_prompts_list):
        clean_text = visual_prompt.strip()
        if not clean_text:
            continue

        audio_text = audio_scenes_list[idx] if idx < len(audio_scenes_list) else ""
        scene_ctx = scene_contexts_list[idx] if scene_contexts_list and idx < len(scene_contexts_list) else ""

        print(f"🖼️  Generando imagen para escena {idx+1}: '{audio_text[:60]}...'")
        image_path = os.path.join(project_path, "images", f"{idx+1}.png")
        os.makedirs(os.path.dirname(image_path), exist_ok=True)

        if os.path.exists(image_path) and not overwrite:
            print(f"   ✓ Imagen {idx+1}.png ya existe, saltando generación.")
            continue

        image_generated = False

        for attempt in range(MAX_RETRIES):
            try:
                # Prompt final: contexto de consistencia + estilo + prompt visual
                final_prompt = scene_ctx + "\n\n" + build_master_prompt(style_block, clean_text)
                final_prompt += f"\n\nEscena {idx+1} de {total_scenes} en la narrativa."
                print(f"   → Escena {idx+1}/{total_scenes} con contexto narrativo específico")

                response = gemini_client.models.generate_content(
                    model=image_model,
                    contents=[final_prompt],
                    config=types.GenerateContentConfig(
                        response_modalities=["IMAGE"],
                        image_config=types.ImageConfig(
                            aspect_ratio="9:16",
                        ),
                    ),
                )

                image_saved = False
                if hasattr(response, 'parts'):
                    for part in response.parts:
                        if hasattr(part, 'inline_data') and part.inline_data is not None:
                            pil_image = part.as_image()
                            pil_image.save(image_path)
                            image_saved = True
                            break

                if not image_saved:
                    raise RuntimeError("Gemini no devolvió datos de imagen válidos en response.parts")

                if "pixel" in style_slug_for_pixelize:
                    pixelize_image(image_path, small_edge=256)
                    print("   ↳ postproceso: pixelize aplicado (downscale + NEAREST)")

                print(f"   ✔ Guardada: {image_path}")
                image_generated = True
                break

            except Exception as e:
                error_message = str(e)
                if "SAFETY" in error_message or "BLOCKED" in error_message:
                    print(f"⚠️ Prompt bloqueado por seguridad (intento {attempt + 1}). Reescribiendo...")
                    rewritten_prompt = rewrite_prompt_for_safety(clean_text, client)
                    if rewritten_prompt:
                        clean_text = rewritten_prompt
                        continue
                    else:
                        all_images_successful = False
                        break
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
            print(f"🚫 Falló la generación de la imagen para la escena {idx+1} después de {MAX_RETRIES} intentos.")
            all_images_successful = False
            break

        time.sleep(1)

    return all_images_successful



def generate_visuals_for_script(
    script_text: str, # <-- Recibe el guion de audio completo
    project_path: str,
    client: OpenAI,
    overwrite: bool = False,
    image_model: str = "gemini-2.5-flash-image",
    image_quality: str = "standard", # No usado, pero mantenido por compatibilidad
    image_style: str = None,
):
    """
    Función "Router" (MODIFICADA) que orquesta la nueva arquitectura.
    PASO 1: Genera los prompts visuales dedicados.
    PASO 2: Genera el brief de consistencia (corto/largo).
    PASO 3: Llama al 'worker' (Gemini o Qwen) con los materiales correctos.
    """
    
    # --- 1. DEFINIR TIPO DE MODELO ---
    model_type = "gemini" # Por defecto
    if image_model == "qwen-image":
        model_type = "qwen"
    
    # --- 2. PREPARAR ESTILO (Coger de la biblioteca correcta) ---
    if not image_style:
        image_style = STYLE_NAMES[0]
    
    if model_type == "qwen":
        print("   (Usando biblioteca de estilos Qwen/Ultra-Cortos)")
        style_block = next((b for n, b in STYLE_PRESETS_QWEN if n == image_style), STYLE_PRESETS_QWEN[0][1])
    else:
        print("   (Usando biblioteca de estilos Gemini/Largos)")
        style_block = next((b for n, b in STYLE_PRESETS_GEMINI if n == image_style), STYLE_PRESETS_GEMINI[0][1])
        
    style_slug = image_style.lower()
    print(f"   Estilo seleccionado: {image_style}")

    # --- 3. PREPARAR ESCENAS (Audio) ---
    # Extraemos el texto de audio de cada escena para pasarlo como log
    audio_scenes_list = re.findall(r'\[imagen:\d+\.png\]\s*(.*?)(?=\n\s*\[|$)', script_text, re.DOTALL)
    if not audio_scenes_list:
        print("\n❌ ERROR CRÍTICO: No se encontraron descripciones de escenas en el guion.")
        return False

    # --- 4. PREPARAR PROMPTS VISUALES (¡NUEVA ARQUITECTURA!) ---
    # Llamamos a la nueva función que crea los prompts visuales
    visual_prompts_list = generate_visual_prompts_for_script(script_text, client)
    if not visual_prompts_list or len(visual_prompts_list) != len(audio_scenes_list):
        print("\n❌ ERROR CRÍTICO: No se pudieron generar los prompts visuales o el número no coincide.")
        print(f"   (Escenas de audio: {len(audio_scenes_list)}, Prompts visuales: {len(visual_prompts_list)})")
        return False
        
    # --- NUEVO: detectar escenas con protagonista según la etiqueta [PROTAGONISTA] ---
    character_flags = []
    cleaned_visual_prompts = []

    for p in visual_prompts_list:
        has_protagonist = "[PROTAGONISTA]" in p
        character_flags.append(has_protagonist)

        # Reemplazamos el marcador por algo neutro en el texto final
        cleaned = p.replace("[PROTAGONISTA]", "la protagonista")
        cleaned_visual_prompts.append(cleaned)

    visual_prompts_list = cleaned_visual_prompts
    print(f"   🧩 Escenas con protagonista detectadas: {sum(character_flags)} de {len(character_flags)}")
        

    # --- 5. PREPARAR BRIEF DE CONSISTENCIA (Largo o Corto) ---
    visual_brief_raw = extract_visual_consistency_brief(script_text, client, model_type=model_type)
    visual_brief = ensure_brief_dict(visual_brief_raw)

    # Guardar brief en texto legible para debug
    try:
        brief_file_path = os.path.join(project_path, "brief.txt")
        with open(brief_file_path, "w", encoding="utf-8") as f:
            f.write("PERSONAJE:\n" + (visual_brief["character"] or "(sin definir)") + "\n\n")
            f.write("ESCENARIO/UBICACIÓN:\n" + (visual_brief["environment"] or "(sin definir)") + "\n\n")
            f.write("ILUMINACIÓN/ATMÓSFERA:\n" + (visual_brief["lighting"] or "(sin definir)") + "\n\n")
            f.write("OBJETOS CLAVE:\n" + (visual_brief["objects"] or "(sin definir)") + "\n")
        print(f"   💾 Brief visual ({model_type}) guardado en: {brief_file_path}")
    except Exception as e:
        print(f"   ⚠️  Advertencia: No se pudo guardar el brief.txt: {e}")
 
    # --- 5.bis. Construir CONTEXTO POR ESCENA ---
    scene_contexts = []
    total_scenes = len(visual_prompts_list)

    for idx, audio_scene in enumerate(audio_scenes_list):
        flags = classify_scene_for_brief(audio_scene)

        # --- NUEVO: el personaje se controla SOLO por la etiqueta [PROTAGONISTA] ---
        if idx < len(character_flags) and character_flags[idx]:
            flags["include_character"] = True
        else:
            flags["include_character"] = False

        ctx = build_consistency_context_for_scene(
            visual_brief,
            include_character=flags["include_character"],
            include_environment=flags["include_environment"],
            include_objects=flags["include_objects"],
            total_scenes=total_scenes,
        )
        scene_contexts.append(ctx)

    print(f"   📖 Contextos de consistencia preparados por escena (total: {len(scene_contexts)})")

        
    # --- 6. EL ROUTER (Llamar al 'worker' correcto) ---
    if model_type == "qwen":
        if not runware_available:
            print("\n❌ Error: El modelo 'qwen-image' requiere Runware, pero no está configurado.")
            return False

        print(f"   📖 Brief de consistencia (qwen/corto) aplicado con lógica por escena")

        return asyncio.run(_generate_visuals_runware_async(
            visual_prompts_list=visual_prompts_list,
            audio_scenes_list=audio_scenes_list,
            scene_contexts_list=scene_contexts,
            project_path=project_path,
            style_block=style_block,
            overwrite=overwrite,
            style_slug_for_pixelize=style_slug
        ))
        
    else:
        print(f"   📖 Brief de consistencia (gemini/largo) aplicado con lógica por escena")

        return _generate_visuals_gemini(
            visual_prompts_list=visual_prompts_list,
            audio_scenes_list=audio_scenes_list,
            scene_contexts_list=scene_contexts,
            project_path=project_path,
            client=client,
            style_block=style_block,
            overwrite=overwrite,
            image_model=image_model,
            style_slug_for_pixelize=style_slug
        )

        
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
            model="gpt-5.1",
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


def generate_automatic_idea(client: OpenAI, style_name: str | None = None):
    """Analiza el master list y genera una nueva idea viral usando OpenAI, adaptada al estilo visual."""
    print("\n" + "="*70)
    print("🤖 MODO AUTOMÁTICO ACTIVADO")
    print("="*70)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    master_list_path = os.path.join(script_dir, "_master_project_top.txt")

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
            response = client.chat.completions.create(
                model="gpt-5.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )

            new_idea = response.choices[0].message.content.strip()
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
                print("⚠️ Idea con tema o inicio no deseado, o longitud rara. Reintentando...")
                if starts_bad:
                    print("   ↳ Motivo: inicio tipo 'medianoche' o similar.")
                if contains_banned:
                    print("   ↳ Motivo: referencia a coche/carretera/viaje.")
                if not longitud_ok:
                    print(f"   ↳ Motivo: longitud fuera de rango (palabras: {word_count}).")

        # Si después de 3 intentos no conseguimos una idea perfecta, usamos la última pero avisamos
        print("⚠️ No se pudo obtener una idea que cumpla todas las restricciones tras varios intentos.")
        if last_idea:
            print("\nÚltima idea generada (se utilizará de todas formas):")
            print(last_idea)
        return last_idea

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
    
    # --- CAMBIO IMPORTANTE AQUÍ ---
    parser.add_argument("--image-model", default="gemini-2.5-flash-image",
                        choices=["gemini-2.5-flash-image", "qwen-image"],
                        help=("Modelo de generación de imágenes. "
                              "Default: 'gemini-2.5-flash-image' (alta calidad, coste ~$0.04/img). "
                              "Alternativa: 'qwen-image' (ahorro, coste ~$0.007/img, usa Runware)."))
    # --- FIN DEL CAMBIO ---
    
    parser.add_argument("--image-quality", default=None,
                        help="Mantenido por compatibilidad, no usado.")
    parser.add_argument("--animate-images", action="store_true",
                        help=("Anima las imágenes generadas usando Seedance 1.0 Pro Fast en Runware "
                              "(864x480, 6s, ~$0.0315 por video - 65%% más barato que Replicate)."))
    args = parser.parse_args()

    # Para compartir el estilo visual entre la idea automática y la generación de imágenes
    chosen_style = None

    # --- MODO AUTOMÁTICO ---
    if args.idea is None and args.project_name is None:
        print("\n🚀 Modo automático detectado (no se proporcionaron --idea ni --project-name)")

        # 1. Ejecutar crear_indice_proyectos.py
        if not run_project_indexer():
            print("❌ Error al actualizar el índice de proyectos. Abortando.")
            return

        # 2. Elegir estilo visual ANTES de generar la idea automática
        chosen_style = interactive_style_selection()
        print(f"✅ Estilo seleccionado para este proyecto: {chosen_style}\n")

        # 3. Generar idea automáticamente
        auto_idea = generate_automatic_idea(client, style_name=chosen_style)
        if not auto_idea:
            print("❌ Error al generar idea automática. Abortando.")
            return

        # 4. Determinar siguiente número de proyecto
        next_number = get_next_project_number()

        # 5. Generar nombre de proyecto
        project_short_name = generate_project_name_from_idea(auto_idea, client)

        # 6. Construir nombre completo del proyecto
        args.idea = auto_idea
        args.project_name = f"{next_number}_{project_short_name}"

        print(f"\n✅ Proyecto automático configurado:")
        print(f"   📂 Nombre: {args.project_name}")
        print(f"   💡 Idea: {auto_idea[:100]}...")
        print("\n" + "="*70)
        print("Continuando con el flujo normal de generación...")
        print("="*70 + "\n")

    # Verificar que ahora tenemos idea y project-name
    if not args.idea or not args.project_name:
        print("❌ Error: Se requiere --idea y --project-name (o ninguno para modo automático)")
        parser.print_help()
        return

    # Si no se especificó image_quality (no se usa)
    if args.image_quality is None:
        args.image_quality = "standard"
        
    print(f"📸 Usando modelo de imagen seleccionado: {args.image_model}")

    project_path = args.project_name
    images_path = os.path.join(project_path, "images")

    # --- LÓGICA DE CREACIÓN DE PROYECTO ---
    if not os.path.exists(images_path):
        os.makedirs(images_path)
        print(f"📁 Proyecto creado en: ./{project_path}/")

        # Copiamos los archivos base
        print("📥 Copiando archivos base (musica.mp3, cierre.mp4)...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for file_name in ["musica.mp3", "cierre.mp4"]:
            source_file = os.path.join(script_dir, file_name)
            if os.path.exists(source_file):
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
            script_content = content_generated["script"].replace(".mp4", ".png")
            f.write(script_content)
            
        with open(social_file, "w", encoding="utf-8") as f:
            f.write(content_generated["social_post"])
            
        content = {"script": script_content}
            
    else:
        print("📝 Archivos de texto ya existen, saltando generación de contenido.")
        with open(script_file, "r", encoding="utf-8") as f:
            script_content = f.read().replace(".mp4", ".png")
            content = {"script": script_content}

    # Menú interactivo de estilo visual
    if chosen_style is None:
        chosen_style = interactive_style_selection()
        print(f"✅ Estilo seleccionado: {chosen_style}\n")
    else:
        print(f"✅ Usando estilo visual ya seleccionado: {chosen_style}\n")

    # Llamada a la función de imágenes (que ahora es un router)
    success = generate_visuals_for_script(
        content["script"],
        project_path,
        client,
        overwrite=args.overwrite_images,
        image_model=args.image_model,     # <-- Pasa el modelo elegido
        image_quality=args.image_quality,
        image_style=chosen_style,
    )

    if not success:
        return

    # Si se especificó --animate-images... (el resto de la función es igual)
    if args.animate_images:
        animate_success = animate_images_with_runware(
            project_path,
            overwrite=args.overwrite_images
        )
        if not animate_success:
            print("\n⚠️  Advertencia: Hubo problemas al animar las imágenes.")
            print("   Puedes intentar nuevamente con --animate-images --overwrite-images")
        else:
            # Actualizar texto.txt para usar .mp4
            script_file = os.path.join(project_path, "texto.txt")
            if os.path.exists(script_file):
                with open(script_file, "r", encoding="utf-8") as f:
                    script_content = f.read()
                updated_content = script_content.replace(".png]", ".mp4]")
                with open(script_file, "w", encoding="utf-8") as f:
                    f.write(updated_content)
                print("\n✅ Archivo texto.txt actualizado: .png → .mp4")
    else:
        print("\n💡 Tip: Puedes animar las imágenes agregando --animate-images a tu comando")

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
        subprocess.run(command, cwd=project_path, check=True, shell=True)
        print(f"\n✅ ¡Proceso completado! El vídeo final está en la carpeta '{project_path}/Out'.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar run.ps1: {e}")
    except FileNotFoundError:
        print(f"❌ Error: 'run.ps1' no encontrado en {run_ps1_path}. Revisa la ruta en el script.")



if __name__ == "__main__":
    main()