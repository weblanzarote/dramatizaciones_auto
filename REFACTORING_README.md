# Reestructuración del Proyecto - Documentación

## 📋 Resumen

Este proyecto ha sido reestructurado para mejorar la mantenibilidad, modularidad y facilidad de desarrollo. Los archivos monolíticos originales (`create_project.py` y `generate_audiovideo_from_txt_drama.py`) han sido divididos en módulos especializados dentro del directorio `src/`.

## 🗂️ Nueva Estructura

```
proyecto_video_ia/
│
├── .env                     # Tus claves de API
├── main_generator.py        # ✨ Punto de entrada para crear historias
├── main_renderer.py         # ✨ Punto de entrada para hacer el vídeo
├── requirements.txt         # Dependencias
│
├── create_project.py        # 📦 ARCHIVO ORIGINAL (conservado por compatibilidad)
├── generate_audiovideo_from_txt_drama.py  # 📦 ARCHIVO ORIGINAL
│
└── src/                     # 🎯 Código fuente modular
    ├── __init__.py
    │
    ├── config/              # Configuraciones y Constantes
    │   ├── __init__.py
    │   ├── settings.py      # Carga .env, claves API, constantes
    │   ├── styles.py        # Presets de estilos (Gemini/Qwen)
    │   └── voices.py        # Mapa de voces de ElevenLabs
    │
    ├── services/            # Clientes de APIs (infraestructura)
    │   ├── __init__.py
    │   ├── openai_service.py    # Wrapper para GPT-5.1
    │   ├── gemini_service.py    # Wrapper para Google GenAI
    │   ├── runware_service.py   # Wrapper para Runware
    │   └── elevenlabs_service.py # Wrapper para TTS
    │
    ├── content/             # Lógica de guion e ideas
    │   ├── __init__.py
    │   ├── ideation.py      # Generar ideas, nombres de proyecto
    │   └── scripting.py     # Generar guion, prompts visuales
    │
    ├── media/               # Procesamiento de assets
    │   ├── __init__.py
    │   ├── image_proc.py    # Pixelize, resize, parse_color
    │   └── audio_proc.py    # Pydub, mezclas
    │
    └── video/               # Edición de vídeo
        ├── __init__.py
        ├── parser.py        # Parsear formato de guion [SPEAKER]
        ├── composition.py   # MoviePy, Ken Burns, montaje
        └── subtitles.py     # Generación de .srt y .ass
```

## 🚀 Uso Completo

### Generar un proyecto (historias + imágenes)

```bash
# 1. Modo interactivo básico
python main_generator.py --idea "Un detective encuentra un espejo maldito"

# 2. Generar idea automáticamente
python main_generator.py --auto-idea

# 3. Dry-run (solo genera guiones, no imágenes)
python main_generator.py --auto-idea --dry-run

# 4. Con opciones avanzadas
python main_generator.py \
    --auto-idea \
    --output ./MisProyectos \
    --overwrite  # Sobrescribe imágenes existentes

# Resultado:
# ./MisProyectos/Nombre_Del_Proyecto/
#   ├── script.txt           # Guion con etiquetas [SPEAKER] e [imagen:X.png]
#   ├── social_post.txt      # Post para redes sociales
#   ├── visual_prompts.json  # Prompts visuales generados
#   ├── brief.txt            # Brief de consistencia visual
#   ├── metadata.json        # Metadata del proyecto
#   └── images/              # Imágenes generadas
#       ├── 1.png
#       ├── 2.png
#       └── ...
```

### Renderizar video (audio + video)

```bash
# 1. Generar audios y video completo
python main_renderer.py ./MisProyectos/Mi_Historia/script.txt \
    --outdir ./Out/Mi_Historia \
    --images-dir ./MisProyectos/Mi_Historia/images \
    --video-out ./Out/Mi_Historia/video.mp4

# 2. Con efecto Ken Burns y música
python main_renderer.py script.txt \
    --outdir ./Out \
    --images-dir ./images \
    --video-out ./video_final.mp4 \
    --kenburns in \              # Zoom in suave
    --kb-zoom 0.15 \             # 15% de zoom
    --kb-sticky \                # No reinicia Ken Burns en misma imagen
    --music-audio \              # Activa música de fondo
    --music-audio-vol 0.15       # Volumen de música al 15%

# 3. Resolución vertical (TikTok/Reels) 9:16
python main_renderer.py script.txt \
    --video-out ./vertical.mp4 \
    --resolution 1080x1920 \     # Vertical
    --fit cover \                # Recorta para llenar
    --kenburns out \             # Zoom out
    --kb-pan random              # Paneo aleatorio

# 4. Solo generar audios (sin video)
python main_renderer.py script.txt \
    --outdir ./Out/MiProyecto

# 5. Dry-run (simular sin generar archivos)
python main_renderer.py script.txt --dry-run

# Resultado:
# ./Out/Mi_Historia/
#   ├── audio/               # Audios individuales
#   │   ├── 001_NARRADOR_*.mp3
#   │   ├── 002_HOMBRE30_*.mp3
#   │   └── ...
#   ├── manifest.json        # Metadata de bloques
#   └── video.mp4            # Video final (si se especificó --video-out)
```

### Opciones avanzadas de renderizado

```bash
# Ken Burns completo
--kenburns {none,in,out}    # Tipo de efecto
--kb-zoom 0.10              # Cantidad de zoom (10% por defecto)
--kb-pan {center,tl2br,tr2bl,bl2tr,br2tl,random}  # Dirección
--kb-sticky                 # No reinicia en imágenes consecutivas

# Ajuste visual
--fit {contain,cover}       # contain=letterbox, cover=recorta
--bg-color "#000000"        # Color de fondo
--pad-ms 200                # Padding al final de cada clip (ms)

# Audio
--music-audio               # Activa música (./images/musica.mp3)
--music-audio-vol 0.2       # Volumen de música
--media-keep-audio          # Mantiene audio de videos fuente
--media-audio-vol 0.2       # Volumen de audio de videos

# Video
--resolution 1920x1080      # Resolución (WxH)
--fps 30                    # Frames por segundo
```

## 📦 Módulos

### `src/config/`
- **settings.py**: Configuración central, carga de variables de entorno, validación de API keys
- **styles.py**: Presets de estilos visuales para Gemini y Qwen
- **voices.py**: Mapeo de voces de ElevenLabs para cada personaje

### `src/services/`
Wrappers para APIs externas:
- **openai_service.py**: Cliente de OpenAI (GPT-5.1)
- **gemini_service.py**: Cliente de Google Gemini (generación de imágenes)
- **runware_service.py**: Cliente de Runware (imágenes y animación)
- **elevenlabs_service.py**: Cliente de ElevenLabs (text-to-speech)

### `src/content/`
Lógica de generación de contenido:
- **ideation.py**: Generación de ideas y nombres de proyectos
- **scripting.py**: Generación de guiones y prompts visuales

### `src/media/`
Procesamiento de archivos multimedia:
- **image_proc.py**: Procesamiento de imágenes (pixelado, colores)
- **audio_proc.py**: Procesamiento de audio (concatenación, mezcla)

### `src/video/`
Edición y composición de video:
- **parser.py**: Parsing de scripts con etiquetas `[SPEAKER]` e `[imagen:X.png]`
- **composition.py**: Composición de video con MoviePy, efectos Ken Burns
- **subtitles.py**: Generación de subtítulos SRT y ASS

## ⚙️ Configuración

El archivo `.env` debe contener:

```env
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
ELEVENLABS_API_KEY=...
RUNWARE_API_KEY=...  # Opcional
```

## ✅ Estado de las Funcionalidades

### Completadas
1. ✅ **Generación de imágenes con Gemini** (`src/services/gemini_service.py`)
   - Lógica completa de consistencia visual
   - Manejo de brief de protagonista
   - Clasificación automática de elementos visuales
   - Detección de protagonista con marcador [PROTAGONISTA]
   - Reintentos y manejo de prompts bloqueados
   - **Archivo**: `src/content/consistency.py` (240 líneas)

2. ✅ **Composición completa de video** (`src/video/renderer.py`)
   - Integración completa de clips con Ken Burns
   - Manejo de bloque [CIERRE]
   - Música de fondo con control de volumen
   - Soporte para imágenes y videos
   - Generación de subtítulos SRT y ASS
   - **Archivo**: `src/video/renderer.py` (240 líneas)

3. ✅ **Main scripts completamente funcionales**
   - `main_generator.py`: Genera historias completas con imágenes
   - `main_renderer.py`: Renderiza videos con todas las opciones

### Opcional
- 🟡 **Generación con Runware** (`src/services/runware_service.py`)
   - Estructura base creada
   - Requiere completar integración async si se desea usar
   - Ver `create_project.py` líneas 1117-1698 para referencia

## 🎯 Ventajas de la Nueva Estructura

### Antes
- ❌ Archivos de >2000 líneas
- ❌ Difícil de mantener
- ❌ Difícil de testear
- ❌ Código duplicado

### Ahora
- ✅ Módulos pequeños y especializados
- ✅ Fácil de entender y modificar
- ✅ Fácil de testear unitariamente
- ✅ Código reutilizable
- ✅ Separación clara de responsabilidades

## 📝 Notas Importantes

1. **Compatibilidad**: Los archivos originales `create_project.py` y `generate_audiovideo_from_txt_drama.py` se conservan por compatibilidad. Puedes seguir usándolos si lo necesitas.

2. **Trabajo en progreso**: Esta es una refactorización inicial. Las funcionalidades más complejas (generación de imágenes, composición de video) requieren completarse usando el código original como referencia.

3. **Imports**: Todos los módulos en `src/` usan imports relativos (`.config`, `.services`, etc.). Los archivos `main_*.py` usan imports absolutos (`src.config`, `src.services`, etc.).

## 🤝 Contribuir

Para añadir funcionalidad:

1. Identifica el módulo apropiado en `src/`
2. Añade la función/clase en ese módulo
3. Actualiza `main_generator.py` o `main_renderer.py` si es necesario
4. Documenta los cambios

## 📚 Referencias

- Archivo original `create_project.py`: 2148 líneas
- Archivo original `generate_audiovideo_from_txt_drama.py`: 1107 líneas
- Total refactorizado: ~20 módulos especializados
