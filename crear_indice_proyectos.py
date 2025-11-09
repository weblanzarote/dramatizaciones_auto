import os
import re
from pathlib import Path

# --- Configuración ---

# El directorio que contiene todas las carpetas de tus proyectos
# Usar el directorio actual donde está el script
ROOT_FOLDER = Path(__file__).parent

# El archivo de salida donde se guardará el índice
OUTPUT_FILE = "_master_project_list.txt"

# --- Fin Configuración ---

def find_first_summary_line(script_path: Path) -> str:
    """Lee un texto.txt y devuelve la primera línea de contenido real."""
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

# --- NUEVA FUNCIÓN DE ORDEN ---
# Esta es una versión más simple que solo necesita el nombre.
def get_sort_key_from_name(project_name):
    """Extrae el número del nombre del proyecto para ordenar."""
    try:
        # 2. Obtiene el número (ej: "10")
        numero_str = project_name.split('_', 1)[0]
        # 3. Lo convierte a entero (10)
        return int(numero_str)
    except (ValueError, IndexError):
        # Si un proyecto no tiene número
        return 99999 

def get_sort_key(linea_proyecto):
    """Extrae el número de la línea de resumen completa para ordenar."""
    try:
        # 1. Obtiene el nombre (ej: "10_LAESPERA")
        nombre_proyecto = linea_proyecto.split(':', 1)[0]
        # 2. Usa la nueva función
        return get_sort_key_from_name(nombre_proyecto)
    except (ValueError, IndexError):
        return 99999 

def main():
    print(f"Buscando proyectos en: {ROOT_FOLDER.resolve()}")
    
    project_summaries = []
    
    # --- NUEVO: Listas para clasificar ---
    viral_projects = []
    medio_viral_projects = []
    
    # Iteramos sobre cada subcarpeta en la carpeta raíz
    for subfolder in ROOT_FOLDER.iterdir():
        if not subfolder.is_dir():
            continue # Ignora archivos sueltos

        project_name = subfolder.name

        # Filtrar solo carpetas de proyectos (que empiecen con número_)
        if not re.match(r'^\d+_', project_name):
            continue # Ignora carpetas que no son proyectos
        
        # --- NUEVO: Clasificación de proyectos ---
        if project_name.endswith("_v"):
            viral_projects.append(project_name)
        elif project_name.endswith("_mv"):
            medio_viral_projects.append(project_name)
        # --- FIN de la clasificación ---
        
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
        
        print(f"  -> Indexado: {project_name} (usando '{script_path.name}')")

    # --- NUEVO: Ordenamos las listas de virales ---
    viral_projects.sort(key=get_sort_key_from_name)
    medio_viral_projects.sort(key=get_sort_key_from_name)

    # Escribimos el archivo maestro
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("--- ÍNDICE DE PROYECTOS 'RELATOS EXTRAORDINARIOS' ---\n\n")
            f.write(f"Total de proyectos indexados: {len(project_summaries)}\n")
            f.write("-" * 50 + "\n\n")
            
            # Ordenamos numéricamente
            project_summaries.sort(key=get_sort_key)
            
            for entry in project_summaries:
                f.write(f"{entry}\n")
                
            # --- NUEVO: Escribir las secciones de virales al final ---
            
            # --- Sección Virales ---
            f.write("\n\n" + "=" * 50 + "\n")
            f.write(f"--- 🔥 TOTAL PROYECTOS VIRALES (_v): {len(viral_projects)} ---\n")
            f.write("=" * 50 + "\n\n")
            
            for name in viral_projects:
                f.write(f"{name}\n")
                
            # --- Sección Medio Virales ---
            f.write("\n\n" + "=" * 50 + "\n")
            f.write(f"--- 🌪️ TOTAL PROYECTOS MEDIO VIRALES (_mv): {len(medio_viral_projects)} ---\n")
            f.write("=" * 50 + "\n\n")
            
            for name in medio_viral_projects:
                f.write(f"{name}\n")
            
            # --- FIN de la nueva sección ---
                
    except Exception as e:
        print(f"\nError fatal al escribir el archivo de salida '{OUTPUT_FILE}': {e}")
        return

    print("\n" + "=" * 50)
    print(f"¡Éxito! Se ha creado el índice en: {OUTPUT_FILE}")
    print(f"Se han indexado {len(project_summaries)} proyectos.")
    print(f"Se encontraron {len(viral_projects)} virales y {len(medio_viral_projects)} medio virales.")
    print("=" * 50)

if __name__ == "__main__":
    main()