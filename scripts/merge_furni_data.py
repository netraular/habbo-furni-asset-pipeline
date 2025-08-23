# scripts/merge_furni_data.py (VERSIÓN FINAL CON CARPETAS DE ICONOS)
import os
import json
import traceback
import shutil
from pathlib import Path
from multiprocessing import Pool, cpu_count
from collections import defaultdict
from tqdm import tqdm

EDITOR_ROTATION_MAP = [2, 4, 6, 0]

# --- (Las funciones index_metadata_files y get_color_ids_from_furni_json no cambian) ---

def index_metadata_files(metadata_dir: Path) -> dict:
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
    if not furni_json_path.exists(): return ['0']
    with open(furni_json_path, 'r') as f: data = json.load(f)
    try:
        vis = next((v for k, v in data.get('visualization', {}).items() if k in ['64', '32']), None)
        if not vis: vis = next(iter(data.get('visualization', {}).values()), {})
        colors = vis.get('colors', {})
        if colors: return sorted(colors.keys(), key=int)
    except Exception: pass
    return ['0']

def process_single_furni(base_dir: Path, metadata_index: dict, project_root: Path, final_data_dir: Path):
    classname = base_dir.name
    try:
        render_data_path = base_dir / "renderdata.json"
        furni_json_path = base_dir / "furni.json"
        rendered_dir = base_dir / "rendered"

        if not render_data_path.exists() or not rendered_dir.is_dir() or not any(rendered_dir.glob("*_no_sd.png")):
            return ("skipped_no_renders", classname)

        color_ids = get_color_ids_from_furni_json(furni_json_path)
        with open(render_data_path, 'r') as f: render_data = json.load(f)

        merged_furni_data = None
        output_dir = None
        is_first_variant = True

        for color_id in color_ids:
            metadata_key = classname if color_id == '0' and classname not in metadata_index else f"{classname}_{color_id}"
            if metadata_key not in metadata_index and color_id == '0': metadata_key = classname
            
            meta_file_path = metadata_index.get(metadata_key)
            if not meta_file_path: continue

            with open(meta_file_path, 'r', encoding='utf-8') as f:
                variant_meta = json.load(f).get("hotelData", {})
            if not variant_meta: continue
            
            if is_first_variant:
                base_id_from_api = (variant_meta.get("classname") or classname).split('*')[0]
                merged_furni_data = {
                    "base_id": base_id_from_api,
                    "dimensions": {"x": variant_meta.get('xdim', 1), "y": variant_meta.get('ydim', 1)},
                    "category": variant_meta.get('category', 'unknown'),
                    "furni_line": variant_meta.get('furni_line', 'unknown'),
                    "variants": {}
                }
                output_dir = final_data_dir / base_id_from_api
                
                # --- CAMBIO 1: Crear la carpeta 'icons' junto a la de 'renders' ---
                (output_dir / "renders").mkdir(parents=True, exist_ok=True)
                (output_dir / "icons").mkdir(parents=True, exist_ok=True)
                
                is_first_variant = False

            source_icon_path = base_dir / f"{classname}_icon_{color_id}.png"
            if not source_icon_path.exists(): source_icon_path = base_dir / f"{classname}_icon.png"
            
            # --- CAMBIO 2: Modificar la ruta de destino del icono ---
            dest_icon_path = output_dir / "icons" / source_icon_path.name
            if source_icon_path.exists() and not dest_icon_path.exists(): shutil.copy(source_icon_path, dest_icon_path)
            
            variant_entry = {
                "id": f"{merged_furni_data['base_id']}_{color_id}" if color_id != "0" else merged_furni_data['base_id'],
                "name": variant_meta.get("name") or variant_meta.get("classname"),
                "description": variant_meta.get("description", ""),
                # --- CAMBIO 3: Actualizar la ruta en el JSON ---
                "icon_path": f"icons/{source_icon_path.name}",
                "renders": {}
            }
            
            for rot_idx, direction in enumerate(EDITOR_ROTATION_MAP):
                render_key = f"{classname}_dir_{direction}_{color_id}_no_sd"
                if render_key not in render_data: render_key = f"{classname}_dir_{direction}_no_sd"
                
                if render_key in render_data:
                    offset = render_data[render_key]
                    source_render_path = rendered_dir / f"{render_key}.png"
                    
                    if source_render_path.exists():
                        dest_render_path = output_dir / "renders" / source_render_path.name
                        if not dest_render_path.exists(): shutil.copy(source_render_path, dest_render_path)
                        variant_entry["renders"][str(rot_idx)] = {"path": f"renders/{source_render_path.name}", "offset": {"x": offset["X"], "y": offset["Y"]}}

            if variant_entry["renders"]:
                merged_furni_data["variants"][color_id] = variant_entry

        if merged_furni_data and merged_furni_data["variants"]:
            with open(output_dir / "data.json", 'w', encoding='utf-8') as f:
                json.dump(merged_furni_data, f, indent=2)
            return ("processed", classname)
        else:
            return ("skipped_no_valid_variants", classname)
            
    except Exception:
        return ("error", classname, traceback.format_exc())

def process_all_furnis():
    # --- (Esta función no cambia, se mantiene la versión rápida con starmap) ---
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    EXTRACTED_DIR = PROJECT_ROOT / "assets" / "2_extracted_swf_data"
    METADATA_DIR = PROJECT_ROOT / "assets" / "3_metadata_processed_api"
    FINAL_DATA_DIR = PROJECT_ROOT / "assets" / "4_final_furni_data"

    print(f"Iniciando fusión de datos y copia de assets hacia '{FINAL_DATA_DIR}'...")
    
    if not EXTRACTED_DIR.is_dir(): print(f"ERROR: El directorio de assets extraídos no existe en '{EXTRACTED_DIR}'"); return

    FINAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    metadata_index = index_metadata_files(METADATA_DIR)
    furni_base_dirs = [d for d in EXTRACTED_DIR.iterdir() if d.is_dir()]
    num_processes = cpu_count()
    print(f"Utilizando {num_processes} procesos para acelerar la fusión...")
    
    tasks = [(d, metadata_index, PROJECT_ROOT, FINAL_DATA_DIR) for d in furni_base_dirs]
    results_map = defaultdict(int)
    error_details = []

    print("Procesando furnis... (esto puede tardar un momento sin mostrar progreso)")
    with Pool(processes=num_processes) as pool:
        results = pool.starmap(process_single_furni, tasks)

    for result in results:
        status = result[0]
        results_map[status] += 1
        if status == "error": error_details.append(result)

    print(f"\n¡Fusión completada!")
    print(f"  - Paquetes de furnis guardados: {results_map.get('processed', 0)}")
    skipped_total = sum(v for k, v in results_map.items() if k.startswith('skipped'))
    print(f"  - Furnis saltados (total): {skipped_total}")
    for reason, count in sorted(results_map.items()):
        if reason.startswith('skipped'): print(f"    - Razón '{reason}': {count}")
    if error_details: print(f"  - Furnis con errores: {len(error_details)}")

if __name__ == "__main__":
    process_all_furnis()