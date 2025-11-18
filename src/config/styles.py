import textwrap

"""
Presets de estilos visuales para generación de imágenes.
Incluye estilos para Gemini (detallados) y Qwen (concisos).
"""

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
