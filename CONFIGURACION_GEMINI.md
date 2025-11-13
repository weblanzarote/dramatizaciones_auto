# 🎨 Configuración de Google Gemini para Generación de Imágenes

## ✅ Cambios Realizados

Tu proyecto ahora usa **Google Gemini 2.5 Flash Image** en lugar de OpenAI para la generación de imágenes.

### Beneficios principales:
- ✨ **Consistencia de personajes**: Los personajes mantienen la misma apariencia en todas las escenas
- 🎭 **Coherencia visual**: Estilo artístico consistente a lo largo de todo el video
- 💰 **Mejor costo-beneficio**: Precio similar pero mejor calidad de consistencia

---

## 🚀 Pasos para Configurar

### 1. Obtener tu API Key de Google AI Studio

Es **MUY SIMPLE** (ya no necesitas Google Cloud Console):

1. Ve a: **https://aistudio.google.com**
2. Inicia sesión con tu cuenta de Google
3. Haz clic en el botón **"Get API Key"** (panel izquierdo)
4. Haz clic en **"Create API Key"**
5. Copia la key que te genera

**¡Eso es todo!** No necesitas:
- ❌ Configurar Google Cloud Console
- ❌ Crear proyectos manualmente
- ❌ Configurar billing (tiene límite gratuito)
- ❌ Entender IAM o service accounts

---

### 2. Configurar tu archivo .env

Copia `.env.example` a `.env` si aún no lo has hecho:

```bash
cp .env.example .env
```

Luego edita `.env` y añade tu key:

```bash
# OpenAI API Key (para generación de texto)
OPENAI_API_KEY=sk-tu-key-de-openai

# Google Gemini API Key (para generación de imágenes)
GEMINI_API_KEY=tu-api-key-de-gemini-aqui

# Replicate (opcional, solo para --animate-images)
REPLICATE_API_TOKEN=tu-token-de-replicate
```

---

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

Esto instalará `google-genai` junto con todas las demás dependencias.

---

## 🎬 Usar el Proyecto

**El uso es IDÉNTICO a antes:**

```bash
# Modo automático (genera idea y nombre automáticamente)
python create_project.py

# Modo manual
python create_project.py --idea "Tu idea aquí" --project-name "205_NOMBRE"

# Con animación de imágenes
python create_project.py --animate-images
```

---

## 🧠 Cómo Funciona la Consistencia

### Primera imagen (escena 1):
- Establece el estilo visual base
- Define los personajes principales
- Crea la paleta de colores
- Establece el tono artístico

### Imágenes siguientes (escenas 2-10):
- **Automáticamente mantienen**:
  - Los mismos personajes (apariencia, ropa, rasgos faciales)
  - El mismo estilo artístico
  - La misma paleta de colores
  - La misma atmósfera visual

### Instrucción interna:
```
"MANTÉN EXACTAMENTE EL MISMO ESTILO VISUAL Y LOS MISMOS PERSONAJES
que en las imágenes anteriores."
```

Gemini está diseñado para entender y mantener esta consistencia de forma nativa.

---

## 💰 Costos Estimados

| Proveedor | Modelo Anterior | Modelo Nuevo |
|-----------|----------------|--------------|
| **OpenAI** | gpt-image-1-mini: ~$0.11 por proyecto | - |
| **Google Gemini** | - | ~$0.15-0.30 por proyecto* |

*Precios pueden variar, consulta en Google AI Studio

**Ventaja:** Por un costo similar o ligeramente superior, obtienes **mucha mejor consistencia visual**.

---

## 🔧 Solución de Problemas

### Error: "No se encontró la GEMINI_API_KEY"
- ✅ Verifica que `.env` existe (no `.env.example`)
- ✅ Verifica que la línea sea: `GEMINI_API_KEY=tu-key-aqui` (sin espacios alrededor del `=`)
- ✅ Verifica que tu key esté correctamente copiada de AI Studio

### Error: "Error al inicializar el cliente de Gemini"
- ✅ Verifica que instalaste las dependencias: `pip install -r requirements.txt`
- ✅ Verifica tu conexión a internet
- ✅ Verifica que tu API key sea válida en https://aistudio.google.com

### Las imágenes no mantienen consistencia
- ℹ️ La primera imagen establece el "estilo base". Si la regeneras con `--overwrite-images`, todas las siguientes cambiarán
- ℹ️ Para mejores resultados, usa estilos visuales que favorezcan personajes definidos (evita "Sombras de Gaia" si quieres rostros consistentes)

---

## 📊 Comparación: Antes vs Ahora

| Aspecto | OpenAI (antes) | Google Gemini (ahora) |
|---------|----------------|----------------------|
| **Consistencia de personajes** | ❌ Baja | ✅ Alta |
| **Consistencia de estilo** | ⚠️ Moderada | ✅ Alta |
| **Calidad de imagen** | ✅ Buena | ✅ Buena |
| **Costo por proyecto** | $0.11 | ~$0.20 |
| **Configuración** | Simple | **Más simple** |

---

## 🆘 ¿Necesitas Ayuda?

Si tienes problemas:
1. Revisa que `.env` tenga las 3 keys configuradas
2. Verifica que `pip install -r requirements.txt` funcionó sin errores
3. Prueba con una idea simple primero para verificar que todo funciona

---

## ✨ Próximos Pasos

1. Configura tu `GEMINI_API_KEY` en `.env`
2. Ejecuta `pip install -r requirements.txt`
3. Prueba con: `python create_project.py`
4. ¡Disfruta de videos con personajes consistentes! 🎉
