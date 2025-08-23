# Habbo Furni Asset Pipeline

An automated pipeline to download, process, and organize Habbo Hotel assets. This project orchestrates a multi-step workflow to transform raw game files into a structured, application-ready format.

The entire process is managed by `pipeline.py`, which executes a 4-step workflow. Each step prepares data for the next, with the final goal of producing a comprehensive and easy-to-use set of assets. The output directories are prefixed with the step number (`1_`, `2_`, etc.) to clearly show the data flow.

---

### ✅ Step 1: Download Raw Assets

This initial step fetches the raw asset files from Habbo servers.

*   **Method:** Uses **[habbo-asset-downloader](https://github.com/higoka/habbo-downloader)** (as a submodule) to download files.
*   **Output:**
    *   Raw `.swf` files are saved to `/assets/1_furnitures_raw`.
    *   Gamedata files (like `furnidata.txt`) are saved to `/assets/1_gamedata_raw`.

---

### ✅ Step 2: Extract, Render & Generate Data

This crucial step processes the raw SWF files from Step 1. It extracts their content, renders visual assets (images, icons), and generates structured data.

*   **Method:** Uses the **[Habbo-SWF-Furni-Extractor](https://github.com/netraular/Habbo-SWF-Furni-Extractor)** project (a custom .NET tool managed as a submodule).
*   **Output:** A structured directory for each furni is created in `/assets/2_extracted_swf_data`. Each subdirectory contains PNGs, GIFs, and local data files like `furni.json` and `renderdata.json`.

---

### ✅ Step 3: Fetch & Process API Metadata

To enrich the locally extracted data, this step fetches additional metadata (like release dates, categories, and multi-language names) from an external API.

*   **Method:** Uses the **[habbo-furni-data-downloader](https://github.com/netraular/habbo-furni-data-downloader)** project (a custom Python tool managed as a submodule) to connect to the **[habbofurni.com API](https://habbofurni.com/)**.
*   The pipeline downloads data, merges English and Spanish sources, and organizes it.
*   **Output:**
    *   Raw API responses are saved to `/assets/3_metadata_raw_api`.
    *   Processed and organized JSON files are saved to `/assets/3_metadata_processed_api`.

---

### ✅ Step 4: Create Self-Contained Furni Packages

This is the final and most important step. It merges all data and assets from the previous steps into clean, portable, and application-ready packages.

*   **Method:** A custom Python script (`scripts/merge_furni_data.py`) performs an **asset-driven merge**:
    *   It reads the local `furni.json` from Step 2 to identify all possible color variations for an object.
    *   For each variation, it finds the corresponding API metadata from Step 3.
    *   It copies all necessary visual assets (icons and rendered images) into a new, organized structure.
    *   All paths within the final `data.json` are relative, making each package completely self-contained.

*   **Output:** The final, application-ready data is saved in `/assets/4_final_furni_data`. Each furni has its own folder which acts as a complete package, containing:
    *   A central `data.json` file with all merged metadata.
    *   An `icons/` subfolder with all variant icons.
    *   A `renders/` subfolder with all variant renders.

    This structure is the **definitive output** of the pipeline. For example:
    ```
    /assets/4_final_furni_data/
    └── rare_dragonlamp/
        ├── data.json
        ├── icons/
        │   ├── rare_dragonlamp_icon_0.png
        │   └── rare_dragonlamp_icon_1.png
        └── renders/
            ├── rare_dragonlamp_dir_2_0_no_sd.png
            └── rare_dragonlamp_dir_4_0_no_sd.png
    ```

---

## Getting Started

### Prerequisites

*   [Git](https://git-scm.com/)
*   [Node.js](https://nodejs.org/) (which includes npm)
*   [Python](https://www.python.org/) (version 3.8 or higher)
*   [.NET SDK](https://dotnet.microsoft.com/download) (version 6.0 or higher)

### Installation

1.  **Clone the repository with all submodules:**
    ```sh
    git clone --recurse-submodules https://github.com/netraular/habbo-furni-asset-pipeline.git
    cd habbo-furni-asset-pipeline
    ```

2.  **Install Node.js dependencies:**
    ```sh
    cd dependencies/habbo-asset-downloader && npm install && cd ../..
    ```

3.  **Install Python dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Configure API Token:**
    *   Rename `.env.example` to `.env`.
    *   Open `.env` and add your API token from `habbofurni.com`.
    ```env
    HABBOFURNI_API_TOKEN="your_token_here"
    ```

## Usage

You can run the entire pipeline or start from a specific step using the `--start-at` argument.

#### Run the entire pipeline
```sh
python pipeline.py
```
#### Run only the final merge (Step 4)
```sh
python pipeline.py --start-at 4
```

## Maintaining the Pipeline

### Updating Dependencies (Submodules)

To pull the latest version of a submodule, run the following command from the project's root directory:
```sh
git submodule update --remote
```
After updating, commit the change to save the new reference:
```sh
git add .
git commit -m "chore(deps): update submodule to latest version"
git push
```