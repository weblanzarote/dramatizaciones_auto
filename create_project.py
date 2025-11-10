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

# --- CONFIGURACIÓN INICIAL ---
# Cargar claves de API de forma segura desde el archivo .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("No se encontró la OPENAI_API_KEY. Asegúrate de que tu archivo .env está configurado.")

# Inicializamos el cliente de OpenAI que se usará para texto e imágenes
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    raise RuntimeError(f"Error al inicializar el cliente de OpenAI: {e}")

# Configuración de Replicate (opcional, solo si se usa --animate-images)
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
replicate_client = None
if REPLICATE_API_TOKEN:
    try:
        import replicate
        replicate_client = replicate.Client(api_token=REPLICATE_API_TOKEN)
    except ImportError:
        print("⚠️  Advertencia: 'replicate' no está instalado. Ejecuta: pip install replicate")
    except Exception as e:
        print(f"⚠️  Advertencia: Error al inicializar Replicate: {e}")


# --- 1. GENERACIÓN DE CONTENIDO CREATIVO CON OPENAI (gpt-5-mini) ---
def generate_creative_content(idea: str):
    """Llama a la API de OpenAI (gpt-5-mini) para obtener guion, post y texto para redes."""
    print(f"🧠 Generando contenido creativo con OpenAI (gpt-5-mini) para la idea: '{idea}'...")

    # Prompt MEJORADO con instrucciones de formato estrictas para el guion
    system_prompt = """
    Eres un creador de contenido viral para la cuenta 'Relatos Extraordinarios'.
    Generarás un objeto JSON con tres claves: "script", "blog_article" y "social_post".

    Reglas para "script":
    - La estructura del guion es MUY ESTRICTA y debe seguir este formato por cada escena:
    1.  Un tag de hablante en su propia línea (ej. `[NARRADOR]`).
    2.  Un tag de imagen en la siguiente línea (ej. `[imagen:1.mp4]`).
    3.  El texto descriptivo de la escena en las líneas siguientes.
    4.  Debe haber una línea en blanco entre cada bloque de escena.
    - Ejemplo de una escena:
    [NARRADOR]
    [imagen:1.mp4]
    En los valles más profundos, se susurran leyendas.

    - El guion completo debe tener entre 7 y 10 escenas.
    - La longitud total debe ser de 200 a 250 palabras.
    - Usa `[NARRADOR]` como hablante para todas las escenas.
    - IMPORTANTE: Las imágenes deben estar numeradas con DÍGITOS NUMÉRICOS: `[imagen:1.mp4]`, `[imagen:2.mp4]`, `[imagen:3.mp4]`, etc. NO uses palabras como "uno", "dos", "tres".
    - Los números en el TEXTO NARRATIVO deben estar escritos con letras (ej: "mil novecientos cincuenta y cinco"), pero los números en las etiquetas [imagen:N.mp4] deben ser dígitos (1, 2, 3...).
    - El guion DEBE terminar obligatoriamente con la etiqueta `[CIERRE]` en su propia línea.
    - Para mantener la coherencia visual, la historia debe centrarse en un único elemento o personaje recurrente (por ejemplo, un faro abandonado, una figura sombría, un objeto maldito). Las descripciones de las escenas deben reforzar este elemento central.
    
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
            model="gpt-5-mini",
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
    ("Sombras de Gaia (siluetas atmosféricas)", textwrap.dedent("""\
    Crea una ilustración atmosférica con un estilo visual distintivo llamado 'Sombras de Gaia'.
    Estilo visual:
    - Siluetas expresivas: figuras en sombra (sin rasgos) con poses que transmiten emoción.
    - Atmósfera lumínica: luz difusa, contraluces, haces de luz entre niebla/polvo.
    - Paleta limitada: azules oscuros/negros/grises con acento cálido (ámbar/dorado/rojo tenue).
    - Composición cinematográfica vertical, textura orgánica y grano leve.
    - Coherencia narrativa entre imágenes, como si todas fueran del mismo universo.
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


# --- 2. GENERACIÓN DE IMÁGENES ESTÁTICAS CON OPENAI ---
# --- VERSIÓN MEJORADA CON REINTENTO AUTOMÁTICO ---
def generate_visuals_for_script(
    script_text: str,
    project_path: str,
    client: OpenAI,
    overwrite: bool = False,
    image_model: str = "dall-e-3",
    image_quality: str = "standard",
    image_style: str = None,
):
    """
    Genera imágenes para el guion con un sistema de reintento automático
    que reescribe los prompts bloqueados por el sistema de seguridad,
    usando un estilo visual seleccionable.

    Args:
        script_text: El texto del guion con las etiquetas [imagen:N.png]
        project_path: Ruta al directorio del proyecto
        client: Cliente de OpenAI
        overwrite: Si es True, regenera imágenes existentes. Si es False, las salta.
        image_model: Modelo de generación (gpt-image-1-mini, gpt-image-1, dall-e-3, dall-e-2)
        image_quality: Calidad (low/medium/high para GPT Image; standard/hd para DALL·E)
        image_style: Nombre del estilo a aplicar (de STYLE_NAMES). Si None, usa el primero.
    """
    print(f"🎨 Empezando la generación de imágenes con reintento automático...")
    print(f"   Modelo: {image_model} | Calidad: {image_quality}")

    # Tamaños recomendados según modelo (vertical por defecto)
    size_map = {
        "gpt-image-1-mini": "1024x1536",  # válido para mini
        "gpt-image-1":      "1024x1536",
        "dall-e-3":         "1024x1792",
        "dall-e-2":         "1024x1024",
    }
    image_size = size_map.get(image_model, "1024x1536")
    print(f"   Tamaño: {image_size}")

    # Estilo elegido
    if not image_style:
        image_style = STYLE_NAMES[0]
    style_block = next((b for n, b in STYLE_PRESETS if n == image_style), STYLE_PRESETS[0][1])
    print(f"   Estilo: {image_style}")

    # Extra: fondo transparente automáticamente solo para modelos GPT Image si lo quisieras
    supports_background = image_model.startswith("gpt-image-1")
    transparent_bg = False  # cámbialo a True si quieres PNG transparente para overlays

    # Extraer escenas
    scenes = re.findall(r'\[imagen:\d+\.png\]\s*(.*?)(?=\n\s*\[|$)', script_text, re.DOTALL)
    if not scenes:
        print("\n❌ ERROR CRÍTICO: No se encontraron descripciones de escenas en el guion.")
        return False

    all_images_successful = True
    MAX_RETRIES = 5  # intentos por imagen

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

        # Prompt específico de la escena (mutable si hay reescrituras por moderación)
        current_scene_prompt = f"{clean_text}"
        image_generated = False

        for attempt in range(MAX_RETRIES):
            try:
                # Construir prompt final con el estilo
                final_prompt = build_master_prompt(style_block, current_scene_prompt)

                # Preparar kwargs (evita enviar background=None)
                kwargs = {
                    "model": image_model,
                    "prompt": final_prompt,
                    "size": image_size,
                    "quality": image_quality,
                    "n": 1,
                }
                if supports_background and transparent_bg:
                    kwargs["background"] = "transparent"

                response = client.images.generate(**kwargs)

                # Validar datos
                if not response.data or len(response.data) == 0:
                    raise RuntimeError("La respuesta de la API no contiene datos de imagen")

                image_data = response.data[0]
                image_url = getattr(image_data, "url", None)
                b64_json = getattr(image_data, "b64_json", None)

                if image_url:
                    r = requests.get(image_url, timeout=60)
                    r.raise_for_status()
                    with open(image_path, "wb") as f:
                        f.write(r.content)
                    image_generated = True

                elif b64_json:
                    image_bytes = base64.b64decode(b64_json)
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                    image_generated = True

                else:
                    raise RuntimeError(f"La API no devolvió ni url ni b64_json. Respuesta: {image_data}")

                # Postproceso: Pixel Art (si el estilo lo indica)
                if "pixel" in image_style.lower():
                    # Ajusta small_edge para más/menos “chunky”
                    pixelize_image(image_path, small_edge=256)
                    print("   ↳ postproceso: pixelize aplicado (downscale + NEAREST)")

                print(f"   ✔ Guardada: {image_path}")
                break  # éxito → sal del bucle de reintentos

            except openai.BadRequestError as e:
                if getattr(e, "code", None) == "moderation_blocked":
                    print(f"⚠️ Prompt bloqueado (intento {attempt + 1}). Reescribiendo...")
                    rewritten_part = rewrite_prompt_for_safety(current_scene_prompt, client)
                    if rewritten_part:
                        current_scene_prompt = rewritten_part
                        continue
                    else:
                        print("❌ No se pudo reescribir el prompt. Abortando esta imagen.")
                        break
                else:
                    print(f"❌ Error de API no relacionado con moderación: {e}")
                    all_images_successful = False
                    break

            except openai.APIError as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"⚠️ Error temporal del servidor (intento {attempt + 1}/{MAX_RETRIES}). Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Error del servidor después de {MAX_RETRIES} intentos: {e}")
                    all_images_successful = False
                    break

            except requests.exceptions.RequestException as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"⚠️ Error de red al descargar imagen (intento {attempt + 1}/{MAX_RETRIES}). Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Error de red después de {MAX_RETRIES} intentos: {e}")
                    all_images_successful = False
                    break

            except RuntimeError as e:
                print(f"❌ Error de validación: {e}")
                print(f"   Modelo '{image_model}' podría no soportar este tamaño/calidad.")
                all_images_successful = False
                break

            except Exception as e:
                print(f"❌ Error inesperado al generar la imagen para la escena {i}: {e}")
                all_images_successful = False
                break

        if not image_generated:
            print(f"🚫 Falló la generación de la imagen para la escena {i} después de {MAX_RETRIES} intentos.")
            all_images_successful = False
            break  # detén el proceso si una imagen falla definitivamente

    if all_images_successful:
        print("✅ Todas las imágenes han sido generadas con éxito.")
        return True
    else:
        print("\n🚫 Proceso detenido debido a un error en la generación de imágenes.")
        return False


# --- 2.5. ANIMACIÓN DE IMÁGENES CON REPLICATE ---
def animate_images_with_replicate(project_path: str, overwrite: bool = False):
    """
    Anima las imágenes PNG del proyecto usando Seedance 1.0 Pro Fast en Replicate.

    Args:
        project_path: Ruta al directorio del proyecto
        overwrite: Si es True, regenera videos existentes. Si es False, los salta.

    Returns:
        True si todas las animaciones se generaron correctamente, False si hubo errores.
    """
    if not replicate_client:
        print("\n❌ Error: Replicate no está configurado correctamente.")
        print("   Asegúrate de:")
        print("   1. Tener REPLICATE_API_TOKEN en tu archivo .env")
        print("   2. Haber instalado: pip install replicate")
        return False

    print("\n🎬 Iniciando animación de imágenes con Replicate...")
    print("   Modelo: bytedance/seedance-1-pro-fast")
    print("   Duración: 5 segundos por video")
    print("   Resolución: 480p (óptima para redes sociales)")
    print("   Costo: $0.015/segundo → ~$0.75 por proyecto de 10 videos 🎯\n")

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

    all_videos_successful = True
    MAX_RETRIES = 3

    for image_file in image_files:
        image_number = image_file.split('.')[0]
        image_path = os.path.join(images_path, image_file)
        video_path = os.path.join(images_path, f"{image_number}_animated.mp4")

        # Si ya existe y no queremos sobrescribir
        if os.path.exists(video_path) and not overwrite:
            print(f"✓ Video {image_number}_animated.mp4 ya existe, saltando animación.")
            continue

        print(f"🎥 Animando {image_file}...")
        video_generated = False

        for attempt in range(MAX_RETRIES):
            try:
                # Abrir la imagen y enviarla a Replicate
                with open(image_path, "rb") as img_file:
                    output = replicate_client.run(
                        "bytedance/seedance-1-pro-fast",
                        input={
                            "image": img_file,
                            "prompt": "Smooth cinematic camera movement, subtle atmospheric motion",
                            "resolution": "480p",
                            "duration": 5
                        }
                    )

                # El output es una URL al video generado
                if output:
                    # Manejar diferentes tipos de output de Replicate
                    if isinstance(output, str):
                        video_url = output
                    elif hasattr(output, 'url'):  # FileOutput object
                        video_url = output.url
                    elif isinstance(output, list) and len(output) > 0:
                        first_item = output[0]
                        video_url = first_item if isinstance(first_item, str) else first_item.url
                    else:
                        raise RuntimeError(f"Formato de output no reconocido: {type(output)}")

                    # Descargar el video
                    print(f"   📥 Descargando video desde Replicate...")
                    response = requests.get(video_url, timeout=120)
                    response.raise_for_status()

                    with open(video_path, "wb") as video_file:
                        video_file.write(response.content)

                    print(f"   ✔ Video guardado: {video_path}")
                    video_generated = True
                    break
                else:
                    raise RuntimeError("Replicate no devolvió una URL de video")

            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = (attempt + 1) * 3
                    print(f"   ⚠️  Error (intento {attempt + 1}/{MAX_RETRIES}): {e}")
                    print(f"   Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"   ❌ Error después de {MAX_RETRIES} intentos: {e}")
                    all_videos_successful = False
                    break

        if not video_generated:
            print(f"🚫 Falló la animación de {image_file}")
            all_videos_successful = False
            # Continuar con las siguientes imágenes en lugar de abortar completamente

        # Pequeña pausa entre llamadas para no saturar la API
        time.sleep(1)

    if all_videos_successful:
        print("\n✅ Todas las imágenes han sido animadas con éxito.")
        print(f"   Los videos están en: {images_path}/")
        print(f"   Archivos: 1_animated.mp4, 2_animated.mp4, etc.")
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
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": (
                    "Eres un asistente que genera nombres cortos de proyecto. "
                    "Dado un texto descriptivo, debes crear un nombre corto de 1-3 palabras "
                    "en MAYÚSCULAS que capture la esencia del contenido. "
                    "El nombre debe ser memorable, descriptivo y apropiado para un proyecto de misterio/paranormal. "
                    "RESPONDE SOLO CON EL NOMBRE, SIN EXPLICACIONES. "
                    "Ejemplos: METROMADRID, CASTILLOCARDONA, PALACIOLINARES, HOMBREPEZ"
                )},
                {"role": "user", "content": f"Genera un nombre de proyecto para: {idea_text}"}
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
                        choices=["gpt-image-1-mini", "gpt-image-1", "dall-e-3", "dall-e-2"],
                        help="Modelo de generación de imágenes. Si no se especifica, se mostrará un menú interactivo.")
    parser.add_argument("--image-quality", default=None,
                        help="Calidad de imagen: low/medium/high (GPT Image) o standard/hd (DALL-E). Si no se especifica, se mostrará un menú interactivo.")
    parser.add_argument("--animate-images", action="store_true",
                        help="Anima las imágenes generadas usando Seedance 1.0 Pro Fast (480p, ~$0.075 por video de 5s).")
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
        args.image_model = "gpt-image-1-mini"
        args.image_quality = "medium"
        print(f"📸 Usando modelo de imagen por defecto: {args.image_model} ({args.image_quality})")

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

    # Si se especificó --animate-images, animar las imágenes con Replicate
    if args.animate_images:
        animate_success = animate_images_with_replicate(
            project_path,
            overwrite=args.overwrite_images
        )
        if not animate_success:
            print("\n⚠️  Advertencia: Hubo problemas al animar las imágenes.")
            print("   Puedes intentar nuevamente con --animate-images --overwrite-images")
            # No abortamos, continuamos con el proceso normal
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