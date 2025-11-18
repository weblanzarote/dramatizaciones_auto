#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generador de proyectos de dramatización.
Punto de entrada principal para crear historias con guion e imágenes.

Antes: create_project.py
Ahora: Usa los módulos refactorizados en src/
"""
import argparse
import json
import sys
from pathlib import Path

# Importar configuración
from src.config.settings import validate_api_keys
from src.config.styles import STYLE_NAMES, STYLE_PRESETS_GEMINI, build_master_prompt

# Importar servicios
from src.services.openai_service import OpenAIService
from src.services.gemini_service import GeminiService

# Importar lógica de contenido
from src.content.ideation import generate_project_name_from_idea, generate_automatic_idea
from src.content.scripting import generate_creative_content, generate_visual_prompts_for_script


def interactive_style_selection():
    """Menú interactivo para seleccionar estilo visual."""
    print("\n" + "="*70)
    print("🎨 SELECCIÓN DE ESTILO VISUAL")
    print("="*70 + "\n")

    for i, name in enumerate(STYLE_NAMES, 1):
        print(f"{i}. {name}")

    while True:
        try:
            choice = input(f"\nElige un estilo (1-{len(STYLE_NAMES)}) [default: 1]: ").strip()
            if choice == "":
                choice = "1"

            idx = int(choice) - 1
            if 0 <= idx < len(STYLE_NAMES):
                selected_name = STYLE_NAMES[idx]
                print(f"\n✅ Seleccionado: {selected_name}\n")
                return selected_name
            else:
                print(f"❌ Opción inválida. Elige un número del 1 al {len(STYLE_NAMES)}.")
        except ValueError:
            print("❌ Por favor, introduce un número válido.")
        except KeyboardInterrupt:
            print("\n\n❌ Cancelado por el usuario.")
            sys.exit(0)


def main():
    """Función principal del generador."""
    parser = argparse.ArgumentParser(
        description="Generador de proyectos de dramatización con IA"
    )
    parser.add_argument("--idea", type=str, help="Idea para la historia")
    parser.add_argument("--auto-idea", action="store_true", help="Generar idea automáticamente")
    parser.add_argument("--output", type=Path, default=Path("./output"), help="Directorio de salida")
    parser.add_argument("--dry-run", action="store_true", help="Simular sin generar imágenes")
    parser.add_argument("--overwrite", action="store_true", help="Sobrescribir imágenes existentes")

    args = parser.parse_args()

    # Validar API keys
    try:
        validate_api_keys(["OPENAI_API_KEY", "GEMINI_API_KEY"])
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)

    # Inicializar servicios
    print("🚀 Inicializando servicios...")
    openai_service = OpenAIService()
    gemini_service = GeminiService()

    # 1. Obtener o generar idea
    if args.auto_idea:
        print("\n🎲 Generando idea automática...")
        idea = generate_automatic_idea(openai_service)
        print(f"💡 Idea generada: {idea}\n")
    elif args.idea:
        idea = args.idea
    else:
        idea = input("💡 Escribe tu idea para la historia: ").strip()
        if not idea:
            print("❌ Debes proporcionar una idea.")
            sys.exit(1)

    # 2. Seleccionar estilo
    style_name = interactive_style_selection()
    style_block = dict(STYLE_PRESETS_GEMINI)[style_name]

    # 3. Generar contenido creativo (guion + social post)
    print("\n🧠 Generando guion y contenido para redes sociales...")
    content = generate_creative_content(idea, openai_service)

    if not content:
        print("❌ Error al generar contenido.")
        sys.exit(1)

    script_text = content.get("script", "")
    social_post = content.get("social_post", "")

    print("✅ Guion generado")
    print("✅ Post para redes generado")

    # 4. Generar nombre de proyecto
    print("\n📝 Generando nombre de proyecto...")
    project_name = generate_project_name_from_idea(idea, openai_service)
    print(f"📁 Nombre del proyecto: {project_name}")

    # 5. Generar prompts visuales
    print("\n🎬 Generando prompts visuales para cada escena...")
    visual_prompts = generate_visual_prompts_for_script(script_text, openai_service)

    if not visual_prompts:
        print("❌ Error al generar prompts visuales.")
        sys.exit(1)

    print(f"✅ {len(visual_prompts)} prompts visuales generados")

    # 6. Crear directorio del proyecto
    project_dir = args.output / project_name.replace(" ", "_")
    project_dir.mkdir(parents=True, exist_ok=True)

    # Guardar archivos
    script_file = project_dir / "script.txt"
    script_file.write_text(script_text, encoding="utf-8")
    print(f"💾 Guion guardado en: {script_file}")

    social_file = project_dir / "social_post.txt"
    social_file.write_text(social_post, encoding="utf-8")
    print(f"💾 Post guardado en: {social_file}")

    prompts_file = project_dir / "visual_prompts.json"
    prompts_file.write_text(json.dumps(visual_prompts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"💾 Prompts visuales guardados en: {prompts_file}")

    metadata = {
        "idea": idea,
        "style": style_name,
        "project_name": project_name
    }
    metadata_file = project_dir / "metadata.json"
    metadata_file.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    # 7. Generar imágenes (si no es dry-run)
    if args.dry_run:
        print("\n✅ DRY-RUN: No se generaron imágenes.")
        print(f"✅ ¡Proyecto creado exitosamente en {project_dir}!")
    else:
        # Importar módulos adicionales para generación
        import re
        from src.content.consistency import (
            extract_visual_consistency_brief,
            ensure_brief_dict,
            classify_scene_for_brief,
            build_consistency_context_for_scene
        )

        print("\n🖼️  Generación de imágenes con Gemini...")

        # Preparar escenas de audio
        audio_scenes_list = re.findall(r'\[imagen:\d+\.png\]\s*(.*?)(?=\n\s*\[|$)', script_text, re.DOTALL)
        if not audio_scenes_list:
            print("❌ ERROR: No se encontraron descripciones de escenas en el guion.")
            sys.exit(1)

        if len(audio_scenes_list) != len(visual_prompts):
            print(f"⚠️ Advertencia: Número de escenas de audio ({len(audio_scenes_list)}) "
                  f"diferente a prompts visuales ({len(visual_prompts)})")

        # Detectar protagonista con marcador [PROTAGONISTA]
        character_flags = []
        cleaned_visual_prompts = []

        for p in visual_prompts:
            has_protagonist = "[PROTAGONISTA]" in p
            character_flags.append(has_protagonist)
            cleaned = p.replace("[PROTAGONISTA]", "la protagonista")
            cleaned_visual_prompts.append(cleaned)

        visual_prompts = cleaned_visual_prompts
        print(f"   🧩 Escenas con protagonista detectadas: {sum(character_flags)} de {len(character_flags)}")

        # Extraer brief de consistencia
        visual_brief_raw = extract_visual_consistency_brief(script_text, openai_service, model_type="gemini")
        visual_brief = ensure_brief_dict(visual_brief_raw)

        # Guardar brief
        try:
            brief_file = project_dir / "brief.txt"
            with open(brief_file, "w", encoding="utf-8") as f:
                f.write("PERSONAJE:\n" + (visual_brief["character"] or "(sin definir)") + "\n\n")
                f.write("ESCENARIO/UBICACIÓN:\n" + (visual_brief["environment"] or "(sin definir)") + "\n\n")
                f.write("ILUMINACIÓN/ATMÓSFERA:\n" + (visual_brief["lighting"] or "(sin definir)") + "\n\n")
                f.write("OBJETOS CLAVE:\n" + (visual_brief["objects"] or "(sin definir)") + "\n")
            print(f"   💾 Brief visual guardado en: {brief_file}")
        except Exception as e:
            print(f"   ⚠️ Advertencia: No se pudo guardar brief.txt: {e}")

        # Construir contexto por escena
        scene_contexts = []
        total_scenes = len(visual_prompts)

        for idx, audio_scene in enumerate(audio_scenes_list):
            flags = classify_scene_for_brief(audio_scene)

            # El personaje se controla por el marcador [PROTAGONISTA]
            if idx < len(character_flags) and character_flags[idx]:
                flags["include_character"] = True
            else:
                flags["include_character"] = False

            ctx = build_consistency_context_for_scene(
                visual_brief,
                include_character=flags["include_character"],
                include_environment=flags["include_environment"],
                include_objects=flags["include_objects"],
                total_scenes=total_scenes,
            )
            scene_contexts.append(ctx)

        print(f"   📖 Contextos de consistencia preparados por escena (total: {len(scene_contexts)})")

        # Generar imágenes con Gemini
        images_dir = project_dir / "images"
        images_dir.mkdir(exist_ok=True)

        success = gemini_service.generate_visuals_for_script(
            visual_prompts_list=visual_prompts,
            audio_scenes_list=audio_scenes_list,
            scene_contexts_list=scene_contexts,
            project_path=str(project_dir),
            client_openai=openai_service,
            style_block=style_block,
            overwrite=args.overwrite if hasattr(args, 'overwrite') else False,
            image_model="gemini-2.5-flash-image",
            style_slug_for_pixelize=style_name.lower()
        )

        if success:
            print(f"\n✅ ¡Proyecto creado exitosamente en {project_dir}!")
            print(f"📁 Imágenes generadas en: {images_dir}")
        else:
            print(f"\n⚠️ Proyecto creado pero hubo errores en la generación de imágenes.")
            print(f"📁 Revisa el directorio: {project_dir}")


if __name__ == "__main__":
    main()
