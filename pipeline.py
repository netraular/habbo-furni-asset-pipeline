import subprocess
import sys
import shutil
from pathlib import Path

# --- 1. CONFIGURACIÓN DE RUTAS ---
PROJECT_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_ROOT / "assets"
DOWNLOADER_DIR = PROJECT_ROOT / "dependencies" / "habbo-asset-downloader"
DOWNLOADER_SCRIPT = DOWNLOADER_DIR / "src" / "index.js"

def _reorganize_output(output_path: Path, expected_source_subdir: str):
    """
    Mueve el contenido de una subcarpeta anidada a la raíz del directorio de salida
    y limpia las carpetas vacías restantes.
    
    Ejemplo: si la descarga crea 'assets/furnitures/dcr/hof_furni', esta función
    moverá el contenido de 'hof_furni' a 'assets/furnitures' y eliminará 'dcr'.
    """
    source_dir = output_path / expected_source_subdir
    
    if not source_dir.is_dir():
        print(f"AVISO: No se encontró la subcarpeta esperada en '{source_dir}'. Saltando reorganización.")
        return

    print(f"Reorganizando: Moviendo contenido desde '{source_dir}' hacia '{output_path}'")
    
    # Mover cada archivo/carpeta desde la fuente al destino
    for item in source_dir.iterdir():
        # shutil.move es potente, mueve archivos y carpetas enteras.
        # Si el destino ya existe, puede dar error, por eso es bueno
        # asegurarse de que el directorio de salida esté limpio si se re-ejecuta.
        try:
            shutil.move(str(item), str(output_path))
        except shutil.Error as e:
            print(f"AVISO: No se pudo mover '{item}'. Puede que ya exista. Error: {e}")

    # Limpiar la estructura de carpetas vacía que quedó atrás
    # shutil.rmtree elimina un directorio y todo su contenido.
    # Aquí lo usamos en la raíz de la estructura anidada.
    try:
        shutil.rmtree(output_path / expected_source_subdir.split('/')[0].split('\\')[0])
        print("Estructura de carpetas anidada eliminada con éxito.")
    except OSError as e:
        print(f"Error al limpiar carpetas anidadas: {e}")


def run_downloader(command: str, output_subdir: str, reorganize_from: str = None):
    """
    Ejecuta el downloader y opcionalmente reorganiza la salida.
    
    Args:
        command (str): El comando a ejecutar (ej: 'furnitures').
        output_subdir (str): La subcarpeta dentro de 'assets' donde guardar los archivos.
        reorganize_from (str, optional): La ruta anidada desde la que mover el contenido.
                                          Usa '/' como separador. Ejemplo: 'dcr/hof_furni'.
    """
    output_path = ASSETS_DIR / output_subdir
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n--- Iniciando descarga de: {command} ---")
    print(f"Directorio de salida temporal: {output_path}")

    cmd_list = ["node", str(DOWNLOADER_SCRIPT), "-c", command, "-o", str(output_path)]

    try:
        # Ejecutamos el subproceso, pero esta vez mostraremos la salida en tiempo real
        # que es más útil para descargas largas.
        with subprocess.Popen(
            cmd_list,
            cwd=DOWNLOADER_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Redirige stderr a stdout
            text=True,
            encoding='utf-8',
            bufsize=1 # Line-buffered
        ) as process:
            for line in process.stdout:
                print(line, end='') # Muestra la salida del downloader en tiempo real
        
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, process.args)

        print(f"--- Descarga de {command} completada. ---")
        
        # --- PASO DE REORGANIZACIÓN ---
        if reorganize_from:
            _reorganize_output(output_path, reorganize_from)

    except FileNotFoundError:
        print("ERROR: El comando 'node' no fue encontrado.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"\nERROR: El downloader falló al ejecutar el comando '{command}'. Código de salida: {e.returncode}")
        sys.exit(1)

def main():
    """Función principal que orquesta todas las tareas."""
    print("==========================================")
    print("=      INICIO DEL PIPELINE DE ACTIVOS    =")
    print("==========================================")

    # Tarea 1: Descargar el gamedata y reorganizar la estructura.
    run_downloader(
        command="gamedata", 
        output_subdir="gamedata",
        reorganize_from="gamedata"  # <-- La ruta anidada que crea el downloader
    )

    # Tarea 2 Descargar los SWF de los furnis y reorganizar la estructura.
    run_downloader(
        command="furnitures", 
        output_subdir="furnitures", 
        reorganize_from="dcr/hof_furni"  # <-- La ruta anidada que crea el downloader
    )

    
    print("\n==========================================")
    print("=      PIPELINE COMPLETADO CON ÉXITO     =")
    print("==========================================")


if __name__ == "__main__":
    main()