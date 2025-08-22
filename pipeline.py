import subprocess
import sys
import shutil
import os
import argparse
from pathlib import Path

# --- 1. CONFIGURACIÓN DE RUTAS ---
PROJECT_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_ROOT / "assets"
DOWNLOADER_DIR = PROJECT_ROOT / "dependencies" / "habbo-asset-downloader"
DOWNLOADER_SCRIPT = DOWNLOADER_DIR / "src" / "index.js"
FURNITURES_DOWNLOAD_DIR = ASSETS_DIR / "furnitures"
GAMEDATA_DOWNLOAD_DIR = ASSETS_DIR / "gamedata"
EXTRACTOR_PROJECT_DIR = PROJECT_ROOT / "dependencies" / "Habbo-SWF-Furni-Extractor"
EXTRACTED_DATA_FINAL_DIR = ASSETS_DIR / "extracted"

def _reorganize_output(output_path: Path, expected_source_subdir: str):
    source_dir = output_path / expected_source_subdir
    if not source_dir.is_dir():
        print(f"AVISO: No se encontró la subcarpeta esperada en '{source_dir}'. Saltando reorganización.")
        return
    print(f"Reorganizando: Moviendo contenido desde '{source_dir}' hacia '{output_path}'")
    for item in source_dir.iterdir():
        destination_item = output_path / item.name
        if destination_item.exists():
            print(f"Destino '{destination_item.name}' ya existe. Sobrescribiendo...")
            if destination_item.is_dir():
                shutil.rmtree(destination_item)
            else:
                destination_item.unlink()
        try:
            shutil.move(str(item), str(output_path))
        except shutil.Error as e:
            print(f"AVISO: No se pudo mover '{item}'. Error: {e}")
    try:
        shutil.rmtree(output_path / expected_source_subdir.split('/')[0].split('\\')[0])
        print("Estructura de carpetas anidada eliminada con éxito.")
    except OSError as e:
        print(f"Error al limpiar carpetas anidadas: {e}")

def run_step_1_download():
    print("\n--- [Step 1] Iniciando descarga de activos ---")
    if FURNITURES_DOWNLOAD_DIR.exists():
        print(f"Limpiando directorio de descarga de furnis anterior: '{FURNITURES_DOWNLOAD_DIR}'")
        shutil.rmtree(FURNITURES_DOWNLOAD_DIR)
    if GAMEDATA_DOWNLOAD_DIR.exists():
        print(f"Limpiando directorio de descarga de gamedata anterior: '{GAMEDATA_DOWNLOAD_DIR}'")
        shutil.rmtree(GAMEDATA_DOWNLOAD_DIR)
    run_downloader(command="furnitures", output_path=FURNITURES_DOWNLOAD_DIR, reorganize_from="dcr/hof_furni")
    run_downloader(command="gamedata", output_path=GAMEDATA_DOWNLOAD_DIR, reorganize_from="gamedata")

def run_downloader(command: str, output_path: Path, reorganize_from: str = None):
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"\nDescargando: {command}...")
    cmd_list = ["node", str(DOWNLOADER_SCRIPT), "-c", command, "-o", str(output_path)]
    try:
        with subprocess.Popen(
            cmd_list, cwd=DOWNLOADER_DIR, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1
        ) as process:
            for line in process.stdout:
                print(line, end='')
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, process.args)
        if reorganize_from:
            _reorganize_output(output_path, reorganize_from)
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"\nERROR durante la descarga de '{command}': {e}")
        sys.exit(1)

def run_step_2_extract():
    """Ejecuta el extractor de .NET para descomprimir los archivos SWF (Step 2)."""
    print("\n--- [Step 2] Iniciando descompresión de archivos SWF ---")

    if not FURNITURES_DOWNLOAD_DIR.is_dir():
        print(f"ERROR: La carpeta de entrada '{FURNITURES_DOWNLOAD_DIR}' no existe. Ejecuta el Step 1 primero.")
        sys.exit(1)

    if EXTRACTED_DATA_FINAL_DIR.exists():
        print(f"Limpiando directorio de salida anterior: '{EXTRACTED_DATA_FINAL_DIR}'")
        shutil.rmtree(EXTRACTED_DATA_FINAL_DIR)
    
    EXTRACTED_DATA_FINAL_DIR.mkdir(parents=True, exist_ok=True)

    print("Ejecutando el extractor de .NET... (esto puede tardar varios minutos)")
    
    # --- CAMBIO IMPORTANTE AQUÍ ---
    # Añadimos el separador '--' para pasar los argumentos a la aplicación
    cmd_list = [
        "dotnet", "run",
        "--project", "SimpleExtractor.csproj",
        "--", # <--- ESTE ES EL CAMBIO CLAVE
        "-i", str(FURNITURES_DOWNLOAD_DIR),
        "-o", str(EXTRACTED_DATA_FINAL_DIR)
    ]

    # --- AÑADIMOS PRINTS DE DEPURACIÓN ---
    print("-" * 50)
    print("Información de ejecución del Extractor:")
    print(f"  Directorio de trabajo: {EXTRACTOR_PROJECT_DIR}")
    print(f"  Comando a ejecutar: {' '.join(cmd_list)}")
    print("-" * 50)

    try:
        with subprocess.Popen(
            cmd_list,
            cwd=EXTRACTOR_PROJECT_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            bufsize=1
        ) as process:
            for line in process.stdout:
                print(line, end='')
        
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, process.args)

        print("\n--- Extracción completada con éxito. ---")
    
    except FileNotFoundError:
        print("ERROR: El comando 'dotnet' no fue encontrado. Asegúrate de que .NET SDK está instalado.")
        sys.exit(1)
    except subprocess.CalledProcessError:
        print(f"\nERROR: El extractor de .NET falló.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Pipeline de orquestación para activos de Habbo.")
    parser.add_argument(
        '--start-at',
        type=int,
        default=1,
        help='El número del paso por el cual empezar el pipeline (ej: 2 para saltar la descarga).'
    )
    args = parser.parse_args()
    
    print("==========================================")
    print("=      INICIO DEL PIPELINE DE ACTIVOS    =")
    print(f"=      Empezando desde el paso: {args.start_at}      =")
    print("==========================================")

    if args.start_at <= 1:
        run_step_1_download()
    
    if args.start_at <= 2:
        run_step_2_extract()

    print("\n==========================================")
    print("=      PIPELINE COMPLETADO CON ÉXITO     =")
    print("==========================================")

if __name__ == "__main__":
    main()