# scripts/merge_furni_data.py (VERSIÓN CON LÓGICA DE BASE MEJORADA)
import os
import json
import traceback
from pathlib import Path
from multiprocessing import Pool, cpu_count
from collections import defaultdict
from tqdm import tqdm

EDITOR_ROTATION_MAP = [2, 4, 6, 0]

def index_metadata_files(metadata_dir: Path) -> dict:
    print("Indexando archivos de metadatos (lógica final)...")
    metadata_index = {}
    
    metadata_folders = [d for d in metadata_dir.iterdir() if d.is_dir()]

    for folder in tqdm(metadata_folders, desc="Indexando"):
        meta_file = folder / "data.json"
        if meta_file.exists():
            metadata_index[folder.name] = meta_file
            
    print(f"Indexación completa. Se encontraron {len(metadata_index)} archivos de metadatos únicos.")
    return metadata_index

def process_single_furni(base_dir: Path, metadata_index: dict, project_root: Path, final_data_dir: Path):
    classname = base_dir.name
    
    try:
        metadata_files = sorted([
            path for name, path in metadata_index.items() 
            if name == classname or name.startswith(classname + '_')
        ])

        if not metadata_files:
            return ("skipped_no_metadata", classname)

        rendered_dir = base_dir / "rendered"
        if not rendered_dir.is_dir() or not any(rendered_dir.glob("*_no_sd.png")):
            return ("skipped_no_renders", classname)

        render_data_path = base_dir / "renderdata.json"
        if not render_data_path.exists():
            return ("skipped_no_renderdata", classname)
    
        with open(render_data_path, 'r') as f:
            render_data = json.load(f)

        # --- LÓGICA MEJORADA PARA SELECCIONAR LA INFORMACIÓN BASE ---
        # 1. Buscar un metadato "ideal" para la base (sin sufijo o con _0)
        base_meta_path = None
        for path in metadata_files:
            # path.parent.name es el nombre de la carpeta, ej: 'rare_dragonlamp_0'
            if path.parent.name == classname or path.parent.name == f"{classname}_0":
                base_meta_path = path
                break
        
        # 2. Si no se encuentra un ideal, usar el primero de la lista ordenada como fallback
        if not base_meta_path:
            base_meta_path = metadata_files[0]
        
        with open(base_meta_path, 'r', encoding='utf-8') as f:
            base_meta = json.load(f).get("hotelData", {})
        
        if not base_meta:
            return ("skipped_bad_metadata", classname)

        base_id_from_api = (base_meta.get("classname") or classname).split('*')[0]

        merged_furni_data = {
            "base_id": base_id_from_api,
            "name": base_meta.get('name', classname) or classname,
            "description": base_meta.get('description', ''),
            "dimensions": {"x": base_meta.get('xdim', 1), "y": base_meta.get('ydim', 1)},
            "category": base_meta.get('category', 'unknown'),
            "furni_line": base_meta.get('furni_line', 'unknown'),
            "variants": {}
        }
        
        for meta_file_path in metadata_files:
            with open(meta_file_path, 'r', encoding='utf-8') as f:
                variant_meta = json.load(f).get("hotelData", {})
            
            api_classname = variant_meta.get("classname") or classname
            color_id = api_classname.split('*')[-1] if '*' in api_classname else "0"

            icon_with_color_path = base_dir / f"{classname}_icon_{color_id}.png"
            icon_generic_path = base_dir / f"{classname}_icon.png"
            final_icon_path_obj = icon_with_color_path if icon_with_color_path.exists() else icon_generic_path

            variant_entry = {
                "id": f"{base_id_from_api}_{color_id}" if color_id != "0" else base_id_from_api,
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
                    full_image_path = project_root / "assets" / image_path_str
                    
                    if full_image_path.exists():
                        variant_entry["renders"][str(rot_idx)] = {
                            "path": image_path_str.replace(os.sep, '/'),
                            "offset": {"x": offset["X"], "y": offset["Y"]}
                        }

            if variant_entry["renders"]:
                merged_furni_data["variants"][color_id] = variant_entry

        if merged_furni_data["variants"]:
            output_dir = final_data_dir / base_id_from_api
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / "data.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(merged_furni_data, f, indent=2, sort_keys=True) # Añadido sort_keys para consistencia
            return ("processed", classname)
        else:
            return ("skipped_no_variants_found", classname)
            
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

if __name__ == "__main__":
    process_all_furnis()