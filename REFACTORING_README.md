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

## 🚀 Uso

### Generar un proyecto (historias + imágenes)

```bash
# Modo interactivo
python main_generator.py --idea "Un detective encuentra un espejo maldito"

# Generar idea automáticamente
python main_generator.py --auto-idea

# Dry-run (solo genera guiones, no imágenes)
python main_generator.py --auto-idea --dry-run
```

### Renderizar video (audio + video)

```bash
# Generar audios y video
python main_renderer.py script.txt \
    --outdir ./Out/MiProyecto \
    --images-dir ./images \
    --video-out ./Out/MiProyecto/video.mp4

# Solo generar audios (sin video)
python main_renderer.py script.txt --outdir ./Out/MiProyecto

# Dry-run (simular sin generar archivos)
python main_renderer.py script.txt --dry-run
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

## 🔧 Tareas Pendientes

La refactorización ha creado una estructura base sólida, pero algunas funcionalidades complejas requieren completarse:

### Alta Prioridad
1. **Generación de imágenes con Gemini** (`src/services/gemini_service.py`)
   - Lógica de consistencia visual
   - Manejo de brief de protagonista
   - Ver `create_project.py` líneas 926-1358

2. **Composición completa de video** (`src/video/composition.py`)
   - Integración completa de clips
   - Manejo de cierre
   - Música de fondo
   - Ver `generate_audiovideo_from_txt_drama.py` líneas 654-1104

3. **Generación de imágenes con Runware** (`src/services/runware_service.py`)
   - Implementación async
   - Animación de imágenes
   - Ver `create_project.py` líneas 1359-1698

### Media Prioridad
- Menús interactivos (selección de modelo, estilo)
- Generación de subtítulos avanzada (typing effect)
- Integración de música de fondo

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
