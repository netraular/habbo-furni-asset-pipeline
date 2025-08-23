# scripts/merge_furni_data.py (VERSIÓN FINAL "ASSET-DRIVEN")
import os
import json
import traceback
from pathlib import Path
from multiprocessing import Pool, cpu_count
from collections import defaultdict
from tqdm import tqdm

EDITOR_ROTATION_MAP = [2, 4, 6, 0]

def index_metadata_files(metadata_dir: Path) -> dict:
    """Crea un índice rápido que mapea el nombre de la carpeta de metadatos a su ruta."""
    print("Indexando archivos de metadatos...")
    metadata_index = {}
    metadata_folders = [d for d in metadata_dir.iterdir() if d.is_dir()]
    for folder in tqdm(metadata_folders, desc="Indexando"):
        meta_file = folder / "data.json"
        if meta_file.exists():
            metadata_index[folder.name] = meta_file
    print(f"Indexación completa. Se encontraron {len(metadata_index)} archivos de metadatos únicos.")
    return metadata_index

def get_color_ids_from_furni_json(furni_json_path: Path) -> list:
    """Extrae la lista de IDs de color disponibles desde el furni.json."""
    if not furni_json_path.exists():
        return ['0'] # Si no hay furni.json, asumimos una sola variante sin color.
    
    with open(furni_json_path, 'r') as f:
        data = json.load(f)
    
    try:
        # Intentar obtener colores de la visualización más común (64)
        vis = data.get('visualization', {}).get('64', {})
        if not vis: # Si no, probar con 32
            vis = data.get('visualization', {}).get('32', {})
        if not vis: # Si no, probar con la primera que encuentre
             vis_keys = list(data.get('visualization', {}).keys())
             if vis_keys:
                vis = data['visualization'][vis_keys[0]]

        colors = vis.get('colors', {})
        if colors:
            return sorted(colors.keys(), key=int) # Devuelve IDs de color ordenados
    except (KeyError, AttributeError):
        pass
        
    return ['0'] # Fallback si no se encuentran colores

def process_single_furni(base_dir: Path, metadata_index: dict, project_root: Path, final_data_dir: Path):
    classname = base_dir.name
    
    try:
        # --- LÓGICA "ASSET-DRIVEN" ---
        render_data_path = base_dir / "renderdata.json"
        furni_json_path = base_dir / "furni.json"
        rendered_dir = base_dir / "rendered"

        if not render_data_path.exists() or not rendered_dir.is_dir() or not any(rendered_dir.glob("*_no_sd.png")):
            return ("skipped_no_renders", classname)

        # 1. Obtener la lista de variantes de color desde el propio furni
        color_ids = get_color_ids_from_furni_json(furni_json_path)
        
        with open(render_data_path, 'r') as f:
            render_data = json.load(f)

        merged_furni_data = {"variants": {}}
        is_first_variant = True

        # 2. Iterar sobre las variantes definidas y buscar sus metadatos
        for color_id in color_ids:
            # Construir el nombre de la carpeta de metadatos que esperamos encontrar
            # Ej: 'rare_dragonlamp' y color '0' -> 'rare_dragonlamp_0'
            # Ej: 'table' y color '0' -> 'table' (sin color)
            # Ej: 'ads_711' y color '1' -> 'ads_711_1'
            metadata_key = classname if color_id == '0' and classname not in metadata_index else f"{classname}_{color_id}"
            if metadata_key not in metadata_index:
                 # Si no existe (ej. rare_dragonlamp_0), prueba sin el _0 (ej. rare_dragonlamp)
                 if color_id == '0':
                    metadata_key = classname
                 else:
                    continue # Si no es color 0 y no se encuentra, saltar esta variante
            
            meta_file_path = metadata_index.get(metadata_key)
            if not meta_file_path:
                continue

            with open(meta_file_path, 'r', encoding='utf-8') as f:
                variant_meta = json.load(f).get("hotelData", {})
            if not variant_meta:
                continue
            
            # 3. Si es la primera variante válida, usar sus datos para el objeto base
            if is_first_variant:
                base_id_from_api = (variant_meta.get("classname") or classname).split('*')[0]
                merged_furni_data.update({
                    "base_id": base_id_from_api,
                    "name": variant_meta.get('name', classname),
                    "description": variant_meta.get('description', ''),
                    "dimensions": {"x": variant_meta.get('xdim', 1), "y": variant_meta.get('ydim', 1)},
                    "category": variant_meta.get('category', 'unknown'),
                    "furni_line": variant_meta.get('furni_line', 'unknown'),
                })
                is_first_variant = False

            # 4. Construir la entrada de la variante (lógica similar a la anterior)
            api_classname = variant_meta.get("classname") or classname
            
            icon_with_color_path = base_dir / f"{classname}_icon_{color_id}.png"
            icon_generic_path = base_dir / f"{classname}_icon.png"
            final_icon_path_obj = icon_with_color_path if icon_with_color_path.exists() else icon_generic_path

            variant_entry = {
                "id": f"{merged_furni_data['base_id']}_{color_id}" if color_id != "0" else merged_furni_data['base_id'],
                "name": variant_meta.get("name") or api_classname,
                "icon_path": f"2_extracted_swf_data/{classname}/{final_icon_path_obj.name}",
                "renders": {}
            }
            
            for rot_idx, direction in enumerate(EDITOR_ROTATION_MAP):
                render_key = f"{classname}_dir_{direction}_{color_id}_no_sd"
                if render_key not in render_data:
                    render_key = f"{classname}_dir_{direction}_no_sd"
                
                if render_key in render_data:
                    offset = render_data[render_key]
                    image_path_str = f"2_extracted_swf_data/{classname}/rendered/{render_key}.png"
                    if (project_root / "assets" / image_path_str).exists():
                        variant_entry["renders"][str(rot_idx)] = {
                            "path": image_path_str.replace(os.sep, '/'),
                            "offset": {"x": offset["X"], "y": offset["Y"]}
                        }

            if variant_entry["renders"]:
                merged_furni_data["variants"][color_id] = variant_entry

        # 5. Guardar solo si se encontró al menos una variante válida
        if merged_furni_data["variants"]:
            output_dir = final_data_dir / merged_furni_data['base_id']
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / "data.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(merged_furni_data, f, indent=2)
            return ("processed", classname)
        else:
            return ("skipped_no_valid_variants", classname)
            
    except Exception:
        return ("error", classname, traceback.format_exc())


def process_all_furnis():
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    EXTRACTED_DIR = PROJECT_ROOT / "assets" / "2_extracted_swf_data"
    METADATA_DIR = PROJECT_ROOT / "assets" / "3_metadata_processed_api"
    FINAL_DATA_DIR = PROJECT_ROOT / "assets" / "4_final_furni_data"

    print(f"Iniciando fusión de datos hacia '{FINAL_DATA_DIR}'...")
    
    if not EXTRACTED_DIR.is_dir():
        print(f"ERROR: El directorio de assets extraídos no existe en '{EXTRACTED_DIR}'")
        return

    FINAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    metadata_index = index_metadata_files(METADATA_DIR)
    furni_base_dirs = [d for d in EXTRACTED_DIR.iterdir() if d.is_dir()]
    num_processes = cpu_count()
    print(f"Utilizando {num_processes} procesos para acelerar la fusión...")
    tasks = [(d, metadata_index, PROJECT_ROOT, FINAL_DATA_DIR) for d in furni_base_dirs]
    results_map = defaultdict(int)
    error_details = []

    with Pool(processes=num_processes) as pool:
        results = list(tqdm(pool.starmap(process_single_furni, tasks), total=len(tasks), desc="Procesando Furnis"))

    for result in results:
        status = result[0]
        results_map[status] += 1
        if status == "error":
            error_details.append(result)

    print(f"\n¡Fusión completada!")
    print(f"  - Archivos de datos finales guardados: {results_map.get('processed', 0)}")
    skipped_total = sum(v for k, v in results_map.items() if k.startswith('skipped'))
    print(f"  - Furnis saltados (total): {skipped_total}")
    for reason, count in sorted(results_map.items()):
        if reason.startswith('skipped'):
            print(f"    - Razón '{reason}': {count}")
    
    if error_details:
        print(f"  - Furnis con errores: {len(error_details)}")
        # (Descomentar para depuración)
        # print("\n--- Mostrando los primeros 5 errores detallados ---")
        # for i, (status, base_id, tb) in enumerate(error_details):
        #     if i >= 5: break
        #     print(f"\nERROR en el furni '{base_id}':\n{tb}")

if __name__ == "__main__":
    process_all_furnis()