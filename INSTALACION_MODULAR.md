# Instalación - Versión Modular

Este paquete contiene la versión modular y optimizada del proyecto de dramatizaciones automáticas.

## 📦 Contenido del Paquete

### Archivos principales
- `main_generator.py` - Generador de historias e imágenes
- `main_renderer.py` - Renderizador de audio y video
- `requirements.txt` - Dependencias de Python

### Directorio src/ (módulos)
- `src/config/` - Configuraciones, estilos, voces
- `src/services/` - Servicios API (OpenAI, Gemini, Runware, ElevenLabs)
- `src/content/` - Generación de ideas, scripts, consistencia visual
- `src/media/` - Procesamiento de imágenes y audio
- `src/video/` - Parsing, composición, subtítulos, renderizado

### Documentación
- `REFACTORING_README.md` - Guía completa de uso
- `README.md` - Documentación original
- `CONFIGURACION_GEMINI.md` - Configuración de Gemini

### Assets
- `cierre.mp4` - Video de cierre
- `musica.mp3` - Música de fondo predeterminada
- `.env.example` - Plantilla para variables de entorno

## 🚀 Instalación Rápida

### 1. Extraer el paquete

**Opción A: Archivo .tar.gz**
```bash
tar -xzf dramatizaciones_auto_modular.tar.gz
cd dramatizaciones_auto_modular/
```

**Opción B: Archivo .zip**
```bash
unzip dramatizaciones_auto_modular.zip
cd dramatizaciones_auto_modular/
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

**Dependencias principales:**
- openai
- google-generativeai
- elevenlabs
- runware
- moviepy
- pillow
- pydub

### 3. Configurar API Keys

Copia el archivo de ejemplo y añade tus claves:

```bash
cp .env.example .env
```

Edita `.env` con tus claves API:

```bash
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AI...
ELEVENLABS_API_KEY=...
RUNWARE_API_KEY=...  # Opcional, solo si usas Runware
```

### 4. Verificar instalación

```bash
python main_generator.py --help
python main_renderer.py --help
```

## 📖 Uso Básico

### Generar proyecto completo con Gemini (alta calidad)

```bash
python main_generator.py --auto-idea --image-model gemini
```

### Generar proyecto con Runware/Qwen (económico)

```bash
python main_generator.py --auto-idea --image-model qwen
```

### Generar proyecto con animación

```bash
python main_generator.py --auto-idea --image-model qwen --animate
```

### Renderizar video

```bash
python main_renderer.py ./output/NombreProyecto/script.txt \
    --outdir ./Out \
    --images-dir ./output/NombreProyecto/images \
    --video-out ./video.mp4 \
    --kenburns in \
    --kb-sticky \
    --music-audio
```

## 📁 Fuentes para Subtítulos (Opcional)

Si quieres usar fuentes personalizadas (como BebasNeue-Regular) para subtítulos:

```bash
mkdir Fonts
# Copia tus archivos .ttf a esta carpeta
cp /ruta/a/BebasNeue-Regular.ttf Fonts/
```

Consulta `FUENTES_SUBTITULOS.md` para más detalles.

## 🔧 Estructura del Proyecto

```
dramatizaciones_auto_modular/
├── Fonts/               # (Opcional) Fuentes personalizadas .ttf
├── src/
│   ├── config/          # Configuraciones
│   │   ├── settings.py  # API keys, constantes
│   │   ├── voices.py    # Mapeo de voces ElevenLabs
│   │   └── styles.py    # Estilos visuales (437 líneas)
│   ├── services/        # Wrappers de APIs
│   │   ├── openai_service.py
│   │   ├── gemini_service.py
│   │   ├── runware_service.py
│   │   └── elevenlabs_service.py
│   ├── content/         # Generación de contenido
│   │   ├── ideation.py      # Generación de ideas
│   │   ├── scripting.py     # Generación de scripts
│   │   └── consistency.py   # Consistencia visual
│   ├── media/           # Procesamiento
│   │   ├── image_proc.py    # Pixelización, colores
│   │   └── audio_proc.py    # Concatenación de audio
│   └── video/           # Video
│       ├── parser.py        # Parsing de scripts
│       ├── composition.py   # Ken Burns, canvas
│       ├── subtitles.py     # SRT y ASS
│       └── renderer.py      # Renderizado completo
├── main_generator.py    # Script principal de generación
├── main_renderer.py     # Script principal de renderizado
├── requirements.txt     # Dependencias
├── .env.example         # Plantilla de configuración
└── REFACTORING_README.md # Documentación completa
```

## ✅ Ventajas de la Versión Modular

- ✅ **20+ módulos especializados** (vs 2 archivos de >2000 líneas)
- ✅ **Fácil de mantener** - Separación clara de responsabilidades
- ✅ **Fácil de extender** - Agregar nuevos servicios o efectos
- ✅ **Fácil de testear** - Módulos independientes
- ✅ **Doble motor de imágenes** - Gemini (calidad) o Runware/Qwen (económico)
- ✅ **Animación integrada** - Con Runware Seedance
- ✅ **Video completo** - MoviePy con Ken Burns, música, subtítulos

## 📚 Documentación Completa

Para más detalles sobre opciones avanzadas, consulta:
- `REFACTORING_README.md` - Guía completa con todos los argumentos
- `CONFIGURACION_GEMINI.md` - Configuración específica de Gemini

## 🆘 Soporte

Si encuentras algún problema:
1. Verifica que todas las API keys estén configuradas en `.env`
2. Verifica que todas las dependencias estén instaladas
3. Consulta `REFACTORING_README.md` para ejemplos de uso

---

**Versión:** Modular v1.0
**Última actualización:** 2025-11-18
