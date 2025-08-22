import subprocess
import os
import sys

# --- Configuración de Rutas ---
# Ruta base del proyecto (donde se ejecuta este script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ruta a la carpeta de dependencias
DEPS_DIR = os.path.join(BASE_DIR, 'dependencies')

# Ruta específica a la herramienta habbo-downloader
DOWNLOADER_DIR = os.path.join(DEPS_DIR, 'habbo-downloader')

# Carpeta de salida final para los assets (nuestra "Fuente de la Verdad")
# Usamos una subcarpeta 'raw_swf' para mantener el orden
ASSETS_DIR = os.path.join(BASE_DIR, 'habbo_assets', 'raw_swf')


def setup_downloader():
    """
    Instala las dependencias de habbo-downloader si no están presentes.
    Esto es crucial para que el pipeline sea reproducible.
    """
    node_modules_path = os.path.join(DOWNLOADER_DIR, 'node_modules')
    if not os.path.exists(node_modules_path):
        print("🔧 'habbo-downloader' no está instalado. Ejecutando 'npm install'...")
        try:
            # Ejecutamos 'npm install' dentro de la carpeta del downloader
            subprocess.run(['npm', 'install'], check=True, cwd=DOWNLOADER_DIR)
            print("✅ Instalación de 'habbo-downloader' completada.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"❌ Error instalando 'habbo-downloader': {e}")
            print("Asegúrate de tener Node.js y npm instalados y en tu PATH.")
            sys.exit(1) # Salimos del script si no podemos instalar la dependencia

def download_all_furni_swfs():
    """
    Paso 1 del pipeline: Descarga todos los archivos SWF de furnis.
    """
    print("--- Paso 1: Descargando archivos SWF de Furnis ---")
    
    # Preparamos la carpeta de salida
    os.makedirs(ASSETS_DIR, exist_ok=True)
    
    # El script principal del downloader es 'index.js'
    downloader_script = os.path.join(DOWNLOADER_DIR, 'index.js')
    
    if not os.path.exists(downloader_script):
        print(f"❌ Error: No se encuentra el script en {downloader_script}.")
        print("Asegúrate de que el submodule se haya clonado correctamente.")
        return

    try:
        print(f"📥 Ejecutando habbo-downloader para descargar en: {ASSETS_DIR}")
        
        # Construimos y ejecutamos el comando
        # Llamamos a 'node index.js' en lugar de 'hdl' para no depender de una instalación global
        command = [
            'node',
            downloader_script,
            '--command', 'furnitures', # El comando para descargar todos los furnis
            '--output', ASSETS_DIR   # Le decimos dónde guardar los archivos
        ]
        
        # cwd=DOWNLOADER_DIR es crucial para que Node encuentre los 'node_modules'
        subprocess.run(command, check=True, cwd=DOWNLOADER_DIR)
        
        print("✅ ¡Descarga de SWFs completada con éxito!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Error durante la descarga: {e}")
        print("El proceso de descarga principal falló.")
        print("ℹ️ Como alternativa, puedes intentar usar la API de https://habbofurni.com/ para descargas individuales.")
    except FileNotFoundError:
        print("❌ Error: 'node' no se encuentra. ¿Está NodeJS instalado y en tu PATH?")


if __name__ == '__main__':
    print("🚀 Iniciando el Pipeline de Assets de Habbo...")
    
    # 1. Asegurarnos de que nuestra herramienta de descarga está lista
    setup_downloader()
    
    # 2. Ejecutar la función de descarga
    download_all_furni_swfs()

    print("🏁 Pipeline finalizado.")