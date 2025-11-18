"""
Indexador de proyectos anteriores para generar ideas basadas en patrones virales.

Genera dos archivos:
- _master_project_list.txt: Índice completo de todos los proyectos
- _master_project_top.txt: Índice curado solo con virales y medio virales
"""
import os
import re
from pathlib import Path


def find_first_summary_line(script_path: Path) -> str:
    """
    Lee un texto.txt y devuelve la primera línea de contenido real.

    Args:
        script_path: Ruta al archivo de texto

    Returns:
        Primera línea de contenido (sin etiquetas de speaker/imagen)
    """
    try:
        with script_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # Ignora líneas vacías o etiquetas de speaker/imagen
                if not line:
                    continue
                if line.startswith("[") and line.endswith("]"):
                    continue

                # Encontramos la primera línea de contenido
                return line
    except Exception as e:
        return f"ERROR al leer el archivo: {e}"

    return "No se encontró texto de resumen."


def get_sort_key_from_name(project_name: str) -> int:
    """
    Extrae el número del nombre del proyecto para ordenar.

    Args:
        project_name: Nombre del proyecto (ej: "10_LAESPERA")

    Returns:
        Número del proyecto para ordenar
    """
    try:
        # Obtiene el número (ej: "10")
        numero_str = project_name.split('_', 1)[0]
        # Lo convierte a entero (10)
        return int(numero_str)
    except (ValueError, IndexError):
        # Si un proyecto no tiene número
        return 99999


def get_sort_key(linea_proyecto: str) -> int:
    """
    Extrae el número de la línea de resumen completa para ordenar.

    Args:
        linea_proyecto: Línea con formato "10_LAESPERA: resumen..."

    Returns:
        Número del proyecto para ordenar
    """
    try:
        # Obtiene el nombre (ej: "10_LAESPERA")
        nombre_proyecto = linea_proyecto.split(':', 1)[0]
        # Usa la función auxiliar
        return get_sort_key_from_name(nombre_proyecto)
    except (ValueError, IndexError):
        return 99999


def index_projects(projects_dir: Path = None, root_dir: Path = None) -> tuple[str, str]:
    """
    Indexa todos los proyectos en la carpeta especificada.

    Args:
        projects_dir: Carpeta que contiene los proyectos (default: proyectos/)
        root_dir: Directorio raíz donde guardar los archivos (default: directorio actual)

    Returns:
        Tupla con (master_list_path, top_list_path)
    """
    # Defaults
    if root_dir is None:
        root_dir = Path.cwd()

    if projects_dir is None:
        projects_dir = root_dir / "proyectos"

    # Archivos de salida
    output_file = root_dir / "_master_project_list.txt"
    top_output_file = root_dir / "_master_project_top.txt"

    print(f"📁 Buscando proyectos en: {projects_dir.resolve()}")

    if not projects_dir.exists():
        print(f"⚠️ La carpeta {projects_dir} no existe.")
        print(f"   Crea la carpeta 'proyectos/' y coloca tus proyectos anteriores ahí.")
        print(f"   Estructura: proyectos/10_PROYECTO/texto.txt")
        return None, None

    project_summaries = []
    summary_dict = {}  # Para poder recuperar el resumen por nombre

    # Listas para clasificar
    viral_projects = []
    medio_viral_projects = []

    # Iteramos sobre cada subcarpeta en la carpeta de proyectos
    for subfolder in projects_dir.iterdir():
        if not subfolder.is_dir():
            continue  # Ignora archivos sueltos

        project_name = subfolder.name

        # Filtrar solo carpetas de proyectos (que empiecen con número_)
        if not re.match(r'^\d+_', project_name):
            continue  # Ignora carpetas que no son proyectos

        # Clasificación de proyectos
        if project_name.endswith("_v"):
            viral_projects.append(project_name)
        elif project_name.endswith("_mv"):
            medio_viral_projects.append(project_name)

        script_path = None
        try:
            script_path = next(subfolder.glob("texto*.txt"))
        except StopIteration:
            pass

        if not script_path or not script_path.exists():
            print(f"  -> AVISO: No se encontró 'texto*.txt' en '{project_name}'")
            continue

        summary = find_first_summary_line(script_path)
        entry = f"{project_name}: {summary}"
        project_summaries.append(entry)
        summary_dict[project_name] = summary  # Guardamos el resumen asociado

        print(f"  -> Indexado: {project_name} (usando '{script_path.name}')")

    # Ordenamos las listas de virales
    viral_projects.sort(key=get_sort_key_from_name)
    medio_viral_projects.sort(key=get_sort_key_from_name)

    # ------------------------------------------------------------------
    # 1) Escribimos el archivo maestro COMPLETO
    # ------------------------------------------------------------------
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("--- ÍNDICE DE PROYECTOS 'RELATOS EXTRAORDINARIOS' ---\n\n")
            f.write(f"Total de proyectos indexados: {len(project_summaries)}\n")
            f.write("-" * 50 + "\n")
            f.write(
                "\nNOTA PARA IA:\n"
                "Para generar nuevas ideas automáticas es más recomendable usar el archivo "
                f"'{top_output_file.name}', que contiene solo los proyectos más relevantes "
                "(virales y medio virales) en formato compacto.\n"
            )
            f.write("-" * 50 + "\n\n")

            # Ordenamos numéricamente todas las entradas
            project_summaries.sort(key=get_sort_key)

            for entry in project_summaries:
                f.write(f"{entry}\n")

            # Sección Virales
            f.write("\n\n" + "=" * 50 + "\n")
            f.write(f"--- 🔥 TOTAL PROYECTOS VIRALES (_v): {len(viral_projects)} ---\n")
            f.write("=" * 50 + "\n\n")

            for name in viral_projects:
                f.write(f"{name}\n")

            # Sección Medio Virales
            f.write("\n\n" + "=" * 50 + "\n")
            f.write(f"--- 🌪️ TOTAL PROYECTOS MEDIO VIRALES (_mv): {len(medio_viral_projects)} ---\n")
            f.write("=" * 50 + "\n\n")

            for name in medio_viral_projects:
                f.write(f"{name}\n")

    except Exception as e:
        print(f"\n❌ Error al escribir el archivo '{output_file}': {e}")
        return None, None

    # ------------------------------------------------------------------
    # 2) Escribimos el archivo "TOP" CURADO solo para la IA
    # ------------------------------------------------------------------
    try:
        with open(top_output_file, "w", encoding="utf-8") as f:
            f.write("--- ÍNDICE CURADO PARA IA: PROYECTOS VIRALES Y MEDIO VIRALES ---\n\n")
            f.write(
                "Este archivo está pensado específicamente para que los modelos de IA generen "
                "nuevas ideas basadas en los patrones de los proyectos más exitosos.\n\n"
            )

            f.write("=" * 50 + "\n")
            f.write(f"🔥 PROYECTOS VIRALES (_v): {len(viral_projects)}\n")
            f.write("=" * 50 + "\n\n")

            for name in viral_projects:
                resumen = summary_dict.get(name, "(sin resumen)")
                f.write(f"{name}: {resumen}\n")

            f.write("\n" + "=" * 50 + "\n")
            f.write(f"🌪️ PROYECTOS MEDIO VIRALES (_mv): {len(medio_viral_projects)}\n")
            f.write("=" * 50 + "\n\n")

            for name in medio_viral_projects:
                resumen = summary_dict.get(name, "(sin resumen)")
                f.write(f"{name}: {resumen}\n")

    except Exception as e:
        print(f"\n❌ Error al escribir el archivo curado '{top_output_file}': {e}")
        return None, None

    print("\n" + "=" * 50)
    print(f"✅ Índice completo creado en: {output_file}")
    print(f"✅ Índice curado para IA creado en: {top_output_file}")
    print(f"📊 Indexados {len(project_summaries)} proyectos")
    print(f"🔥 Virales: {len(viral_projects)} | 🌪️ Medio virales: {len(medio_viral_projects)}")
    print("=" * 50)

    return str(output_file), str(top_output_file)


def get_next_project_number(master_list_path: Path = None) -> int:
    """
    Lee el master list y determina el siguiente número de proyecto.

    Args:
        master_list_path: Ruta al _master_project_list.txt

    Returns:
        Siguiente número de proyecto
    """
    if master_list_path is None:
        master_list_path = Path.cwd() / "_master_project_list.txt"

    if not master_list_path.exists():
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
