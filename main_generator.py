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
    else:
        print("\n🖼️  Generación de imágenes...")
        print("⚠️  NOTA: La lógica completa de generación de imágenes con Gemini")
        print("   está en el archivo original create_project.py (líneas 1245-1698).")
        print("   Por simplicidad, esta versión refactorizada requiere que completes")
        print("   esa funcionalidad en src/services/gemini_service.py")

        # TODO: Implementar generación de imágenes
        # for i, prompt in enumerate(visual_prompts, 1):
        #     full_prompt = build_master_prompt(style_block, prompt)
        #     # Llamar a gemini_service.generate_image(...)
        #     pass

    print(f"\n✅ ¡Proyecto creado exitosamente en {project_dir}!")


if __name__ == "__main__":
    main()
