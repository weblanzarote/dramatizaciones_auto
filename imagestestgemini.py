import os
import pathlib
import datetime
import textwrap
from PIL import Image
from slugify import slugify
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types

# =========================
# CONFIGURACIÓN PREDEFINIDA
# =========================

# Cargar claves de API
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("No se encontró la GEMINI_API_KEY en .env")

# Inicializar cliente de Gemini
try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    print("✅ Cliente de Google Gemini inicializado.")
except Exception as e:
    raise RuntimeError(f"Error al inicializar el cliente de Gemini: {e}")


# ===== ESTILOS DE IMAGEN (presets) =====
# (Son los mismos 10 estilos que ya tienes)
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


# Tamaños válidos para Gemini (Aspect Ratios)
ASPECT_RATIOS = [
    ("portrait_9x16",  "9:16"),   # vertical (recomendado para redes)
    ("square_1x1",     "1:1"),
    ("landscape_16x9", "16:9"), # horizontal
]

DEFAULT_MODEL = "gemini-2.5-flash-image"
DEFAULT_VARIATIONS = 1
OUTPUT_ROOT = "out_gemini" # Carpeta de salida diferente


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
    print("\nDescribe la escena que quieres ilustrar (para Gemini):")
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
    print("\n=== ESTILOS DISPONIBLES (para Gemini) ===")
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
    print("4. Todos los formatos")
    raw = input("> ").strip()
    if raw == "1":
        return [ASPECT_RATIOS[0]]
    elif raw == "2":
        return [ASPECT_RATIOS[1]]
    elif raw == "3":
        return [ASPECT_RATIOS[2]]
    else:
        return ASPECT_RATIOS


def build_prompt(style_block: str, scene_text: str):
    return (
        style_block.strip()
        + "\n\nDirección visual adicional:\n"
          "- Encuadre cinematográfico pensado para vídeo social.\n"
          "- Sensación de fotograma de una misma historia o universo visual.\n"
          "- Mantén atmósfera evocadora y narrativa.\n\n"
        + "Escena específica a ilustrar:\n"
        + scene_text.strip()
    )


def save_pil_image(pil_image: Image.Image, path: pathlib.Path):
    """Guarda una imagen PIL en la ruta especificada."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Corrección: Eliminamos el argumento "PNG" redundante.
    # La librería infiere el formato desde la extensión .png del 'path'.
    pil_image.save(path)


# =========================
# PROGRAMA PRINCIPAL
# =========================

def main():
    chosen_style_ids = list_styles()
    scene_text = ask_scene_text()
    chosen_formats = list_formats()

    print("\n¿Cuántas variaciones por estilo/tamaño quieres generar? (Enter = 1)")
    raw_n = input("> ").strip()
    n_variations = int(raw_n) if raw_n.isdigit() and int(raw_n) > 0 else DEFAULT_VARIATIONS

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_root = pathlib.Path(OUTPUT_ROOT)

    print("\n🎨 Generando imágenes con Google Gemini... puede tardar unos minutos.\n")

    for style_idx in chosen_style_ids:
        style_name, style_block = STYLE_PRESETS[style_idx]
        style_slug = slugify(style_name)

        for size_tag, aspect_ratio_val in chosen_formats:
            prompt = build_prompt(style_block, scene_text)

            for v in range(n_variations):
                try:
                    print(f"   Generando [Gemini]: {style_slug} ({size_tag}) v{v+1}...")
                    
                    # --- LLAMADA A GEMINI ---
                    response = gemini_client.models.generate_content(
                        model=DEFAULT_MODEL,
                        contents=[prompt],
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"],
                            image_config=types.ImageConfig(
                                aspect_ratio=aspect_ratio_val,
                            ),
                        ),
                        # Opcional: añadir configuraciones de seguridad si fueran necesarias
                        # safety_settings={
                        #     'HATE': 'BLOCK_NONE',
                        #     'HARASSMENT': 'BLOCK_NONE',
                        #     'SEXUAL': 'BLOCK_NONE',
                        #     'DANGEROUS': 'BLOCK_NONE'
                        # }
                    )

                    # --- PROCESAR RESPUESTA DE GEMINI ---
                    image_saved = False
                    if hasattr(response, 'parts'):
                        for part in response.parts:
                            if hasattr(part, 'inline_data') and part.inline_data is not None:
                                # Usar el método as_image() para obtener la imagen PIL
                                pil_image = part.as_image()
                                
                                # Guardado
                                filename = f"{timestamp}_{style_slug}_{size_tag}_v{v+1}.png"
                                out_path = out_root / style_slug / size_tag / filename
                                save_pil_image(pil_image, out_path)
                                print(f"✔ {out_path}")
                                image_saved = True

                                # --- POSTPROCESO para el estilo Pixel Art ---
                                if "pixel" in style_slug:
                                    pixelize_image(out_path, small_edge=256)
                                    print("  ↳ postproceso: pixelize aplicado (downscale + NEAREST)")
                                
                                break # Salir del bucle de 'parts'

                    if not image_saved:
                        # Manejar el caso donde Gemini no devuelve imagen (ej. bloqueada)
                        # Imprimir el 'prompt_feedback' si existe
                        feedback = getattr(response, 'prompt_feedback', 'No feedback')
                        raise RuntimeError(f"Gemini no devolvió datos de imagen válidos. Feedback: {feedback}")

                except Exception as e:
                    print(f"✖ Error con estilo '{style_name}', tamaño '{size_tag}', variación {v+1}:\n  {e}")

    print("\n✅ Listo. Todas las imágenes están en:", out_root.resolve())


if __name__ == "__main__":
    main()