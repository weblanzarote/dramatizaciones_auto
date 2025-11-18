"""
Servicio para interactuar con Google Gemini (generación de imágenes).
"""
import time
from google import genai
from google.genai import types
from ..config.settings import GEMINI_API_KEY
from ..config.styles import build_master_prompt
from ..media.image_proc import pixelize_image


class GeminiService:
    """Cliente para Google Gemini."""

    def __init__(self, api_key: str = None):
        """
        Inicializa el cliente de Gemini.

        Args:
            api_key: Clave API de Gemini. Si no se proporciona, usa la del config.
        """
        self.api_key = api_key or GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY no configurada")

        self.client = genai.Client(api_key=self.api_key)

    def generate_image(self, prompt: str, aspect_ratio: str = "9:16",
                      number_of_images: int = 1, **kwargs):
        """
        Genera imágenes con Gemini.

        Args:
            prompt: Descripción de la imagen
            aspect_ratio: Ratio de aspecto (ej: "9:16", "1:1")
            number_of_images: Número de imágenes a generar
            **kwargs: Argumentos adicionales

        Returns:
            Respuesta de la API con las imágenes generadas
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-image",
                contents=[prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=types.ImageConfig(
                        aspect_ratio=aspect_ratio,
                    ),
                    **kwargs
                )
            )
            return response
        except Exception as e:
            raise RuntimeError(f"Error al generar imagen con Gemini: {e}")

    def generate_visuals_for_script(
        self,
        visual_prompts_list: list,
        audio_scenes_list: list,
        scene_contexts_list: list,
        project_path: str,
        client_openai,
        style_block: str,
        overwrite: bool,
        image_model: str = "gemini-2.5-flash-image",
        style_slug_for_pixelize: str = ""
    ) -> bool:
        """
        Genera imágenes con Google Gemini usando:
        - visual_prompts_list: prompts visuales dedicados por escena
        - audio_scenes_list: texto de audio original (solo para logs)
        - scene_contexts_list: brief de consistencia específico por escena

        Args:
            visual_prompts_list: Lista de prompts visuales
            audio_scenes_list: Lista de textos de audio (para logs)
            scene_contexts_list: Lista de contextos de consistencia
            project_path: Ruta del proyecto
            client_openai: Cliente de OpenAI (para reescritura de prompts)
            style_block: Bloque de estilo visual
            overwrite: ¿Sobrescribir imágenes existentes?
            image_model: Modelo de Gemini a usar
            style_slug_for_pixelize: Slug del estilo (para detectar pixel art)

        Returns:
            True si todas las imágenes se generaron correctamente
        """
        import os
        from ..content.scripting import rewrite_prompt_for_safety

        print(f"🎨 Generando imágenes con Google Gemini (Opción alta calidad)...")
        print(f"   Modelo: {image_model}")

        all_images_successful = True
        MAX_RETRIES = 5

        total_scenes = len(visual_prompts_list)

        for idx, visual_prompt in enumerate(visual_prompts_list):
            clean_text = visual_prompt.strip()
            if not clean_text:
                continue

            audio_text = audio_scenes_list[idx] if idx < len(audio_scenes_list) else ""
            scene_ctx = scene_contexts_list[idx] if scene_contexts_list and idx < len(scene_contexts_list) else ""

            print(f"🖼️  Generando imagen para escena {idx+1}: '{audio_text[:60]}...'")
            image_path = os.path.join(project_path, "images", f"{idx+1}.png")
            os.makedirs(os.path.dirname(image_path), exist_ok=True)

            if os.path.exists(image_path) and not overwrite:
                print(f"   ✓ Imagen {idx+1}.png ya existe, saltando generación.")
                continue

            image_generated = False

            for attempt in range(MAX_RETRIES):
                try:
                    # Prompt final: contexto de consistencia + estilo + prompt visual
                    final_prompt = scene_ctx + "\n\n" + build_master_prompt(style_block, clean_text)
                    final_prompt += f"\n\nEscena {idx+1} de {total_scenes} en la narrativa."
                    print(f"   → Escena {idx+1}/{total_scenes} con contexto narrativo específico")

                    response = self.client.models.generate_content(
                        model=image_model,
                        contents=[final_prompt],
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"],
                            image_config=types.ImageConfig(
                                aspect_ratio="9:16",
                            ),
                        ),
                    )

                    image_saved = False
                    if hasattr(response, 'parts'):
                        for part in response.parts:
                            if hasattr(part, 'inline_data') and part.inline_data is not None:
                                pil_image = part.as_image()
                                pil_image.save(image_path)
                                image_saved = True
                                break

                    if not image_saved:
                        raise RuntimeError("Gemini no devolvió datos de imagen válidos en response.parts")

                    if "pixel" in style_slug_for_pixelize:
                        pixelize_image(image_path, small_edge=256)
                        print("   ↳ postproceso: pixelize aplicado (downscale + NEAREST)")

                    print(f"   ✔ Guardada: {image_path}")
                    image_generated = True
                    break

                except Exception as e:
                    error_message = str(e)
                    if "SAFETY" in error_message or "BLOCKED" in error_message:
                        print(f"⚠️ Prompt bloqueado por seguridad (intento {attempt + 1}). Reescribiendo...")
                        rewritten_prompt = rewrite_prompt_for_safety(clean_text, client_openai)
                        if rewritten_prompt:
                            clean_text = rewritten_prompt
                            continue
                        else:
                            all_images_successful = False
                            break
                    elif attempt < MAX_RETRIES - 1:
                        wait_time = (attempt + 1) * 2
                        print(f"⚠️ Error temporal (intento {attempt + 1}/{MAX_RETRIES}): {error_message[:100]}")
                        print(f"   Reintentando en {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ Error después de {MAX_RETRIES} intentos: {error_message}")
                        all_images_successful = False
                        break

            if not image_generated:
                print(f"🚫 Falló la generación de la imagen para la escena {idx+1} después de {MAX_RETRIES} intentos.")
                all_images_successful = False
                break

            time.sleep(1)

        return all_images_successful
