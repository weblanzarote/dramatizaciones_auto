import os
import shutil
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


# --- 1. GENERACIÓN DE CONTENIDO CREATIVO CON OPENAI (gpt-4o-mini) ---
def generate_creative_content(idea: str):
    """Llama a la API de OpenAI (gpt-4o-mini) para obtener guion, post y texto para redes."""
    print(f"🧠 Generando contenido creativo con OpenAI para la idea: '{idea}'...")

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
            model="gpt-4o-mini",
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
        print(f"❌ Error al generar contenido con OpenAI (gpt-4o-mini): {e}")
        return None
        
def rewrite_prompt_for_safety(prompt_text: str, client: OpenAI):
    """Llama a un modelo de texto para reescribir un prompt bloqueado."""
    print("✍️  Reescribiendo el prompt para evitar filtros de seguridad...")
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Usamos un modelo rápido y barato para esta tarea
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

# --- 2. GENERACIÓN DE IMÁGENES ESTÁTICAS CON OPENAI (DALL-E 3) ---
# --- VERSIÓN MEJORADA CON REINTENTO AUTOMÁTICO ---
def generate_visuals_for_script(script_text: str, project_path: str, client: OpenAI):
    """
    Genera imágenes para el guion con un sistema de reintento automático
    que reescribe los prompts bloqueados por el sistema de seguridad.
    """
    print("🎨 Empezando la generación de imágenes con reintento automático...")

    master_prompt = (
        "Eres un ilustrador de novelas gráficas de terror. El estilo visual es el de un cómic gótico y oscuro, "
        "fuertemente inspirado en el arte de Mike Mignola (Hellboy), pero con un mayor nivel de detalle cinematográfico. "
        "Características NO NEGOCIABLES del estilo: "
        "- **Paleta de colores muy limitada y desaturada:** Dominada por negros profundos, grises fríos, azules nocturnos y un único color de acento ocasional como un rojo sangre o un amarillo enfermizo. "
        "- **Iluminación dramática (claroscuro):** Usa sombras duras y proyectadas para ocultar detalles y crear tensión. La luz debe parecer que emana de fuentes débiles y misteriosas. "
        "- **Texturas orgánicas y ásperas:** Trazos de tinta visibles, superficies rugosas en la piedra y la madera, y un grano de película sutil sobre toda la imagen. "
        "- **Personaje recurrente:** La historia puede incluir a 'El Coleccionista', una figura alta y demacrada con un largo abrigo oscuro y un sombrero de ala ancha que siempre oculta su rostro en la sombra. Si aparece, su aspecto debe ser consistente. "
        "Cada imagen debe sentirse como una viñeta de la misma página del mismo cómic. Mantén siempre una relación de aspecto vertical de 1024x1536. "
        "Ahora, ilustra la siguiente escena específica de la historia: "
    )

    scenes = re.findall(r'\[imagen:\d+\.png\]\s*(.*?)(?=\n\s*\[|$)', script_text, re.DOTALL)
    
    if not scenes:
        print("\n❌ ERROR CRÍTICO: No se encontraron descripciones de escenas en el guion.")
        return False

    all_images_successful = True
    MAX_RETRIES = 3 # Número máximo de intentos por imagen

    for i, scene_text in enumerate(scenes, 1):
        clean_text = scene_text.strip()
        if not clean_text:
            continue

        print(f"🖼️  Generando imagen para escena {i}: '{clean_text[:50]}...'")
        image_path = os.path.join(project_path, "images", f"{i}.png")
        
        # Guardamos el prompt específico de la escena para poder modificarlo si falla
        current_scene_prompt = f"\"{clean_text}\""
        image_generated = False

        for attempt in range(MAX_RETRIES):
            try:
                # Componemos el prompt final en cada intento
                final_prompt = f"{master_prompt} {current_scene_prompt}"
                
                response = client.images.generate(
                  model="dall-e-3",
                  prompt=final_prompt,
                  size="1024x1792",
                  quality="standard",
                  n=1,
                )
                image_url = response.data[0].url
                
                image_response = requests.get(image_url, timeout=60)
                image_response.raise_for_status()
                
                with open(image_path, "wb") as f:
                    f.write(image_response.content)
                
                image_generated = True
                break # Si la imagen se genera con éxito, salimos del bucle de reintentos

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


# --- 3. FUNCIÓN PRINCIPAL ORQUESTADORA ---
def main():
    parser = argparse.ArgumentParser(description="Automatización para Relatos Extraordinarios")
    parser.add_argument("--idea", required=True, help="La idea principal para el vídeo.")
    parser.add_argument("--project-name", required=True, help="El nombre de la carpeta del proyecto (p.ej. 192_RISA).")
    args = parser.parse_args()

    project_path = args.project_name
    images_path = os.path.join(project_path, "images")
    
    # --- LÓGICA DE CREACIÓN DE PROYECTO ---
    if not os.path.exists(images_path):
        os.makedirs(images_path)
        print(f"📁 Proyecto creado en: ./{project_path}/")

        # Copiamos los archivos base si existen en la carpeta principal
        print("📥 Copiando archivos base (musica.mp3, cierre.mp4)...")
        for file_name in ["musica.mp3", "cierre.mp4"]:
            source_file = file_name
            if os.path.exists(source_file):
                shutil.copy(source_file, os.path.join(project_path, file_name)) # Copia al directorio del proyecto
            else:
                print(f"⚠️  Aviso: El archivo '{file_name}' no se encontró en la carpeta principal. No se copiará.")

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
    success = generate_visuals_for_script(content["script"], project_path, client)
    if not success:
        return

    # El bloque que modificaba el guion aquí ya no es necesario,
    # porque nos aseguramos de que siempre trabaje con .png desde el principio.
    
    print("\n🎬 Todo listo. Lanzando el renderizado final con run.ps1...")
    
    # Asegúrate de que la ruta a run.ps1 es correcta. Si está en la carpeta superior: ..\\run.ps1
    # Si create_project.py y run.ps1 están en la misma carpeta, la ruta sería solo "run.ps1"
    command = [
        "powershell.exe", "-ExecutionPolicy", "Bypass", "-File", "run.ps1",
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
        print("❌ Error: 'run.ps1' no encontrado. Revisa la ruta en el script.")


if __name__ == "__main__":
    main()