# Dramatizaciones Auto - Relatos Extraordinarios

Sistema automatizado de generación de contenido viral para la cuenta 'Relatos Extraordinarios'.

## 🚀 Características

- Generación automática de guiones, imágenes y videos
- Análisis de proyectos virales anteriores
- Modo automático con IA para generar ideas virales
- Integración con OpenAI (GPT-4o-mini, DALL-E, GPT Image)
- Sistema de retry automático para imágenes bloqueadas

## 📋 Requisitos

- Python 3.8+
- OpenAI API Key configurada en `.env`
- PowerShell (para generación de video)
- Dependencias: `pip install -r requirements.txt` (si existe)

## 🎯 Uso

### Modo Automático (NUEVO) ⚡

El modo automático analiza todos los proyectos anteriores, identifica los virales, y genera automáticamente:
- Una nueva idea basada en patrones virales
- Un nombre de proyecto apropiado
- La numeración correcta del proyecto

```bash
python create_project.py
```

El script automáticamente:
1. ✅ Ejecuta `crear_indice_proyectos.py` para actualizar el índice
2. 🧠 Analiza proyectos VIRALES (_v) y MEDIO VIRALES (_mv)
3. 💡 Genera una nueva idea con alto potencial viral
4. 📈 Determina el siguiente número de proyecto
5. 🏷️ Genera un nombre descriptivo para el proyecto
6. 🎬 Ejecuta todo el flujo de generación de video

### Modo Manual (Original)

Si prefieres proporcionar tu propia idea:

```bash
python create_project.py --idea "Tu idea aquí" --project-name "205_NOMBREPROYECTO"
```

### Opciones Adicionales

```bash
# Regenerar imágenes aunque ya existan
python create_project.py --overwrite-images

# Regenerar video aunque ya exista
python create_project.py --force-video

# Especificar modelo de imagen
python create_project.py --image-model dall-e-3 --image-quality hd

# Modo automático con opciones específicas
python create_project.py --image-model gpt-image-1-mini --image-quality medium
```

## 📊 Gestión de Proyectos

### Marcar Proyectos como Virales

Para que el sistema aprenda de tus proyectos exitosos, añade sufijos a las carpetas:

- `_v` - Proyecto VIRAL (ejemplo: `67_METROMADRID_v`)
- `_mv` - Proyecto MEDIO VIRAL (ejemplo: `23_ELPAN_mv`)

### Actualizar Índice Manualmente

```bash
python crear_indice_proyectos.py
```

Esto genera/actualiza `_master_project_list.txt` con todos los proyectos y sus estadísticas.

## 🎨 Modelos de Imagen Disponibles

1. **GPT Image 1 Mini - Calidad BAJA** ($0.06/10 imgs)
2. **GPT Image 1 Mini - Calidad MEDIA** ($0.15/10 imgs) ⭐ RECOMENDADO
3. **GPT Image 1 - Calidad MEDIA** ($0.63/10 imgs)
4. **GPT Image 1 - Calidad ALTA** ($2.50/10 imgs)
5. **DALL-E 2 - Standard** ($0.20/10 imgs)
6. **DALL-E 3 - Standard** ($0.80/10 imgs)
7. **DALL-E 3 - HD** ($1.20/10 imgs)

## 📁 Estructura de Proyecto

Cada proyecto genera:
```
205_NOMBREPROYECTO/
├── images/           # Imágenes generadas (PNG)
│   ├── 1.png
│   ├── 2.png
│   └── ...
├── Out/              # Video final
│   └── video.mp4
├── texto.txt         # Guion del video
├── redes.txt         # Post para redes sociales
├── musica.mp3        # Música de fondo
└── cierre.mp4        # Video de cierre
```

## 🔧 Configuración

Crea un archivo `.env` en el directorio raíz:

```env
OPENAI_API_KEY=tu_clave_api_aqui
```

## 💡 Ejemplos de Proyectos Virales

El sistema aprende de estos patrones:
- 🔥 Leyendas urbanas españolas (Metro Madrid, Palacio Linares)
- 🏚️ Lugares abandonados (La Mussara, Aldea Abuín)
- 👻 Historias paranormales (Poltergeist Asturias, Tirso de Molina)
- 🎭 Misterios históricos (Hombre Pez, Milagro Calanda)

## 🚨 Solución de Problemas

### Error: "No se encontró la OPENAI_API_KEY"
- Verifica que el archivo `.env` existe y contiene la clave correcta

### Error al generar imágenes
- El sistema reintenta automáticamente hasta 5 veces
- Los prompts bloqueados se reescriben automáticamente

### Error al ejecutar run.ps1
- Verifica que PowerShell está disponible
- Asegúrate de que `run.ps1` existe en el directorio raíz

## 📈 Estadísticas Actuales

- Total de proyectos: 189
- Proyectos virales: 11
- Proyectos medio virales: 23
- Tasa de éxito viral: ~18%

## 🎓 Aprendizaje Continuo

El sistema mejora automáticamente:
1. Cada proyecto marcado como viral/medio-viral alimenta el análisis
2. La IA identifica patrones de éxito
3. Las nuevas ideas se generan basándose en estos patrones
4. El ciclo se repite mejorando la tasa de viralidad

---

**¡Disfruta creando contenido viral! 🚀**
