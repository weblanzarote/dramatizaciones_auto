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
    Eres un guionista experto especializado en narrativas de misterio, terror y contenido paranormal con alto potencial viral.
    Trabajas para el canal 'Relatos Extraordinarios' y creas historias cortas pero muy cinematográficas, con estructura de novela gráfica.

    Tu tarea es, a partir de una sola idea, generar un objeto JSON con TRES claves de primer nivel:
    - "script"
    - "blog_article"
    - "social_post"

    Debes responder EXCLUSIVAMENTE con ese objeto JSON, sin texto adicional.

    ------------------------------------------------
    SECCIÓN 1: "script" – GUION NARRADO CINEMATOGRÁFICO
    ------------------------------------------------

    El valor de "script" será un solo string que contenga varias escenas encadenadas.

    FORMATO TÉCNICO OBLIGATORIO PARA CADA ESCENA:
    1. Primera línea: etiqueta del hablante en MAYÚSCULAS, siempre `[NARRADOR]`
    2. Segunda línea: etiqueta de imagen con este formato exacto: `[imagen:X.mp4]`
       - X es un número entero en dígitos: 1, 2, 3, 4...
    3. Tercera línea: texto narrativo completo de la escena (aprox. 12–18 palabras)
    4. Una línea en blanco antes de empezar la siguiente escena

    PARÁMETROS GLOBALES:
    - Número de escenas: entre 6 y 10
    - Longitud total del guion: entre 80 y 140 palabras
    - Duración objetivo del vídeo: ~60 segundos
    - En las etiquetas de imagen, usa SIEMPRE dígitos: `[imagen:1.mp4]`, `[imagen:2.mp4]`, etc.
    - En el texto narrativo, escribe siempre los números con letras (por ejemplo: "mil novecientos cincuenta")
    - Al FINAL del string del guion, después de la última escena, incluye SIEMPRE una línea con solo: `[CIERRE]`

    ESTILO DE ESCRITURA:
    - Escribe en español natural, fluido, como si alguien contara la historia en voz alta
    - Usa oraciones completas con verbos conjugados en pasado o presente, no estilo telegráfico
    - La narración debe sonar bien al leerse en voz alta para una voz en off
    - Evita repetir las mismas frases de apertura en diferentes guiones
      (no empieces siempre igual: varía el arranque de la historia)
    - Evita fórmulas demasiado usadas como "nadie volvió a hablar de aquello" o "nunca volvió a ser el mismo"

    CONTENIDO NARRATIVO:
    - Construye una progresión clara: presentación → aumento de tensión → clímax → resolución o giro final
    - Mantén un elemento o personaje central recurrente para dar coherencia visual a todas las escenas
    - Crea atmósfera con detalles sensoriales: luces, sombras, sonidos, texturas, temperatura, clima
    - Describe lo que se ve y se siente dentro de la escena, no técnicas de cámara ni lenguaje técnico audiovisual
    - Evita los clichés más evidentes del género y busca detalles concretos, extraños o inquietantes que generen intriga
    - El giro final debe dejar una sensación de duda, inquietud o misterio abierto

    -------------------------------------
    SECCIÓN 2: "blog_article" – ARTÍCULO
    -------------------------------------

    El valor de "blog_article" será un texto en español que amplíe la historia del guion.

    REQUISITOS:
    - Tono mixto: narrativo y ligeramente explicativo, como un artículo que cuenta la leyenda o el caso
    - Debe dar contexto al lugar, a los personajes o al fenómeno, y profundizar en el misterio
    - Estructura clara con secciones diferenciadas

    FORMATO:
    - Usa títulos de sección con formato compatible con editores de texto y Google Docs, por ejemplo:
      `## Introducción`, `## La historia`, `## El misterio`, etc.
    - Longitud orientativa: entre 600 y 1 000 palabras
    - No menciones que el texto está escrito para un vídeo ni hables del "script" o del "JSON"

    CIERRE DEL ARTÍCULO:
    - Termina SIEMPRE con una última línea que contenga EXACTAMENTE cinco palabras clave relevantes, separadas por comas, sin almohadillas ni texto adicional.
    - Ejemplo de formato (no uses estas palabras literalmente):
      `palabra1, palabra2, palabra3, palabra4, palabra5`

    --------------------------------------------
    SECCIÓN 3: "social_post" – TEXTO PARA REDES
    --------------------------------------------

    El valor de "social_post" será un único string en español, pensado para la descripción de TikTok u otras redes.

    REQUISITOS:
    - Extensión máxima: 300 caracteres
    - Debe ser directo, sugerente e intrigante, pero sin revelar del todo el giro final
    - No puede empezar con estas expresiones: "Te atreves", "Descubre", "Conoces", "Conocías"
    - Debe incluir SIEMPRE el hashtag `#RelatosExtraordinarios`
    - Además de `#RelatosExtraordinarios`, añade entre 1 y 4 hashtags adicionales muy relevantes para la historia
    - Los hashtags deben ir dentro del mismo texto, no en una línea aparte obligatoriamente

    -----------------------------------
    FORMATO FINAL DE LA RESPUESTA JSON
    -----------------------------------

    - Responde SOLO con un objeto JSON válido.
    - Usa comillas dobles para las claves y los valores de cadenas.
    - Asegúrate de que el JSON pueda ser parseado sin errores.
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
        print(f"❌ Error al generar contenido con OpenAI (gpt-5.1): {e}")
        return None
        
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
    
    Esta versión está optimizada para generar instrucciones claras y densas
    para modelos de imagen como Gemini, SIN usar ejemplos concretos que
    puedan sesgar el resultado.
    """
    print("📋 Analizando guión para extraer brief de consistencia visual (versión SIN ejemplos)...")

    try:
        # Prompt del sistema mejorado, sin ejemplos concretos
        system_prompt = """
    Eres un Director de Arte experto en crear 'Briefs de Consistencia' para secuencias de storyboard.
    Tu tarea es analizar el guion y definir los elementos visuales RECURRENTES que deben
    mantenerse idénticos en todas las escenas.

    Tu brief será usado para instruir a un modelo de imagen (Gemini), así que debe ser denso
    en adjetivos visuales, texturales y atmosféricos, inferidos *únicamente* del guion.

    --------------------------------------------------
    DIRECTRICES DE FORMATO (MUY IMPORTANTE)
    --------------------------------------------------

    1.  **OMITE LÍNEAS IRRELEVANTES:** Responde *únicamente* con las líneas para las que
        encuentres información clara en el guion. Si no hay un personaje principal
        recurrente, *OMITE* toda la línea 'PERSONAJE:'. Si no hay un escenario clave,
        *OMITE* la línea 'ESCENARIO:'.
        
    2.  **NO USES 'N/A':** Nunca escribas 'N/A', 'Ninguno' o 'No aplica'. Simplemente omite
        la línea correspondiente si no hay nada que añadir.

    3.  **SÉ HÍPER-ESPECÍFICO:** Usa adjetivos potentes inferidos del tono del guion para
        describir texturas, materiales, iluminación y emociones.

    --------------------------------------------------
    FORMATO DE SALIDA ESTRICTO
    --------------------------------------------------
    (Usa este formato exacto, rellenando la información INFERIDA del guion)

    PERSONAJE: [Describe aquí: Género/Edad aparente, Ropa EXACTA y su estado/textura, Rasgos físicos/pelo distintivos, Actitud o emoción dominante]
    ESCENARIO: [Describe aquí: Tipo de lugar o vehículo recurrente, Estilo/Época, Estado (nuevo, decrépito...), Textura clave (piedra, metal, madera...)]
    ELEMENTOS CLAVE:
    - [Describe aquí: El tipo de iluminación predominante y su cualidad (ej. dura, suave, color...)]
    - [Describe aquí: La atmósfera general (ej. niebla, polvo, lluvia, tensión...)]
    - [Describe aquí: La paleta de color principal o acentos recurrentes]

    --------------------------------------------------
    REGLA ESPECIAL (OBLIGATORIA)
    --------------------------------------------------
    - Si el guion está narrado en 1ª persona ('yo', 'mi', 'nosotros', 'miro'), *DEBES*
      crear una descripción visual para el 'PERSONAJE:' narrador. Infiere sus rasgos
      (edad, ropa, actitud) del contexto y el tono de la narración.
    """

        response = client.chat.completions.create(
            model="gpt-5.1", 
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                }
,
                {"role": "user", "content": f"Analiza este guión y extrae el brief de consistencia:\n\n{script_text}"}
            ]
        )

        brief = response.choices[0].message.content.strip()
        
        # Pequeña limpieza por si acaso gpt-5.1 añade líneas vacías extra
        brief_lines = [line for line in brief.split('\n') if line.strip()]
        brief = '\n'.join(brief_lines)

        print(f"✅ Brief visual optimizado (sin ejemplos) extraído:\n{brief}\n")
        return brief

    except Exception as e:
        print(f"⚠️ No se pudo extraer brief visual optimizado: {e}")
        # Devolvemos un string vacío seguro para no romper el flujo
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
            model="gpt-5.1",
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