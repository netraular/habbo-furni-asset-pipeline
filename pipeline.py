import subprocess
import sys
import shutil
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# --- Cargar variables de entorno desde .env ---
load_dotenv()

# --- 1. CONFIGURACIÓN DE RUTAS Y SECRETOS ---
PROJECT_ROOT = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_ROOT / "assets"
# Dependencias
DOWNLOADER_DIR = PROJECT_ROOT / "dependencies" / "habbo-asset-downloader"
DOWNLOADER_SCRIPT = DOWNLOADER_DIR / "src" / "index.js"
EXTRACTOR_PROJECT_DIR = PROJECT_ROOT / "dependencies" / "Habbo-SWF-Furni-Extractor"
METADATA_DOWNLOADER_DIR = PROJECT_ROOT / "dependencies" / "habbo-furni-data-downloader"
# Rutas de los Pasos
FURNITURES_DOWNLOAD_DIR = ASSETS_DIR / "furnitures"
GAMEDATA_DOWNLOAD_DIR = ASSETS_DIR / "gamedata"
EXTRACTED_DATA_FINAL_DIR = ASSETS_DIR / "extracted"
METADATA_RAW_DIR = ASSETS_DIR / "metadata_raw"
METADATA_PROCESSED_DIR = ASSETS_DIR / "metadata_processed"

# Cargar el Token desde las variables de entorno
HABBOFURNI_API_TOKEN = os.getenv("HABBOFURNI_API_TOKEN")

# --- Añadir el submodule al path de Python para poder importarlo ---
sys.path.append(str(METADATA_DOWNLOADER_DIR))
try:
    from download_furni_data import download_furni_by_hotel, HOTELS
    from process_furni import process_and_save_furni
except ImportError as e:
    print(f"Error importando los scripts del submodule: {e}")
    print("Asegúrate de que el submodule está en la ruta correcta y los archivos .py existen.")
    sys.exit(1)


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
    print("\n--- [Step 2] Iniciando descompresión y renderizado de SWF ---")
    if not FURNITURES_DOWNLOAD_DIR.is_dir():
        print(f"ERROR: La carpeta de entrada '{FURNITURES_DOWNLOAD_DIR}' no existe. Ejecuta el Step 1 primero.")
        sys.exit(1)
    if EXTRACTED_DATA_FINAL_DIR.exists():
        print(f"Limpiando directorio de salida anterior: '{EXTRACTED_DATA_FINAL_DIR}'")
        shutil.rmtree(EXTRACTED_DATA_FINAL_DIR)
    EXTRACTED_DATA_FINAL_DIR.mkdir(parents=True, exist_ok=True)
    print("Ejecutando el extractor de .NET... (esto puede tardar varios minutos)")
    cmd_list = [
        "dotnet", "run", "--project", "SimpleExtractor.csproj", "--",
        "-i", str(FURNITURES_DOWNLOAD_DIR), "-o", str(EXTRACTED_DATA_FINAL_DIR)
    ]
    print("-" * 50)
    print("Información de ejecución del Extractor:")
    print(f"  Directorio de trabajo: {EXTRACTOR_PROJECT_DIR}")
    print(f"  Comando a ejecutar: {' '.join(cmd_list)}")
    print("-" * 50)
    try:
        with subprocess.Popen(
            cmd_list, cwd=EXTRACTOR_PROJECT_DIR, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=True, encoding='utf-8', bufsize=1
        ) as process:
            for line in process.stdout:
                print(line, end='')
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, process.args)
        print("\n--- Extracción completada con éxito. ---")
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        print(f"\nERROR: El extractor de .NET falló: {e}")
        sys.exit(1)

def run_step_3_fetch_metadata():
    """
    Descarga y procesa metadatos (en formato JSON) desde la API de HabboFurni.com.
    Este paso NO descarga los archivos SWF o iconos, ya que eso se gestiona en los pasos 1 y 2.
    """
    print("\n--- [Step 3] Iniciando descarga y procesamiento de metadata desde API ---")

    if not HABBOFURNI_API_TOKEN:
        print("❌ ERROR: La variable de entorno 'HABBOFURNI_API_TOKEN' no está configurada.")
        print("Por favor, crea un archivo .env en la raíz del proyecto y añade tu token.")
        sys.exit(1)
    
    # 1. Limpieza de directorios antiguos
    if METADATA_RAW_DIR.exists():
        print(f"Limpiando directorio de metadatos brutos anterior: '{METADATA_RAW_DIR}'")
        shutil.rmtree(METADATA_RAW_DIR)
    if METADATA_PROCESSED_DIR.exists():
        print(f"Limpiando directorio de metadatos procesados anterior: '{METADATA_PROCESSED_DIR}'")
        shutil.rmtree(METADATA_PROCESSED_DIR)
    METADATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # 2. Descarga de datos brutos de la API
    print(f"\nDescargando datos de Habbo.com... (Salida: '{METADATA_RAW_DIR}')")
    hotel_com = next((h for h in HOTELS if h["short_name"] == "COM"), None)
    if not download_furni_by_hotel(hotel_com, HABBOFURNI_API_TOKEN, METADATA_RAW_DIR):
        print("Fallo al descargar datos de Habbo.com. Abortando.")
        sys.exit(1)
    
    print(f"\nDescargando datos de Habbo.es... (Salida: '{METADATA_RAW_DIR}')")
    hotel_es = next((h for h in HOTELS if h["short_name"] == "ES"), None)
    if not download_furni_by_hotel(hotel_es, HABBOFURNI_API_TOKEN, METADATA_RAW_DIR):
        print("Fallo al descargar datos de Habbo.es. Abortando.")
        sys.exit(1)

    # 3. Procesamiento y fusión de los datos descargados
    print(f"\nProcesando y fusionando los datos descargados... (Salida: '{METADATA_PROCESSED_DIR}')")
    if not process_and_save_furni(METADATA_RAW_DIR, METADATA_PROCESSED_DIR):
        print("Fallo al procesar los metadatos. Abortando.")
        sys.exit(1)
    
    print("\n--- Metadata descargada y procesada con éxito. ---")

def main():
    parser = argparse.ArgumentParser(description="Pipeline de orquestación para activos de Habbo.")
    parser.add_argument(
        '--start-at', type=int, default=1, choices=[1, 2, 3],
        help='El número del paso por el cual empezar el pipeline (1: Descarga, 2: Extracción, 3: Metadata).'
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
        
    if args.start_at <= 3:
        run_step_3_fetch_metadata()

    print("\n==========================================")
    print("=      PIPELINE COMPLETADO CON ÉXITO     =")
    print("==========================================")

if __name__ == "__main__":
    main()