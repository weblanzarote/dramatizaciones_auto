"""
Procesamiento de imágenes: pixelización, resize, conversiones de color.
"""
from PIL import Image


def pixelize_image(path: str, small_edge: int = 256):
    """
    Aplica efecto de pixelado estilo retro a una imagen.

    Downscale fuerte y upscale con NEAREST para píxel gordo retro.
    Ajusta small_edge: 256 (suave), 192/160/128 (más "chunky").

    Args:
        path: Ruta a la imagen
        small_edge: Tamaño del borde pequeño para el downscale
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


def parse_color(value):
    """
    Parsea un valor de color en formato hex, nombre o tupla RGB.

    Args:
        value: Color como "#rrggbb", "white"/"black", o tupla/lista (r,g,b)

    Returns:
        Tupla (r, g, b) o string del color
    """
    if isinstance(value, (tuple, list)) and len(value) == 3:
        return tuple(int(v) for v in value)

    if isinstance(value, str):
        s = value.strip()
        if s.startswith("#") and len(s) == 7:
            r = int(s[1:3], 16)
            g = int(s[3:5], 16)
            b = int(s[5:7], 16)
            return (r, g, b)
        # Como fallback, intenta nombres ("black", "white") si tu versión lo soporta
        return s

    return (0, 0, 0)
