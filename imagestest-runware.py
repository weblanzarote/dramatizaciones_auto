import os
import pathlib
import datetime
import textwrap
import asyncio
import requests
import io
import sys
from PIL import Image
from slugify import slugify
from dotenv import load_dotenv

# --- CONFIGURACIÓN DE RUNWARE ---
# Cargar claves de API
load_dotenv()
RUNWARE_API_KEY = os.getenv("RUNWARE_API_KEY")
if not RUNWARE_API_KEY:
    raise ValueError("No se encontró la RUNWARE_API_KEY en .env")

# Importar librerías de Runware
try:
    from runware import Runware, IImageInference
    print("✅ Cliente de Runware importado.")
except ImportError:
    print("❌ 'runware' no está instalado. Ejecuta: pip install runware")
    sys.exit(1)
except Exception as e:
    raise RuntimeError(f"Error al importar Runware: {e}")

# --- MODELOS A PROBAR ---
RUNWARE_MODELS = [
    {
        "name": "Qwen-Image (Obedece mejor)",
        "id": "runware:108@1",
        "cost": 0.007
    },
    {
        "name": "FLUX.1 Krea [dev] (Alta calidad)",
        "id": "runware:107@1",
        "cost": 0.0098
    },
    {
        "name": "Juggernaut Lightning Flux (El + Rápido/Barato)",
        "id": "rundiffusion:110@101",
        "cost": 0.00169
    },
    {
        "name": "Seedream 3.0 (Coste alto)",
        "id": "bytedance:3@1",
        "cost": 0.018
    },
]

# --- PROMPT NEGATIVO ESTÁNDAR ---
# (Crítico para que los modelos de Runware den buenos resultados)
NEGATIVE_PROMPT = (
    "(worst quality, low quality, normal quality, plain, boring, blurry, jpeg artifacts, "
    "signature, watermark, text, username, error, poorly drawn, malformed, deformed, "
    "mutated, ugly, duplicate, out of frame, missing items, extra limbs, fused fingers)"
)

# ===== ESTILOS DE IMAGEN (presets) =====

STYLE_PRESETS = [
    # 1 — CINEMATIC WILDLIFE DOCUMENTARY
    ("Cinematic Wildlife Macro", """\
Award-winning wildlife photography. Extreme close-up shot on Sony A7R IV with 100mm f/2.8 macro lens. 
Shallow depth of field, razor-sharp focus on eyes, creamy bokeh background. 
Natural golden hour lighting, wet fur texture visible, National Geographic composition.
    """),

    # 2 — MIYAZAKI WATERCOLOR ANIME
    ("Studio Ghibli Watercolor Style", """\
Hand-painted watercolor anime aesthetic in the style of Studio Ghibli. 
Soft bleeding colors, visible paper texture, organic brushstroke edges. 
Gentle pastel palette of greens and blues, dreamy atmosphere, whimsical details.
    """),

    # 3 — BAROQUE OIL MASTERPIECE
    ("Baroque Oil Painting", """\
Masterful Baroque oil painting by Rembrandt. Rich impasto technique with thick, visible brushstrokes. 
Dramatic chiaroscuro lighting, deep shadows and golden highlights. 
Velvet textures, jewel-toned colors, classical composition with diagonal movement.
    """),

    # 4 — CYBERPUNK NEON NOIR
    ("Cyberpunk Neon Aesthetic", """\
Blade Runner inspired cyberpunk scene. Torrential rain reflecting neon signs (hot pink, cyan, electric purple). 
Wet asphalt with mirror-like reflections, volumetric fog, lens flares. 
Low-angle shot, anamorphic lens distortion, deep shadows with colored rim lighting.
    """),

    # 5 — VICTORIAN BOTANICAL ILLUSTRATION
    ("Scientific Botanical Art", """\
Precision botanical illustration from 1880s field journal. 
Ink outlines with layered watercolor washes on aged cream paper. 
Every vein and stamen meticulously detailed, scientific Latin annotations visible, pressed flower texture.
    """),

    # 6 — 1970s KODACHROME SLIDE
    ("Vintage Kodachrome Film", """\
Autumn 1975 Kodachrome 64 slide film. 
Characteristic warm color shift, fine grain structure, slight vignetting. 
Saturated oranges and reds, nostalgic family album aesthetic, soft corner blur, date stamp visible.
    """),

    # 7 — ENGINEERING TECHNICAL DRAWING
    ("Architectural Blueprint", """\
Precision technical drawing on blueprint paper. 
White lines on Prussian blue background, measured annotations in Helvetica font. 
Isometric projection, draftman's pencil texture, registration marks, fold creases visible.
    """),

    # 8 — GLITCH ART DATA MOSHING
    ("Intentional Digital Glitch", """\
Aggressive datamoshing with macroblocking artifacts, RGB channel separation, vertical sync errors. 
Corrupted JPEG headers producing unpredictable color shifts. 
Heavy compression artifacts, screen tear lines, hexadecimal code overlays.
    """),

    # 9 — MONET IMPRESSIONISM
    ("Monet Impressionist Landscape", """\
Claude Monet style plein air painting. 
Visible broken color technique, dappled light through short, thick strokes. 
Atmospheric perspective, lavender and teal palette, canvas weave texture, en plein air spontaneity.
    """),

    # 10 — DARK FANTASY CONCEPT ART
    ("Dark Fantasy Game Art", """\
Dungeons & Dragons concept art by Brom and Frank Frazetta. 
Oil painting meets digital, muscular dynamic poses, bloody weapons. 
Desaturated colors with blood red accents, grimdark atmosphere, hyper-detailed armor textures.
    """),

    # 11 — UKIYO-E WOODBLOCK PRINT
    ("Traditional Japanese Ukiyo-e", """\
Hokusai style woodblock print (浮世絵). 
Bold outlines with flat color planes, visible wood grain texture, bokashi gradient technique. 
S Prussian blue and beni red pigments, Japanese calligraphy stamp, washi paper texture.
    """),

    # 12 — MINIMALIST SCANDINAVIAN DESIGN
    ("Scandinavian Minimalism", """\
IKEA catalog minimalist photography. 
Bright white background, soft diffused lighting, geometric shadows. 
Muted pastel palette (powder pink, sage green), clean lines, negative space, hygge aesthetic.
    """),
]




# Tamaños para Runware (Tag, Width, Height)
ASPECT_RATIOS = [
    ("portrait_9x16", 768, 1344),   # vertical
    ("square_1x1", 1024, 1024),      # cuadrado
    ("landscape_16x9", 1344, 768),  # horizontal
]

DEFAULT_VARIATIONS = 1
OUTPUT_ROOT = "out_runware_tests" # Nueva carpeta de salida


# =========================
# FUNCIONES DE UTILIDAD
# =========================
def pixelize_image(path: pathlib.Path, small_edge: int = 256):
    """
    Hace un downscale fuerte y luego upscale con NEAREST para aumentar el tamaño de píxel.
    """
    try:
        im = Image.open(path).convert("RGBA")
        w, h = im.size
        if w <= 0 or h <= 0:
            return
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


def ask_scene_text():
    print("\nDescribe la escena que quieres ilustrar (para Runware):")
    scene = input("> ").strip()
    if not scene:
        scene = ("Una figura solitaria, con un abrigo largo y texturizado, está de pie en una plaza de adoquines antiguos. "
                 "La escena es nocturna y acaba de llover. La única luz proviene de dos fuentes: "
                 "una farola de gas de hierro forjado que arroja una luz ámbar, y el parpadeo de "
                 "un letrero de neón rojo de una tienda cercana. Los adoquines están mojados, "
                 "reflejando ambas luces. Sobre una verja de hierro, un cuervo mecánico observa "
                 "al espectador. La figura mira directamente a la cámara con una expresión indescifrable.")
    print(f"\nUsando escena: {scene[:100]}...")
    return scene


def list_styles():
    print("\n=== ESTILOS VISUALES DISPONIBLES ===")
    for idx, (name, _) in enumerate(STYLE_PRESETS, start=1):
        print(f"{idx}. {name}")
    print("\nElige uno o varios estilos separando con comas (ej: 1,3,5).")
    print("O pulsa Enter para usar TODOS los estilos.")
    raw = input("> ").strip()
    if not raw:
        return list(range(len(STYLE_PRESETS)))
    chosen_indices = []
    for part in raw.split(","):
        if part.strip().isdigit():
            i = int(part.strip()) - 1
            if 0 <= i < len(STYLE_PRESETS):
                chosen_indices.append(i)
    return chosen_indices or list(range(len(STYLE_PRESETS)))


def list_formats():
    print("\n=== FORMATOS DISPONIBLES (Aspect Ratios) ===")
    print("1. Vertical (9:16) - Recomendado")
    print("2. Cuadrado (1:1)")
    print("3. Horizontal (16:9)")
    print("4. Todos los formatos (Default: 1)")
    raw = input("> ").strip()
    if raw == "2":
        return [ASPECT_RATIOS[1]]
    elif raw == "3":
        return [ASPECT_RATIOS[2]]
    elif raw == "4":
        return ASPECT_RATIOS
    else:
        # Default es 1 (Vertical)
        return [ASPECT_RATIOS[0]]


def select_model():
    print("\n=== MODELOS DE RUNWARE A PROBAR ===")
    for idx, model in enumerate(RUNWARE_MODELS, start=1):
        print(f"{idx}. {model['name']} (Coste: ~${model['cost']})")
    
    chosen_idx = 0
    while chosen_idx < 1 or chosen_idx > len(RUNWARE_MODELS):
        raw = input(f"\nElige un modelo (1-{len(RUNWARE_MODELS)}) [Default: 1]: ").strip()
        if not raw:
            raw = "1"
        if raw.isdigit() and 1 <= int(raw) <= len(RUNWARE_MODELS):
            chosen_idx = int(raw)
        else:
            print("❌ Opción inválida.")
            
    chosen_model = RUNWARE_MODELS[chosen_idx - 1]
    print(f"✅ Modelo seleccionado: {chosen_model['name']} ({chosen_model['id']})")
    return chosen_model


def build_positive_prompt(style_block: str, scene_text: str, aspect_tag: str):
    """
    Construye el prompt positivo optimizado para Runware (Escena primero).
    """
    # Pista de aspect ratio para el modelo
    ratio_hint = "9:16 portrait"
    if "square" in aspect_tag:
        ratio_hint = "1:1 square"
    elif "landscape" in aspect_tag:
        ratio_hint = "16:9 landscape"

    return (
        f"(masterpiece, best quality, ultra-detailed, cinematic photography), {ratio_hint}.\n\n"
        "ESCENA PRINCIPAL (Objeto principal de la imagen):\n"
        f"{scene_text.strip()}\n\n"
        "======================================\n"
        "ESTILO VISUAL APLICADO (Contexto y atmósfera):\n"
        f"{style_block.strip()}"
    )


def save_image_from_url(image_url: str, path: pathlib.Path):
    """Descarga una imagen de una URL y la guarda en la ruta."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        response = requests.get(image_url, timeout=120)
        response.raise_for_status()
        # Guardar directamente los bytes descargados
        with open(path, "wb") as f:
            f.write(response.content)
    except Exception as e:
        print(f"   (Error al descargar/guardar imagen: {e})")
        raise


# =========================
# PROGRAMA PRINCIPAL (ASYNC)
# =========================

async def main_async(chosen_model, chosen_style_ids, scene_text, chosen_formats, n_variations):
    """
    Función asíncrona que se conecta a Runware y genera las imágenes.
    """
    runware = None
    try:
        # Conectar a Runware
        runware = Runware(api_key=RUNWARE_API_KEY)
        await runware.connect()
        print(f"\n✅ Conectado a Runware API. Generando imágenes...\n")

        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        # Crear carpeta de salida específica para este modelo
        model_slug = slugify(chosen_model['name'].split('(')[0].strip())
        out_root = pathlib.Path(OUTPUT_ROOT) / model_slug

        for style_idx in chosen_style_ids:
            style_name, style_block = STYLE_PRESETS[style_idx]
            style_slug = slugify(style_name)

            # Iteramos sobre la lista de formatos original
            for size_tag, original_width, original_height in chosen_formats:
                
                # Construir el prompt positivo (escena primero)
                prompt_text = build_positive_prompt(style_block, scene_text, size_tag)

                for v in range(n_variations):
                    
                    # --- CORRECCIÓN V6 ---
                    # 1. Empezamos con los parámetros óptimos (los del Playground)
                    params = {
                        "positivePrompt": prompt_text,
                        "negativePrompt": NEGATIVE_PROMPT,
                        "model": chosen_model['id'],
                        "width": original_width,
                        "height": original_height,
                        "numberResults": 1,
                        "includeCost": True,
                        "CFGScale": 2.5,  # Valor del Playground para estilos
                        "steps": 20       # Valor del Playground
                    }

                    # 2. Comprobar si es Seedream 3.0 y modificar los parámetros
                    if chosen_model['id'] == 'bytedance:3@1':
                        print(f"     (Nota: Detectado Seedream 3.0, ajustando parámetros...)")
                        
                        # 2a. Seedream NO soporta prompt negativo
                        params["negativePrompt"] = None 
                        
                        # 2b. Seedream NO soporta 'steps' (lo borramos)
                        del params["steps"]
                        
                        # 2c. Seedream SÍ soporta CFGScale, así que NO lo borramos.

                        # 2d. Seedream SÓLO soporta dimensiones específicas
                        if size_tag == 'portrait_9x16':
                            params["width"] = 720
                            params["height"] = 1280
                        elif size_tag == 'square_1x1':
                            params["width"] = 1024
                            params["height"] = 1024
                        elif size_tag == 'landscape_16_9':
                            params["width"] = 1280
                            params["height"] = 720
                        print(f"     (Ajustando dimensión, quitando negativePrompt y steps, PERO MANTENIENDO CFGScale=2.5)")
                    
                    # --- FIN DE LA LÓGICA ESPECIAL ---

                    print(f"   Generando [{model_slug}]: {style_slug} ({size_tag} @ {params['width']}x{params['height']}) v{v+1}...")
                    
                    try:
                        # 3. Llamar a la API con el diccionario de parámetros dinámico
                        request = IImageInference(**params)
                        
                        images = await runware.imageInference(requestImage=request)

                        if not images:
                            raise RuntimeError("La API no devolvió imágenes.")

                        # --- PROCESAR RESPUESTA DE RUNWARE ---
                        image_res = images[0]
                        image_url = image_res.imageURL
                        cost = image_res.cost if hasattr(image_res, 'cost') and image_res.cost else "N/A"

                        # Guardado
                        # Guardar todo en la misma carpeta del modelo (sin subcarpetas)
                        filename = f"{timestamp}_{style_slug}_{size_tag}_v{v+1}.png"
                        out_path = out_root / filename

                        save_image_from_url(image_url, out_path)
                        print(f"   ✔ Guardada (sin subcarpetas): {out_path} (Coste: ${cost})")

                        # --- POSTPROCESO para el estilo Pixel Art ---
                        if "pixel" in style_slug:
                            pixelize_image(out_path, small_edge=256)
                            print("     ↳ postproceso: pixelize aplicado (downscale + NEAREST)")

                    except Exception as e:
                        print(f"   ✖ Error con estilo '{style_name}', tamaño '{size_tag}', variación {v+1}:\n     {e}")
                        # Continuar con la siguiente imagen en caso de error
                        await asyncio.sleep(1)

    except Exception as e:
        print(f"\n❌ Error fatal durante la generación: {e}")
    finally:
        if runware:
            try:
                await runware.disconnect()
                print("\n🔌 Desconectado de Runware API.")
            except Exception as e:
                print(f"   (Advertencia al desconectar: {e})")


# =========================
# PUNTO DE ENTRADA (SYNC)
# =========================

def main():
    try:
        # --- Recopilar todas las opciones del usuario de forma síncrona ---
        chosen_model = select_model()
        chosen_style_ids = list_styles()
        scene_text = ask_scene_text()
        chosen_formats = list_formats()

        print("\n¿Cuántas variaciones por estilo/tamaño quieres genera? (Enter = 1)")
        raw_n = input("> ").strip()
        n_variations = int(raw_n) if raw_n.isdigit() and int(raw_n) > 0 else DEFAULT_VARIATIONS

        # --- Ejecutar el bucle principal asíncrono ---
        print("\n🎨 Configuración completa. Iniciando generación asíncrona...")
        asyncio.run(main_async(
            chosen_model,
            chosen_style_ids,
            scene_text,
            chosen_formats,
            n_variations
        ))

        model_slug = slugify(chosen_model['name'].split('(')[0].strip())
        out_root = pathlib.Path(OUTPUT_ROOT) / model_slug
        print(f"\n✅ Listo. Todas las imágenes están en:", out_root.resolve())

    except KeyboardInterrupt:
        print("\n\n❌ Proceso interrumpido por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Ha ocurrido un error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()