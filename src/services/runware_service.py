"""
Servicio para interactuar con Runware (generación y animación de imágenes).
"""
import os
import re
import time
import base64
import io
import asyncio
import requests
from pathlib import Path
from PIL import Image

from ..config.settings import RUNWARE_API_KEY, QWEN_AIR_ID, NEGATIVE_PROMPT
from ..config.styles import _build_runware_prompt
from ..media.image_proc import pixelize_image

# Intentar importar Runware
try:
    from runware import Runware, IVideoInference, IFrameImage, IImageInference
    RUNWARE_AVAILABLE = True
except ImportError:
    RUNWARE_AVAILABLE = False
    Runware = None
    IVideoInference = None
    IFrameImage = None
    IImageInference = None


class RunwareService:
    """Cliente para Runware."""

    def __init__(self, api_key: str = None):
        """
        Inicializa el servicio de Runware.

        Args:
            api_key: Clave API de Runware. Si no se proporciona, usa la del config.
        """
        if not RUNWARE_AVAILABLE:
            raise ImportError(
                "Runware no está instalado. Ejecuta: pip install runware"
            )

        self.api_key = api_key or RUNWARE_API_KEY
        if not self.api_key:
            raise ValueError("RUNWARE_API_KEY no configurada")

    async def generate_visuals_for_script(
        self,
        visual_prompts_list: list,
        audio_scenes_list: list,
        scene_contexts_list: list,
        project_path: str,
        style_block: str,
        overwrite: bool,
        style_slug_for_pixelize: str = ""
    ) -> bool:
        """
        Genera imágenes con Runware (Qwen-Image) de forma async.

        Args:
            visual_prompts_list: Lista de prompts visuales
            audio_scenes_list: Lista de textos de audio (para logs)
            scene_contexts_list: Lista de contextos de consistencia
            project_path: Ruta del proyecto
            style_block: Bloque de estilo visual
            overwrite: ¿Sobrescribir imágenes existentes?
            style_slug_for_pixelize: Slug del estilo (para detectar pixel art)

        Returns:
            True si todas las imágenes se generaron correctamente
        """
        print(f"🎨 Generando imágenes con Runware (Opción ahorro: Qwen-Image)...")
        print(f"   Modelo: Qwen-Image ({QWEN_AIR_ID})")
        print(f"   Parámetros: CFGScale=2.5, Steps=20")

        runware = None
        all_images_successful = True

        try:
            # Conectar a Runware
            runware = Runware(api_key=self.api_key)
            await runware.connect()
            print("\n✅ Conectado a Runware API para generación de imágenes.")

            # Iterar sobre la lista de prompts visuales
            for i, visual_prompt in enumerate(visual_prompts_list):

                # Obtenemos datos de la escena para los logs y el nombre de archivo
                image_id = f"{i+1}.png"
                audio_text = audio_scenes_list[i] if i < len(audio_scenes_list) else ""

                print(f"🖼️  Generando imagen {image_id} (Audio: '{audio_text[:40]}...'):")
                print(f"   Llamando con Visual Prompt: '{visual_prompt[:60]}...'")
                image_path = os.path.join(project_path, "images", image_id)
                os.makedirs(os.path.dirname(image_path), exist_ok=True)

                if os.path.exists(image_path) and not overwrite:
                    print(f"   ✓ Imagen {image_id} ya existe, saltando generación.")
                    continue

                image_generated = False

                try:
                    # Construir prompt con contexto de consistencia
                    scene_context = ""
                    if scene_contexts_list and i < len(scene_contexts_list):
                        scene_context = scene_contexts_list[i]

                    final_prompt = _build_runware_prompt(style_block, visual_prompt, scene_context, max_length=1850)

                    # Log de depuración
                    prompt_length = len(final_prompt)
                    print("\n" + "="*80)
                    print(f"   DEBUG: Preparando prompt para Qwen (Escena {i+1})")
                    print(f"   LONGITUD TOTAL: {prompt_length} caracteres (Límite: 1900)")
                    if prompt_length > 1900:
                        print("   !!!!!!!!!! ALERTA: EL PROMPT SUPERA EL LÍMITE !!!!!!!!!")
                    print("="*80)
                    print(final_prompt)
                    print("="*80 + "\n")

                    # Parámetros de Runware
                    params = {
                        "positivePrompt": final_prompt,
                        "negativePrompt": NEGATIVE_PROMPT,
                        "model": QWEN_AIR_ID,
                        "width": 768,   # 9:16
                        "height": 1344, # 9:16
                        "numberResults": 1,
                        "includeCost": True,
                        "CFGScale": 2.5,
                        "steps": 20
                    }

                    request = IImageInference(**params)
                    images = await runware.imageInference(requestImage=request)

                    if not images:
                        raise RuntimeError("La API de Runware no devolvió imágenes.")

                    # Procesar respuesta
                    image_res = images[0]
                    image_url = image_res.imageURL
                    cost = image_res.cost if hasattr(image_res, 'cost') and image_res.cost else "N/A"

                    # Descargar y guardar la imagen
                    response = requests.get(image_url, timeout=120)
                    response.raise_for_status()
                    with open(image_path, "wb") as f:
                        f.write(response.content)

                    # Postproceso: Pixel Art
                    if "pixel" in style_slug_for_pixelize:
                        pixelize_image(image_path, small_edge=256)
                        print("   ↳ postproceso: pixelize aplicado (downscale + NEAREST)")

                    cost_str = f" (Coste: ${cost})" if cost != "N/A" else ""
                    print(f"   ✔ Guardada: {image_path}{cost_str}")
                    image_generated = True

                except Exception as e:
                    print(f"❌ Error en escena {i+1} (Runware): {e}")
                    if "1900 characters" in str(e):
                        print("   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                        print("   ERROR: El prompt ha superado los 1900 caracteres.")
                        print("   Revisa la longitud del brief.txt y de los estilos.")
                        print("   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    all_images_successful = False
                    break  # Detener en caso de error

                time.sleep(1)  # Pausa entre imágenes

        except Exception as e:
            print(f"❌ Error fatal conectando o generando con Runware: {e}")
            all_images_successful = False
        finally:
            if runware:
                await runware.disconnect()
                print("\n🔌 Desconectado de Runware API (imágenes).")

        return all_images_successful

    async def animate_single_image(
        self,
        runware_instance,
        image_path: str,
        video_path: str,
        image_number: str
    ) -> bool:
        """
        Anima una imagen estática con Seedance 1.0 Pro Fast.

        Args:
            runware_instance: Instancia de Runware ya conectada
            image_path: Ruta a la imagen PNG
            video_path: Ruta de salida del video MP4
            image_number: Número de imagen (para logs)

        Returns:
            True si la animación fue exitosa
        """
        MAX_RETRIES = 3

        for attempt in range(MAX_RETRIES):
            try:
                print(f"🎥 Animando imagen {image_number}...")

                # Leer y procesar la imagen
                img = Image.open(image_path)
                width, height = img.size
                aspect_ratio = width / height

                print(f"   📐 Imagen original: {width}x{height} (ratio: {aspect_ratio:.3f})")

                # Dimensiones soportadas por Seedance 1.0 Pro Fast (bytedance:2@2)
                SUPPORTED_DIMENSIONS = [
                    (864, 480, 1.800, "16:9 landscape"),
                    (736, 544, 1.353, "4:3 landscape"),
                    (640, 640, 1.000, "1:1 square"),
                    (544, 736, 0.739, "3:4 portrait"),
                    (480, 864, 0.556, "9:16 portrait"),
                    (416, 960, 0.433, "9:21 portrait"),
                    (960, 416, 2.308, "21:9 landscape"),
                ]

                # Encontrar dimensión más cercana
                best_match = min(SUPPORTED_DIMENSIONS, key=lambda d: abs(d[2] - aspect_ratio))
                output_width, output_height, _, format_name = best_match

                print(f"   → Usando dimensión: {output_width}x{output_height} ({format_name})")

                # Convertir imagen a base64
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                image_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
                image_uri = f"data:image/png;base64,{image_data}"

                # Crear request para Runware usando Seedance 1.0 Pro Fast
                request = IVideoInference(
                    positivePrompt="Smooth cinematic camera movement, subtle atmospheric motion, natural dynamics",
                    model="bytedance:2@2",  # Seedance 1.0 Pro Fast
                    duration=6,  # 6 segundos
                    width=output_width,
                    height=output_height,
                    numberResults=1,
                    includeCost=True,
                    frameImages=[
                        IFrameImage(
                            inputImage=image_uri,
                            frame="first"
                        )
                    ]
                )

                # Generar video
                videos = await runware_instance.videoInference(requestVideo=request)

                if videos and len(videos) > 0:
                    video = videos[0]

                    # Descargar el video desde la URL
                    print(f"   📥 Descargando video desde Runware...")
                    response = requests.get(video.videoURL, timeout=120)
                    response.raise_for_status()

                    with open(video_path, "wb") as video_file:
                        video_file.write(response.content)

                    # Mostrar información de costo
                    if hasattr(video, 'cost') and video.cost:
                        print(f"   💰 Costo: ${video.cost}")

                    print(f"   ✔ Video guardado: {video_path}")
                    return True
                else:
                    raise RuntimeError("Runware no devolvió videos")

            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = (attempt + 1) * 3
                    print(f"   ⚠️  Error (intento {attempt + 1}/{MAX_RETRIES}): {e}")
                    print(f"   Reintentando en {wait_time}s...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    print(f"   ❌ Error después de {MAX_RETRIES} intentos: {e}")
                    return False

        return False

    def animate_images(self, project_path: str, overwrite: bool = False) -> bool:
        """
        Anima todas las imágenes PNG del proyecto usando Seedance 1.0 Pro Fast.

        Args:
            project_path: Ruta al directorio del proyecto
            overwrite: Si es True, regenera videos existentes

        Returns:
            True si todas las animaciones se generaron correctamente
        """
        print("\n🎬 Iniciando animación de imágenes con Runware...")
        print("   Modelo: Seedance 1.0 Pro Fast (bytedance:2@2)")
        print("   Duración: 6 segundos por video")
        print("   Resolución: Auto-detecta aspect ratio")
        print("   Costo: ~$0.0315 por video → ~$0.19-0.31 por proyecto de 6-10 videos 💰")
        print("   💡 AHORRO: 65% más barato que Replicate\n")

        images_path = os.path.join(project_path, "images")
        if not os.path.exists(images_path):
            print(f"❌ Error: No se encontró la carpeta {images_path}")
            return False

        # Buscar todas las imágenes PNG numeradas
        image_files = []
        for filename in os.listdir(images_path):
            if re.match(r'^\d+\.png$', filename):
                image_files.append(filename)

        if not image_files:
            print(f"❌ Error: No se encontraron imágenes PNG numeradas en {images_path}")
            return False

        # Ordenar por número
        image_files.sort(key=lambda x: int(x.split('.')[0]))
        print(f"📁 Encontradas {len(image_files)} imágenes para animar: {', '.join(image_files)}\n")

        # Función async principal
        async def animate_all():
            runware = Runware(api_key=self.api_key)
            await runware.connect()
            print("✅ Conectado a Runware API\n")

            all_videos_successful = True

            try:
                for image_file in image_files:
                    image_number = image_file.split('.')[0]
                    image_path = os.path.join(images_path, image_file)
                    video_path = os.path.join(images_path, f"{image_number}.mp4")

                    # Si ya existe y no queremos sobrescribir
                    if os.path.exists(video_path) and not overwrite:
                        print(f"✓ Video {image_number}.mp4 ya existe, saltando animación.")
                        continue

                    # Animar imagen
                    success = await self.animate_single_image(
                        runware, image_path, video_path, image_number
                    )

                    if not success:
                        print(f"🚫 Falló la animación de {image_file}")
                        all_videos_successful = False

                    # Pequeña pausa entre llamadas
                    await asyncio.sleep(1)

            finally:
                try:
                    await runware.disconnect()
                except Exception as e:
                    print(f"   ⚠️  Advertencia al cerrar conexión: {e}")

            return all_videos_successful

        # Ejecutar el loop async
        all_successful = asyncio.run(animate_all())

        if all_successful:
            print("\n✅ Todas las imágenes han sido animadas con éxito.")
            print(f"   Los videos están en: {images_path}/")
            print(f"   Archivos: 1.mp4, 2.mp4, 3.mp4, etc.")
            return True
        else:
            print("\n⚠️  Proceso completado con algunos errores en la animación.")
            return False


def is_runware_available() -> bool:
    """Verifica si Runware está disponible."""
    return RUNWARE_AVAILABLE
