import os
import base64
import pathlib
import datetime
import textwrap
from PIL import Image
from slugify import slugify
from dotenv import load_dotenv
from openai import OpenAI

# =========================
# CONFIGURACIÓN PREDEFINIDA
# =========================

STYLE_PRESETS = [
    # 1) Sombras de Gaia
    (
        "Sombras de Gaia (siluetas atmosféricas)",
        textwrap.dedent("""\
        Crea una ilustración atmosférica con un estilo visual distintivo llamado 'Sombras de Gaia'.
        Estilo visual:
        - Siluetas expresivas: figuras en sombra (sin rasgos) con poses que transmiten emoción.
        - Atmósfera lumínica: luz difusa, contraluces, haces de luz entre niebla/polvo.
        - Paleta limitada: azules oscuros/negros/grises con acento cálido (ámbar/dorado/rojo tenue).
        - Composición cinematográfica vertical, textura orgánica y grano leve.
        - Coherencia narrativa entre imágenes, como si todas fueran del mismo universo.
        """).strip()
    ),

    # 2) Fábulas Nocturnas
    (
        "Fábulas Nocturnas (animales simbólicos)",
        textwrap.dedent("""\
        Crea una ilustración con animales antropomorfos que encarnan roles humanos
        (por ejemplo, un cuervo mensajero vigilante, un zorro astuto, un gato errante melancólico).
        Estilo visual:
        - Tonos nocturnos con bruma y luz teatral.
        - Sombras largas y enfoque narrativo en la pose.
        - Paleta reducida con un único color de acento emocional.
        - Sensación de fábula oscura y cuento moderno.
        """).strip()
    ),

    # 3) Tinta + Acento
    (
        "Tinta + Acento (monocromo)",
        textwrap.dedent("""\
        Ilustración monocromática estilo tinta, con un único color de acento que resalte un objeto o emoción.
        Estilo visual:
        - Alto contraste, negros profundos y blancos limpios.
        - Textura de pincel seco, bordes ligeramente irregulares.
        - Sensación de novela negra / cómic adulto.
        - Minimalista y muy gráfico.
        """).strip()
    ),

    # 4) Pincel Expresionista
    (
        "Pincel Expresionista (pintura digital)",
        textwrap.dedent("""\
        Pintura digital expresionista con pinceladas visibles.
        Estilo visual:
        - Formas sugeridas más que definidas, bordes suaves.
        - Luces y sombras dramáticas de estilo cinematográfico.
        - Colores ligeramente desaturados con estallidos puntuales de color intenso.
        - Apariencia de concept art de una película.
        """).strip()
    ),

    # 5) Diorama de Papel
    (
        "Diorama de Papel (teatro de sombras)",
        textwrap.dedent("""\
        Ilustración estilo diorama de papel recortado.
        Estilo visual:
        - Planos superpuestos como capas de cartulina.
        - Sombras proyectadas para dar profundidad.
        - Personajes y objetos con bordes nítidos tipo recorte.
        - Iluminación lateral o contraluz, aspecto artesanal teatral.
        """).strip()
    ),

    # ▼ NUEVOS ESTILOS ▼

    # 6) Anime Nocturno
    (
        "Anime Nocturno (línea + cel shading)",
        textwrap.dedent("""\
        Ilustración con estética anime japonesa contemporánea.
        Estilo visual:
        - Dibujo de contorno claro (línea limpia) y cel shading en 2–3 niveles.
        - Proporciones estilizadas, ojos expresivos, gestos claros.
        - Colores planos con sombras definidas; brillos de lluvia y neón.
        - Fondo con perspectiva profunda y niebla azulada.
        - Evita textura pictórica; evita pinceladas sueltas; evita realismo fotográfico.
        """).strip()
    ),

    # 7) Ghibli Melancólico
    (
        "Ghibli Melancólico (acuarela suave)",
        textwrap.dedent("""\
        Ilustración inspirada en estudios Ghibli.
        Estilo visual:
        - Colores suaves, aspecto de acuarela; contornos discretos.
        - Luz cálida envolvente, atmósfera de nostalgia y calma.
        - Detalles naturales (hojas, viento, lluvia delicada) integrados en la escena.
        - Siluetas redondeadas, formas amables y composición contemplativa.
        - Evita texturas agresivas y contrastes extremos; evita noir duro.
        """).strip()
    ),

    # 8) Pixar Cinemático
    (
        "Pixar Cinemático (3D suave)",
        textwrap.dedent("""\
        Ilustración con look de animación tipo Pixar.
        Estilo visual:
        - Volúmenes suaves y materiales limpios; sensación 3D con iluminación global suave.
        - Luces volumétricas; reflejos sutiles en suelo mojado.
        - Personajes con proporciones caricaturizadas y expresividad clara.
        - Paleta viva pero controlada: fríos nocturnos con un acento cálido.
        - Evita grano fílmico y brochazos; evita blanco y negro.
        """).strip()
    ),
    
    # 9) Pixel Art
    (
        "Pixel Noir (8-bit, 16x16 tiles)",
        textwrap.dedent("""\
        Ilustración estilo pixel art retro.
        Requisitos de estilo:
        - Dibuja con píxeles grandes y visiblemente cuadriculados (grid perceptible).
        - Paleta limitada de 16–32 colores; evita degradados suaves y efectos de aerógrafo.
        - Sombreado con dithering (patrones de píxel) y rampas de color cortas.
        - Contornos negros de 1–2 px en personajes/objetos; evita antialiasing.
        - Bloques y detalles sugeridos (no realistas); estética de juego 16-bit.
        - Composición clara y legible en baja resolución (pensada para tiles 16x16).
        - Evita pinceladas pictóricas, grano fílmico y desenfoques; usa píxel duro.
        """).strip()
    ),

    # 10) Pixel Art Isometrico  
    (
        "Pixel Art Isométrico RPG (16×16 tiles)",
        textwrap.dedent("""\
        Ilustración en estilo pixel art isométrico (3/4 view) como un RPG clásico.
        Requisitos estrictos:
        - Cámara elevada en 3/4 isométrico; líneas paralelas ~30–35°; horizonte alto.
        - Paleta limitada (24–48 colores); evita gradientes suaves y anti-aliasing.
        - Píxel grueso y visible; contornos oscuros; bloques de color planos.
        - Sombreado por bloques y dithering retro; luces y sombras diagonales consistentes.
        - Suelo y elementos en tiles 16×16 (adoquines, bordes, esquinas); sensación “tileable”.
        - Personaje y objetos alineados a la rejilla; proporciones tipo sprite (chunky).
        - Fondo con capas (parallax simple) y siluetas simplificadas de edificios.
        - Evita brochazos pictóricos, blur, glow excesivo y realismo fotográfico.
        - Aspecto de mockup de RPG táctico/aventura isométrica.
        """).strip()
    ),
    
    
]


# Tamaños válidos para GPT Image 1 Mini
SIZE_PRESETS = [
    ("square_1024",    "1024x1024"),
    ("portrait_2x3",   "1024x1536"),  # vertical (recomendado para redes)
    ("landscape_3x2",  "1536x1024"),  # horizontal
]

DEFAULT_MODEL = "gpt-image-1-mini"
DEFAULT_QUALITY = "medium"
DEFAULT_VARIATIONS = 1
OUTPUT_ROOT = "out"


# =========================
# FUNCIONES DE UTILIDAD
# =========================
def pixelize_image(path: pathlib.Path, small_edge: int = 256):
    """
    Hace un downscale fuerte y luego upscale con NEAREST para aumentar el tamaño de píxel.
    small_edge = tamaño (en píxeles) del lado pequeño tras el downscale.
    """
    try:
        im = Image.open(path).convert("RGBA")
        w, h = im.size
        # Calcula nueva resolución proporcional con el lado corto = small_edge
        if w <= 0 or h <= 0:
            return
        if w < h:
            new_w = small_edge
            new_h = int(h * (small_edge / w))
        else:
            new_h = small_edge
            new_w = int(w * (small_edge / h))

        # Downscale (BILINEAR para llegar rápido), luego upscale (NEAREST)
        small = im.resize((max(1, new_w), max(1, new_h)), Image.BILINEAR)
        up = small.resize((w, h), Image.NEAREST)

        # Opcional: ligero posterize/quantize para reforzar paleta limitada
        try:
            up = up.convert("P", palette=Image.ADAPTIVE, colors=48).convert("RGBA")
        except Exception:
            pass

        up.save(path)
    except Exception as e:
        print(f"  (postproceso pixelize falló: {e})")


def ask_scene_text():
    print("\nDescribe la escena que quieres ilustrar:")
    scene = input("> ").strip()
    if not scene:
        scene = ("Un callejón lluvioso a medianoche; una farola rompe la niebla. "
                 "Un cuervo observa desde una barandilla mientras una figura se aleja.")
    return scene


def ask_transparent_bg():
    print("\n¿Quieres fondo transparente? (y/N):")
    ans = input("> ").strip().lower()
    return ans == "y"


def list_styles():
    print("\n=== ESTILOS DISPONIBLES ===")
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
    print("\n=== FORMATOS DISPONIBLES ===")
    print("1. Cuadrado (1024x1024)")
    print("2. Vertical (1024x1536)")
    print("3. Horizontal (1536x1024)")
    print("4. Todos los formatos")
    raw = input("> ").strip()
    if raw == "1":
        return [SIZE_PRESETS[0]]
    elif raw == "2":
        return [SIZE_PRESETS[1]]
    elif raw == "3":
        return [SIZE_PRESETS[2]]
    else:
        return SIZE_PRESETS


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


def save_png(b64_png: str, path: pathlib.Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(b64_png))


# =========================
# PROGRAMA PRINCIPAL
# =========================

def main():
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("❌ No se encontró OPENAI_API_KEY en .env")
        print("Ejemplo de .env:\nOPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx")
        return

    client = OpenAI(api_key=api_key)

    chosen_style_ids = list_styles()
    scene_text = ask_scene_text()
    transparent = ask_transparent_bg()
    chosen_formats = list_formats()

    print("\n¿Cuántas variaciones por estilo/tamaño quieres generar? (Enter = 1)")
    raw_n = input("> ").strip()
    n_variations = int(raw_n) if raw_n.isdigit() and int(raw_n) > 0 else DEFAULT_VARIATIONS

    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_root = pathlib.Path(OUTPUT_ROOT)

    print("\n🎨 Generando imágenes... puede tardar unos minutos.\n")

    for style_idx in chosen_style_ids:
        style_name, style_block = STYLE_PRESETS[style_idx]
        style_slug = slugify(style_name)

        for size_tag, size_val in chosen_formats:
            prompt = build_prompt(style_block, scene_text)

            for v in range(n_variations):
                try:
                    kwargs = {
                        "model": DEFAULT_MODEL,
                        "prompt": prompt,
                        "size": size_val,
                        "quality": DEFAULT_QUALITY,
                        "n": 1
                    }
                    if transparent:
                        kwargs["background"] = "transparent"

                    # Generación de imagen
                    resp = client.images.generate(**kwargs)
                    b64 = resp.data[0].b64_json

                    # Guardado
                    filename = f"{timestamp}_{style_slug}_{size_tag}_v{v+1}.png"
                    out_path = out_root / style_slug / size_tag / filename
                    save_png(b64, out_path)
                    print(f"✔ {out_path}")

                    # --- POSTPROCESO para el estilo Pixel Art ---
                    if "pixel-art" in style_slug or "pixel" in style_slug:
                        pixelize_image(out_path, small_edge=256)
                        print("  ↳ postproceso: pixelize aplicado (downscale + NEAREST)")

                except Exception as e:
                    print(f"✖ Error con estilo '{style_name}', tamaño '{size_tag}', variación {v+1}:\n  {e}")

    print("\n✅ Listo. Todas las imágenes están en:", out_root.resolve())


if __name__ == "__main__":
    main()

