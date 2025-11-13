#!/usr/bin/env python3
"""
Script de prueba para verificar la configuración de API keys.
Ejecuta esto antes de usar create_project.py para asegurar que todo está bien configurado.
"""

import os
from dotenv import load_dotenv

def test_api_keys():
    """Verifica que todas las API keys necesarias están configuradas."""
    print("="*70)
    print("🔍 VERIFICACIÓN DE CONFIGURACIÓN DE API KEYS")
    print("="*70 + "\n")

    load_dotenv()

    all_ok = True

    # Test OpenAI
    print("1️⃣ OpenAI API Key (para generación de texto):")
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key.startswith("sk-"):
        print(f"   ✅ Configurada: {openai_key[:10]}...{openai_key[-4:]}")
    else:
        print("   ❌ NO configurada o formato incorrecto")
        print("      Debe empezar con 'sk-'")
        all_ok = False

    print()

    # Test Gemini
    print("2️⃣ Google Gemini API Key (para generación de imágenes):")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key and len(gemini_key) > 20:
        print(f"   ✅ Configurada: {gemini_key[:10]}...{gemini_key[-4:]}")
    else:
        print("   ❌ NO configurada")
        print("      Obtén tu key en: https://aistudio.google.com/apikey")
        all_ok = False

    print()

    # Test Replicate (opcional)
    print("3️⃣ Replicate API Token (opcional, para --animate-images):")
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if replicate_token:
        print(f"   ✅ Configurada: {replicate_token[:10]}...{replicate_token[-4:]}")
    else:
        print("   ⚠️  No configurada (es opcional)")
        print("      Solo necesaria si usas --animate-images")

    print()
    print("="*70)

    if all_ok:
        print("✅ TODAS LAS API KEYS NECESARIAS ESTÁN CONFIGURADAS")
        print()
        print("🚀 Puedes ejecutar:")
        print("   python create_project.py")
        print()
        return True
    else:
        print("❌ FALTAN API KEYS OBLIGATORIAS")
        print()
        print("📝 Pasos para configurar:")
        print("   1. Copia .env.example a .env:")
        print("      cp .env.example .env")
        print()
        print("   2. Edita .env y añade tus keys:")
        print("      - OPENAI_API_KEY desde https://platform.openai.com/api-keys")
        print("      - GEMINI_API_KEY desde https://aistudio.google.com/apikey")
        print()
        print("   3. Vuelve a ejecutar este script para verificar")
        print()
        return False

def test_imports():
    """Verifica que todas las dependencias están instaladas."""
    print("="*70)
    print("📦 VERIFICACIÓN DE DEPENDENCIAS")
    print("="*70 + "\n")

    required_modules = [
        ("openai", "OpenAI"),
        ("google.genai", "Google Gemini"),
        ("requests", "Requests"),
        ("PIL", "Pillow"),
        ("dotenv", "python-dotenv"),
    ]

    optional_modules = [
        ("replicate", "Replicate"),
    ]

    all_ok = True

    print("Módulos obligatorios:")
    for module_name, display_name in required_modules:
        try:
            __import__(module_name)
            print(f"   ✅ {display_name}")
        except ImportError:
            print(f"   ❌ {display_name} - NO INSTALADO")
            all_ok = False

    print("\nMódulos opcionales:")
    for module_name, display_name in optional_modules:
        try:
            __import__(module_name)
            print(f"   ✅ {display_name}")
        except ImportError:
            print(f"   ⚠️  {display_name} - no instalado (opcional)")

    print()

    if all_ok:
        print("✅ Todas las dependencias obligatorias están instaladas\n")
        return True
    else:
        print("❌ Faltan dependencias obligatorias")
        print("\n💡 Ejecuta: pip install -r requirements.txt\n")
        return False

if __name__ == "__main__":
    print("\n")

    # Verificar imports
    imports_ok = test_imports()

    print()

    # Verificar API keys
    keys_ok = test_api_keys()

    print("="*70)
    if imports_ok and keys_ok:
        print("🎉 ¡TODO LISTO! Puedes empezar a usar el proyecto.")
    else:
        print("⚠️  Por favor, completa la configuración antes de continuar.")
    print("="*70 + "\n")
