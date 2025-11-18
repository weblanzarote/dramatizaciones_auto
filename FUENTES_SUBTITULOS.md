# Configuración de Fuentes para Subtítulos

## 📝 Fuente por Defecto: BebasNeue-Regular

La versión modular está configurada para usar **BebasNeue-Regular** como fuente predeterminada para subtítulos ASS.

## 📁 Ubicación de las Fuentes

### Opción 1: Carpeta Fonts en el Proyecto (Recomendado)

Crea una carpeta `Fonts/` en la raíz del proyecto y coloca ahí tus archivos `.ttf`:

```
dramatizaciones_auto/
├── Fonts/
│   ├── BebasNeue-Regular.ttf
│   ├── Arial.ttf
│   └── ... otras fuentes
├── main_generator.py
├── main_renderer.py
└── src/
```

### Opción 2: Fuentes del Sistema

También puedes usar fuentes instaladas en tu sistema operativo:
- **Linux**: `/usr/share/fonts/` o `~/.fonts/`
- **Windows**: `C:\Windows\Fonts\`
- **macOS**: `/Library/Fonts/` o `~/Library/Fonts/`

## 🚀 Uso con main_renderer.py

### Usar BebasNeue-Regular (predeterminado)

```bash
python main_renderer.py ./output/Proyecto/script.txt \
    --video-out ./video.mp4 \
    --ass-typing-out ./subtitles.ass
```

### Usar otra fuente

```bash
python main_renderer.py ./output/Proyecto/script.txt \
    --video-out ./video.mp4 \
    --ass-typing-out ./subtitles.ass \
    --ass-font "Arial"
```

### Usar archivo .ttf específico con ruta completa

```bash
python main_renderer.py ./output/Proyecto/script.txt \
    --video-out ./video.mp4 \
    --ass-typing-out ./subtitles.ass \
    --ass-font "./Fonts/BebasNeue-Regular.ttf"
```

## ⚙️ Argumentos de Subtítulos Disponibles

### Subtítulos SRT (básicos)

```bash
--subs-out RUTA            # Genera archivo SRT
--subs-with-speaker        # Incluye nombre del speaker
--subs-font FUENTE         # Fuente (default: Arial)
--subs-fontsize 7.0        # Tamaño de fuente
--subs-margin-v 100        # Margen inferior en pixels
--subs-outline 2           # Grosor del contorno
--subs-shadow 1            # Sombra
--subs-uppercase           # Convierte a MAYÚSCULAS
```

### Subtítulos ASS (con efectos)

```bash
--ass-typing-out RUTA      # Genera archivo ASS con efectos
--ass-font FUENTE          # Fuente (default: BebasNeue-Regular)
--ass-fontsize 48          # Tamaño de fuente ASS
--ass-margin-v 80          # Margen inferior en pixels
--ass-outline 2            # Grosor del contorno
--ass-shadow 1             # Sombra
--ass-style-name Typing    # Nombre del estilo ASS
--subs-typing              # Activa efecto typing
--subs-word-timing length  # Timing por longitud de palabra
--subs-min-seg-ms 60       # Duración mínima por segmento (ms)
```

## 📖 Ejemplos Completos

### 1. Video con subtítulos ASS usando BebasNeue

```bash
python main_renderer.py ./output/MiProyecto/script.txt \
    --outdir ./Out \
    --images-dir ./output/MiProyecto/images \
    --video-out ./video.mp4 \
    --kenburns in \
    --kb-sticky \
    --music-audio \
    --ass-typing-out ./subtitles.ass \
    --subs-typing \
    --ass-font "BebasNeue-Regular" \
    --ass-fontsize 52 \
    --ass-margin-v 100
```

### 2. Video con subtítulos SRT simples

```bash
python main_renderer.py ./output/MiProyecto/script.txt \
    --video-out ./video.mp4 \
    --subs-out ./subtitles.srt \
    --subs-with-speaker \
    --subs-uppercase
```

### 3. Video con subtítulos usando fuente del sistema

```bash
python main_renderer.py ./output/MiProyecto/script.txt \
    --video-out ./video.mp4 \
    --ass-typing-out ./subtitles.ass \
    --ass-font "Impact" \
    --ass-fontsize 56
```

## 🔧 Verificar Fuentes Disponibles

### Linux (usando fc-list)

```bash
fc-list | grep -i bebas
fc-list | grep -i arial
```

### Listar fuentes en carpeta Fonts/

```bash
ls -la Fonts/
```

## ⚠️ Notas Importantes

1. **Nombre vs Ruta**: Puedes usar el nombre de la fuente ("BebasNeue-Regular") si está instalada en el sistema, o la ruta completa al archivo .ttf ("./Fonts/BebasNeue-Regular.ttf")

2. **Extensión del archivo**: El nombre de la fuente en el archivo ASS no necesita la extensión .ttf. MoviePy/libass la busca automáticamente.

3. **Compatibilidad**: Los archivos ASS con fuentes personalizadas funcionan en cualquier reproductor que soporte ASS (VLC, MPV, etc.)

4. **Fuentes incluidas en video**: Si quieres que la fuente se vea igual en todos los sistemas, necesitas "quemar" los subtítulos en el video (burn-in), no usar soft-subs.

## 📦 Descargar BebasNeue

Si no tienes la fuente BebasNeue, puedes descargarla de:
- Google Fonts: https://fonts.google.com/specimen/Bebas+Neue
- GitHub: https://github.com/dharmatype/Bebas-Neue

Descarga el archivo `BebasNeue-Regular.ttf` y colócalo en la carpeta `Fonts/` del proyecto.

## 🆘 Solución de Problemas

### Error: "Fuente no encontrada"

1. Verifica que el archivo .ttf existe en `Fonts/`
2. Prueba usar la ruta completa: `--ass-font "./Fonts/BebasNeue-Regular.ttf"`
3. Instala la fuente en el sistema operativo

### Los subtítulos no se ven

1. Verifica que especificaste `--ass-typing-out` o `--subs-out`
2. Comprueba que el archivo ASS/SRT se generó correctamente
3. Abre el archivo .ass con un editor de texto para verificar

### La fuente se ve diferente en otros sistemas

1. Usa burn-in (quemar subtítulos en el video) en lugar de soft-subs
2. O asegúrate de que la fuente está instalada en el sistema de reproducción
