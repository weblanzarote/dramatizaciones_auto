import os
import shutil
import time
import sys
import base64
from dotenv import load_dotenv
import subprocess
import argparse
import json
import re
import requests
from PIL import Image
from openai import OpenAI
import openai

# --- CONFIGURACIÓN INICIAL ---
# Cargar claves de API de forma segura desde el archivo .env
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("No se encontró la OPENAI_API_KEY. Asegúrate de que tu archivo .env está configurado.")

# Inicializamos el cliente de OpenAI que se usará para texto e imágenes
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    raise RuntimeError(f"Error al inicializar el cliente de OpenAI: {e}")


# --- 1. GENERACIÓN DE CONTENIDO CREATIVO CON OPENAI (gpt-5-mini) ---
def generate_creative_content(idea: str):
    """Llama a la API de OpenAI (gpt-5-mini) para obtener guion, post y texto para redes."""
    print(f"🧠 Generando contenido creativo con OpenAI (gpt-5-mini) para la idea: '{idea}'...")

    # Prompt MEJORADO con instrucciones de formato estrictas para el guion
    system_prompt = """
    Eres un creador de contenido viral para la cuenta 'Relatos Extraordinarios'.
    Generarás un objeto JSON con tres claves: "script", "blog_article" y "social_post".

    Reglas para "script":
    - La estructura del guion es MUY ESTRICTA y debe seguir este formato por cada escena:
    1.  Un tag de hablante en su propia línea (ej. `[NARRADOR]`).
    2.  Un tag de imagen en la siguiente línea (ej. `[imagen:1.mp4]`).
    3.  El texto descriptivo de la escena en las líneas siguientes.
    4.  Debe haber una línea en blanco entre cada bloque de escena.
    - Ejemplo de una escena:
    [NARRADOR]
    [imagen:1.mp4]
    En los valles más profundos, se susurran leyendas.

    - El guion completo debe tener entre 10 y 11 escenas.
    - La longitud total debe ser de 250 a 300 palabras.
    - Usa `[NARRADOR]` como hablante para todas las escenas.
    - Las imágenes deben estar numeradas secuencialmente: `[imagen:1.mp4]`, `[imagen:2.mp4]`, etc.
    - Todos los números deben estar escritos con letras (ej: "mil novecientos cincuenta y cinco").
    - El guion DEBE terminar obligatoriamente con la etiqueta `[CIERRE]` en su propia línea.
    - Para mantener la coherencia visual, la historia debe centrarse en un único elemento o personaje recurrente (por ejemplo, un faro abandonado, una figura sombría, un objeto maldito). Las descripciones de las escenas deben reforzar este elemento central.
    
    Reglas para "blog_article":
    - Debe expandir la historia del guion con un tono objetivo.
    - El formato debe ser compatible con Google Docs, usando títulos de sección más grandes.
    - Debe finalizar siempre con 5 palabras clave separadas por comas (sin #).

    Reglas para "social_post":
    - Descripción corta e impactante para TikTok (<300 caracteres).
    - No puede empezar con "Te atreves", "Descubre", "Conoces" o "Conocías".
    - Debe incluir siempre el hashtag #RelatosExtraordinarios y hasta 4 hashtags más muy relevantes.
    
    Responde únicamente con el objeto JSON solicitado, sin texto adicional.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Genera el contenido para la siguiente idea: {idea}"}
            ]
        )

        content = json.loads(response.choices[0].message.content)
        print("✅ Contenido creativo generado con éxito.")
        return content

    except Exception as e:
        print(f"❌ Error al generar contenido con OpenAI (gpt-5-mini): {e}")
        return None
        
def rewrite_prompt_for_safety(prompt_text: str, client: OpenAI):
    """Llama a un modelo de texto para reescribir un prompt bloqueado."""
    print("✍️  Reescribiendo el prompt para evitar filtros de seguridad...")
    try:
        response = client.chat.completions.create(
            model="gpt-5-nano", # Usamos un modelo rápido y barato para esta tarea simple
            messages=[
                {"role": "system", "content": (
                    "Eres un asistente que reformula prompts para un generador de imágenes. "
                    "El siguiente prompt fue bloqueado por un filtro de seguridad. "
                    "Tu tarea es reescribirlo para describir una escena visualmente similar, "
                    "pero usando un lenguaje neutro y seguro, evitando palabras que impliquen "
                    "sufrimiento, violencia, 'plagas', 'trastornos' o cualquier contenido sensible. "
                    "Responde únicamente con el prompt reformulado, sin explicaciones."
                )},
                {"role": "user", "content": prompt_text}
            ]
        )
        rewritten_prompt = response.choices[0].message.content.strip()
        print(f"✅ Nuevo prompt generado: '{rewritten_prompt[:80]}...'")
        return rewritten_prompt
    except Exception as e:
        print(f"❌ Error al intentar reescribir el prompt: {e}")
        return None

# --- MENÚ INTERACTIVO PARA SELECCIÓN DE MODELO ---
def interactive_model_selection():
    """Menú interactivo para seleccionar modelo y calidad de imagen."""
    print("\n" + "="*70)
    print("🎨 CONFIGURACIÓN DE GENERACIÓN DE IMÁGENES")
    print("="*70)
    print("\nSelecciona el modelo de generación de imágenes:\n")

    models = [
        {
            "name": "GPT Image 1 Mini - Calidad BAJA",
            "model": "gpt-image-1-mini",
            "quality": "low",
            "cost": "$0.06 por 10 imágenes",
            "note": "Más económico, calidad básica"
        },
        {
            "name": "GPT Image 1 Mini - Calidad MEDIA",
            "model": "gpt-image-1-mini",
            "quality": "medium",
            "cost": "$0.15 por 10 imágenes",
            "note": "Buen balance calidad/precio (RECOMENDADO)"
        },
        {
            "name": "GPT Image 1 - Calidad MEDIA",
            "model": "gpt-image-1",
            "quality": "medium",
            "cost": "$0.63 por 10 imágenes",
            "note": "Mayor calidad GPT Image"
        },
        {
            "name": "GPT Image 1 - Calidad ALTA",
            "model": "gpt-image-1",
            "quality": "high",
            "cost": "$2.50 por 10 imágenes",
            "note": "Máxima calidad GPT Image"
        },
        {
            "name": "DALL-E 2 - Standard",
            "model": "dall-e-2",
            "quality": "standard",
            "cost": "$0.20 por 10 imágenes",
            "note": "Económico, tamaño 1024x1024 (cuadrado)"
        },
        {
            "name": "DALL-E 3 - Standard",
            "model": "dall-e-3",
            "quality": "standard",
            "cost": "$0.80 por 10 imágenes",
            "note": "Alta calidad, garantizado"
        },
        {
            "name": "DALL-E 3 - HD",
            "model": "dall-e-3",
            "quality": "hd",
            "cost": "$1.20 por 10 imágenes",
            "note": "Máxima calidad, más detalle"
        }
    ]

    for i, m in enumerate(models, 1):
        print(f"{i}. {m['name']}")
        print(f"   💰 {m['cost']} | {m['note']}")
        print()

    while True:
        try:
            choice = input("Elige una opción (1-7) [default: 2]: ").strip()
            if choice == "":
                choice = "2"

            idx = int(choice) - 1
            if 0 <= idx < len(models):
                selected = models[idx]
                print(f"\n✅ Seleccionado: {selected['name']}")
                print(f"   Modelo: {selected['model']} | Calidad: {selected['quality']}")
                print(f"   Costo estimado: {selected['cost']}")
                print("="*70 + "\n")
                return selected['model'], selected['quality']
            else:
                print("❌ Opción inválida. Elige un número del 1 al 7.")
        except ValueError:
            print("❌ Por favor, introduce un número válido.")
        except KeyboardInterrupt:
            print("\n\n❌ Cancelado por el usuario.")
            sys.exit(0)


# --- 2. GENERACIÓN DE IMÁGENES ESTÁTICAS CON OPENAI (DALL-E 3) ---
# --- VERSIÓN MEJORADA CON REINTENTO AUTOMÁTICO ---
def generate_visuals_for_script(script_text: str, project_path: str, client: OpenAI, overwrite: bool = False,
                                image_model: str = "dall-e-3", image_quality: str = "standard"):
    """
    Genera imágenes para el guion con un sistema de reintento automático
    que reescribe los prompts bloqueados por el sistema de seguridad.

    Args:
        script_text: El texto del guion con las etiquetas [imagen:N.png]
        project_path: Ruta al directorio del proyecto
        client: Cliente de OpenAI
        overwrite: Si es True, regenera imágenes existentes. Si es False, las salta.
        image_model: Modelo de generación (gpt-image-1-mini, gpt-image-1, dall-e-3, dall-e-2)
        image_quality: Calidad de imagen (low/medium/high para GPT Image, standard/hd para DALL-E)
    """
    print(f"🎨 Empezando la generación de imágenes con reintento automático...")
    print(f"   Modelo: {image_model} | Calidad: {image_quality}")

    # Mapeo de tamaños según modelo
    size_map = {
        "gpt-image-1-mini": "1024x1536",
        "gpt-image-1": "1024x1536",
        "dall-e-3": "1024x1792",
        "dall-e-2": "1024x1024"
    }
    image_size = size_map.get(image_model, "1024x1792")
    print(f"   Tamaño: {image_size}")

    master_prompt = (
        "Crea una ilustración atmosférica al estilo de novela gráfica moderna con enfoque cinematográfico. "
        "Estilo visual: "
        "- **Paleta de colores limitada y atmosférica:** Tonos dominantes acordes a la escena (azules nocturnos para misterio, "
        "ocres cálidos para interiores antiguos, grises fríos para exteriores), con un color de acento ocasional para destacar elementos clave. "
        "- **Iluminación dramática:** Usa luz y sombras para crear atmósfera y profundidad. La iluminación debe reforzar el mood de la escena. "
        "- **Composición cinematográfica:** Encuadre que cuente la historia visualmente, con atención al detalle y texturas realistas. "
        "- **Coherencia narrativa:** Cada imagen debe ser parte de la misma historia visual, manteniendo consistencia en estilo y tono. "
        "Formato vertical para redes sociales (9:16). "
        "Ilustra la siguiente escena específica: "
    )

    scenes = re.findall(r'\[imagen:\d+\.png\]\s*(.*?)(?=\n\s*\[|$)', script_text, re.DOTALL)
    
    if not scenes:
        print("\n❌ ERROR CRÍTICO: No se encontraron descripciones de escenas en el guion.")
        return False

    all_images_successful = True
    MAX_RETRIES = 5 # Número máximo de intentos por imagen (aumentado para errores temporales del servidor)

    for i, scene_text in enumerate(scenes, 1):
        clean_text = scene_text.strip()
        if not clean_text:
            continue

        print(f"🖼️  Generando imagen para escena {i}: '{clean_text[:50]}...'")
        image_path = os.path.join(project_path, "images", f"{i}.png")

        # Verificar si la imagen ya existe y no queremos sobrescribirla
        if os.path.exists(image_path) and not overwrite:
            print(f"   ✓ Imagen {i}.png ya existe, saltando generación.")
            continue

        # Guardamos el prompt específico de la escena para poder modificarlo si falla
        current_scene_prompt = f"\"{clean_text}\""
        image_generated = False

        for attempt in range(MAX_RETRIES):
            try:
                # Componemos el prompt final en cada intento
                final_prompt = f"{master_prompt} {current_scene_prompt}"

                response = client.images.generate(
                  model=image_model,
                  prompt=final_prompt,
                  size=image_size,
                  quality=image_quality,
                  n=1,
                )

                # Validar que tenemos datos de imagen
                if not response.data or len(response.data) == 0:
                    raise RuntimeError(f"La respuesta de la API no contiene datos de imagen")

                image_data = response.data[0]

                # Soportar tanto URL como base64
                image_url = getattr(image_data, "url", None)
                b64_json = getattr(image_data, "b64_json", None)

                if image_url:
                    # Descargar desde URL
                    image_response = requests.get(image_url, timeout=60)
                    image_response.raise_for_status()
                    with open(image_path, "wb") as f:
                        f.write(image_response.content)
                    image_generated = True
                    break
                elif b64_json:
                    # Decodificar desde base64
                    image_bytes = base64.b64decode(b64_json)
                    with open(image_path, "wb") as f:
                        f.write(image_bytes)
                    image_generated = True
                    break
                else:
                    raise RuntimeError(f"La API no devolvió ni url ni b64_json. Respuesta: {image_data}")

            except openai.BadRequestError as e:
                # Comprobamos si el error es específicamente por moderación
                if e.code == 'moderation_blocked':
                    print(f"⚠️ Prompt bloqueado en el intento {attempt + 1}. Intentando reescribir...")
                    rewritten_part = rewrite_prompt_for_safety(current_scene_prompt, client)

                    if rewritten_part:
                        current_scene_prompt = rewritten_part # Actualizamos el prompt para el siguiente intento
                    else:
                        print("❌ No se pudo reescribir el prompt. Abortando esta imagen.")
                        break # Salimos si la reescritura falla
                else:
                    # Si es otro tipo de error, lo mostramos y rompemos el bucle
                    print(f"❌ Error de API no relacionado con la moderación: {e}")
                    all_images_successful = False
                    break

            except openai.APIError as e:
                # Error del servidor (500, 502, 503, etc.) - es temporal, reintentar
                if attempt < MAX_RETRIES - 1:
                    wait_time = (attempt + 1) * 2  # 2s, 4s, 6s...
                    print(f"⚠️ Error temporal del servidor OpenAI (intento {attempt + 1}/{MAX_RETRIES}). Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                    continue  # Reintentar
                else:
                    print(f"❌ Error del servidor OpenAI después de {MAX_RETRIES} intentos: {e}")
                    all_images_successful = False
                    break

            except requests.exceptions.RequestException as e:
                # Error de red al descargar la imagen
                if attempt < MAX_RETRIES - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"⚠️ Error de red al descargar imagen (intento {attempt + 1}/{MAX_RETRIES}). Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"❌ Error de red después de {MAX_RETRIES} intentos: {e}")
                    all_images_successful = False
                    break

            except RuntimeError as e:
                # Error de validación (URL None, respuesta vacía, etc.)
                print(f"❌ Error de validación: {e}")
                print(f"   Modelo '{image_model}' podría no ser válido o no soportar este tamaño/calidad.")
                all_images_successful = False
                break

            except Exception as e:
                print(f"❌ Error inesperado al generar la imagen para la escena {i}: {e}")
                all_images_successful = False
                break
        
        if not image_generated:
            print(f"🚫 Falló la generación de la imagen para la escena {i} después de {MAX_RETRIES} intentos.")
            all_images_successful = False
            break # Detenemos todo el proceso si una imagen falla definitivamente

    if all_images_successful:
        print("✅ Todas las imágenes han sido generadas con éxito.")
        return True
    else:
        print("\n🚫 Proceso detenido debido a un error en la generación de imágenes.")
        return False


# --- 3. FUNCIONES PARA MODO AUTOMÁTICO ---
def run_project_indexer():
    """Ejecuta crear_indice_proyectos.py para actualizar el master list."""
    print("📊 Actualizando índice de proyectos...")
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        indexer_path = os.path.join(script_dir, "crear_indice_proyectos.py")

        if not os.path.exists(indexer_path):
            print(f"⚠️ No se encontró crear_indice_proyectos.py en {indexer_path}")
            return False

        result = subprocess.run(
            [sys.executable, indexer_path],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Índice de proyectos actualizado correctamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar crear_indice_proyectos.py: {e}")
        print(f"Salida: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False


def get_next_project_number():
    """Lee el master list y determina el siguiente número de proyecto."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    master_list_path = os.path.join(script_dir, "_master_project_list.txt")

    if not os.path.exists(master_list_path):
        print("⚠️ No se encontró _master_project_list.txt, usando número 1")
        return 1

    max_number = 0
    try:
        with open(master_list_path, "r", encoding="utf-8") as f:
            for line in f:
                # Buscar líneas que empiecen con número_NOMBRE
                match = re.match(r'^(\d+)_', line)
                if match:
                    num = int(match.group(1))
                    if num > max_number:
                        max_number = num

        next_number = max_number + 1
        print(f"📈 Último proyecto: {max_number}, siguiente: {next_number}")
        return next_number
    except Exception as e:
        print(f"❌ Error al leer _master_project_list.txt: {e}")
        return 1


def generate_project_name_from_idea(idea_text: str, client: OpenAI):
    """Genera un nombre corto de proyecto basado en la idea usando OpenAI."""
    print("🏷️ Generando nombre de proyecto...")

    try:
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": (
                    "Eres un asistente que genera nombres cortos de proyecto. "
                    "Dado un texto descriptivo, debes crear un nombre corto de 1-3 palabras "
                    "en MAYÚSCULAS que capture la esencia del contenido. "
                    "El nombre debe ser memorable, descriptivo y apropiado para un proyecto de misterio/paranormal. "
                    "RESPONDE SOLO CON EL NOMBRE, SIN EXPLICACIONES. "
                    "Ejemplos: METROMADRID, CASTILLOCARDONA, PALACIOLINARES, HOMBREPEZ"
                )},
                {"role": "user", "content": f"Genera un nombre de proyecto para: {idea_text}"}
            ]
        )

        project_name = response.choices[0].message.content.strip()
        # Limpiar el nombre (solo letras y números, mayúsculas)
        project_name = re.sub(r'[^A-Z0-9]', '', project_name.upper())

        print(f"✅ Nombre generado: {project_name}")
        return project_name
    except Exception as e:
        print(f"❌ Error al generar nombre de proyecto: {e}")
        # Fallback: generar nombre genérico basado en timestamp
        import datetime
        fallback_name = f"PROYECTO{datetime.datetime.now().strftime('%m%d%H%M')}"
        print(f"⚠️ Usando nombre fallback: {fallback_name}")
        return fallback_name


def generate_automatic_idea(client: OpenAI):
    """Analiza el master list y genera una nueva idea viral usando OpenAI."""
    print("\n" + "="*70)
    print("🤖 MODO AUTOMÁTICO ACTIVADO")
    print("="*70)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    master_list_path = os.path.join(script_dir, "_master_project_list.txt")

    if not os.path.exists(master_list_path):
        print(f"❌ Error: No se encontró {master_list_path}")
        return None

    # Leer el contenido del master list
    print("📖 Leyendo análisis de proyectos anteriores...")
    try:
        with open(master_list_path, "r", encoding="utf-8") as f:
            master_content = f.read()
    except Exception as e:
        print(f"❌ Error al leer el archivo: {e}")
        return None

    # Crear el prompt para OpenAI
    print("🧠 Analizando proyectos virales y generando nueva idea...")

    system_prompt = """
Eres un analista de contenido viral experto en la cuenta 'Relatos Extraordinarios'.

Tu tarea es:
1. Analizar el índice de proyectos proporcionado
2. Identificar patrones en los proyectos VIRALES (_v) y MEDIO VIRALES (_mv)
3. Generar UNA SOLA idea original para un nuevo proyecto que:
   - Siga los patrones de los proyectos virales exitosos
   - Sea completamente original (no repetir temas ya hechos)
   - Tenga potencial viral similar
   - Se centre en misterio, paranormal, leyendas españolas, lugares abandonados o historias extraordinarias
   - Sea específica y detallada (200-300 palabras)

IMPORTANTE:
- Responde SOLO con la idea del nuevo proyecto, sin explicaciones adicionales
- La idea debe ser un texto narrativo listo para usar
- No incluyas títulos ni encabezados, solo el contenido de la idea
- Debe ser similar en tono y estructura a las ideas existentes en el índice
"""

    user_prompt = f"""
Aquí está el índice completo de proyectos con especial atención a los VIRALES y MEDIO VIRALES al final:

{master_content}

Genera UNA idea original para el siguiente proyecto que tenga alto potencial viral.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8  # Un poco de creatividad
        )

        new_idea = response.choices[0].message.content.strip()

        print("\n" + "="*70)
        print("💡 NUEVA IDEA GENERADA:")
        print("="*70)
        print(new_idea)
        print("="*70 + "\n")

        return new_idea
    except Exception as e:
        print(f"❌ Error al generar idea automática: {e}")
        return None


# --- 4. FUNCIÓN PRINCIPAL ORQUESTADORA ---
def main():
    parser = argparse.ArgumentParser(description="Automatización para Relatos Extraordinarios")
    parser.add_argument("--idea", required=False, help="La idea principal para el vídeo.")
    parser.add_argument("--project-name", required=False, help="El nombre de la carpeta del proyecto (p.ej. 192_RISA).")
    parser.add_argument("--overwrite-images", action="store_true", help="Regenera todas las imágenes aunque ya existan.")
    parser.add_argument("--force-video", action="store_true", help="Regenera el video aunque ya exista.")
    parser.add_argument("--image-model", default=None,
                        choices=["gpt-image-1-mini", "gpt-image-1", "dall-e-3", "dall-e-2"],
                        help="Modelo de generación de imágenes. Si no se especifica, se mostrará un menú interactivo.")
    parser.add_argument("--image-quality", default=None,
                        help="Calidad de imagen: low/medium/high (GPT Image) o standard/hd (DALL-E). Si no se especifica, se mostrará un menú interactivo.")
    args = parser.parse_args()

    # --- MODO AUTOMÁTICO ---
    # Si no se proporcionó idea ni project-name, activar modo automático
    if args.idea is None and args.project_name is None:
        print("\n🚀 Modo automático detectado (no se proporcionaron --idea ni --project-name)")

        # 1. Ejecutar crear_indice_proyectos.py
        if not run_project_indexer():
            print("❌ Error al actualizar el índice de proyectos. Abortando.")
            return

        # 2. Generar idea automáticamente analizando proyectos virales
        auto_idea = generate_automatic_idea(client)
        if not auto_idea:
            print("❌ Error al generar idea automática. Abortando.")
            return

        # 3. Determinar siguiente número de proyecto
        next_number = get_next_project_number()

        # 4. Generar nombre de proyecto
        project_short_name = generate_project_name_from_idea(auto_idea, client)

        # 5. Construir nombre completo del proyecto
        args.idea = auto_idea
        args.project_name = f"{next_number}_{project_short_name}"

        print(f"\n✅ Proyecto automático configurado:")
        print(f"   📂 Nombre: {args.project_name}")
        print(f"   💡 Idea: {auto_idea[:100]}...")
        print("\n" + "="*70)
        print("Continuando con el flujo normal de generación...")
        print("="*70 + "\n")

    # Verificar que ahora tenemos idea y project-name (manual o automático)
    if not args.idea or not args.project_name:
        print("❌ Error: Se requiere --idea y --project-name (o ninguno para modo automático)")
        parser.print_help()
        return

    # Si no se especificaron modelo y calidad, mostrar menú interactivo
    if args.image_model is None or args.image_quality is None:
        args.image_model, args.image_quality = interactive_model_selection()

    project_path = args.project_name
    images_path = os.path.join(project_path, "images")

    # --- LÓGICA DE CREACIÓN DE PROYECTO ---
    if not os.path.exists(images_path):
        os.makedirs(images_path)
        print(f"📁 Proyecto creado en: ./{project_path}/")

        # Copiamos los archivos base si existen en la carpeta principal del script
        print("📥 Copiando archivos base (musica.mp3, cierre.mp4)...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        for file_name in ["musica.mp3", "cierre.mp4"]:
            source_file = os.path.join(script_dir, file_name)
            if os.path.exists(source_file):
                # Copiar a la carpeta images/
                dest_file = os.path.join(images_path, file_name)
                shutil.copy(source_file, dest_file)
                print(f"   ✓ {file_name} copiado a images/")
            else:
                print(f"⚠️  Aviso: El archivo '{file_name}' no se encontró en {script_dir}. No se copiará.")

    script_file = os.path.join(project_path, "texto.txt")
    social_file = os.path.join(project_path, "redes.txt")
    
    content = None
    if not os.path.exists(script_file):
        content_generated = generate_creative_content(args.idea)
        if not content_generated:
            return

        with open(script_file, "w", encoding="utf-8") as f:
            # Reemplazamos .mp4 por .png desde el momento de la creación
            script_content = content_generated["script"].replace(".mp4", ".png")
            f.write(script_content)
            
        with open(social_file, "w", encoding="utf-8") as f:
            f.write(content_generated["social_post"])
            
        content = {"script": script_content}
            
    else:
        print("📝 Archivos de texto ya existen, saltando generación de contenido.")
        with open(script_file, "r", encoding="utf-8") as f:
            # Nos aseguramos de que el guion que leemos usa .png para la lógica de re-generación
            script_content = f.read().replace(".mp4", ".png")
            content = {"script": script_content}

    # Llamada a la función de imágenes pasando el objeto 'client' para las reescrituras
    success = generate_visuals_for_script(
        content["script"],
        project_path,
        client,
        overwrite=args.overwrite_images,
        image_model=args.image_model,
        image_quality=args.image_quality
    )
    if not success:
        return

    # El bloque que modificaba el guion aquí ya no es necesario,
    # porque nos aseguramos de que siempre trabaje con .png desde el principio.

    # Verificar si el video base ya existe
    video_out_path = os.path.join(project_path, "Out", "video.mp4")
    video_exists = os.path.exists(video_out_path)

    if video_exists and not args.force_video:
        print(f"\n✅ El video base ya existe en '{video_out_path}'")
        print("   Saltando generación de video. Usa --force-video si quieres regenerarlo.")
        print("\n💡 Puedes ejecutar manualmente desde la carpeta del proyecto:")
        print(f"   cd {project_path}")
        print(f"   powershell -ExecutionPolicy Bypass ..\\run.ps1 -NoBurn  (para regenerar solo video)")
        print(f"   powershell -ExecutionPolicy Bypass ..\\run.ps1           (para quemar subtítulos)")
        return

    print("\n🎬 Todo listo. Lanzando el renderizado final con run.ps1...")

    # Obtener la ruta absoluta de run.ps1 (está en el mismo directorio que este script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    run_ps1_path = os.path.join(script_dir, "run.ps1")

    command = [
        "powershell.exe", "-ExecutionPolicy", "Bypass", "-File", run_ps1_path,
        "-Resolution", "1080x1920", "-Fit", "cover", "-KenBurns", "in",
        "-KbZoom", "0.2", "-KbPan", "random", "-KbSticky", "-VideoFill", "slow",
        "-MediaKeepAudio", "-MediaAudioVol", "0.1",
        "-MusicAudio", "-MusicAudioVol", "0.1"
    ]

    try:
        # Ejecutamos el comando desde dentro de la carpeta del proyecto
        subprocess.run(command, cwd=project_path, check=True, shell=True)
        print(f"\n✅ ¡Proceso completado! El vídeo final está en la carpeta '{project_path}/Out'.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al ejecutar run.ps1: {e}")
    except FileNotFoundError:
        print(f"❌ Error: 'run.ps1' no encontrado en {run_ps1_path}. Revisa la ruta en el script.")


if __name__ == "__main__":
    main()