# Habbo Furni Asset Pipeline

An automated pipeline to download, process, and organize Habbo Hotel assets. This project orchestrates a multi-step workflow to transform raw game files into a usable format for applications like room decorators.

## The Pipeline Workflow

The entire process is designed as a 4-step pipeline. Each step prepares data for the next, with the final goal of producing a comprehensive and easy-to-use set of assets.

---

### ✅ Step 1: Download SWF Files & Gamedata

This initial step is responsible for fetching the raw asset files from Habbo servers.

*   **Primary Method:** The pipeline uses a forked version of **[higoka/habbo-downloader](https://github.com/higoka/habbo-downloader)**, managed as a Git submodule, to execute the downloads.
*   **Output:** Raw `.swf` files are saved to `/assets/furnitures`, and gamedata files to `/assets/gamedata`.

> **Status:** Fully implemented in `pipeline.py`.

---

### ✅ Step 2: Extract, Render & Generate Data

This crucial step processes the raw SWF files downloaded in Step 1. It extracts their content, renders visual assets (images, animations), and generates structured data files.

*   It uses the **[Habbo-SWF-Furni-Extractor](https://github.com/netraular/Habbo-SWF-Furni-Extractor)** project, a custom .NET tool managed as a submodule.
*   The tool processes all files from `/assets/furnitures` and produces a structured output in `/assets/extracted`, including PNGs, GIFs, and local `furni.json` files.

> **Status:** **Fully implemented** in `pipeline.py`.

---

### ✅ Step 3: Fetch & Process API Metadata

To enrich the locally extracted data, this step fetches additional metadata (like release dates, categories, and multi-language names/descriptions) from a web API.

*   It uses the **[habbo-furni-data-downloader](https://github.com/netraular/habbo-furni-data-downloader)** project, a custom Python tool managed as a submodule, to connect to the **[habbofurni.com API](https://habbofurni.com/)**.
*   The pipeline downloads data from both the `.com` (English) and `.es` (Spanish) hotels and merges them to create a more complete record.
*   The final, processed metadata is saved in `/assets/metadata_processed`, where each furni has its own folder containing a `data.json` file.
*   **Note:** This step only handles JSON metadata. The actual asset files (`.swf`, `.png`) are managed by Steps 1 and 2.

> **Status:** **Fully implemented** in `pipeline.py`.

---

### 🔲 Step 4: Merge All Data Sources

This is the final data processing step. A custom script will merge the information from all previous steps into a single, unified data structure.

*   It will combine the local data (`furni.json` from Step 2) with the downloaded gamedata (from Step 1) and the external API metadata (from Step 3).

> **Status:** Not yet implemented.

---

## Getting Started

### Prerequisites

*   [Git](https://git-scm.com/)
*   [Node.js](https://nodejs.org/) (which includes npm)
*   [Python](https://www.python.org/) (version 3.6 or higher)
*   [.NET SDK](https://dotnet.microsoft.com/download) (version 6.0 or higher)

### Installation

1.  **Clone the repository with all submodules:**
    ```sh
    git clone --recurse-submodules https://github.com/netraular/habbo-furni-asset-pipeline.git
    ```

2.  **Navigate into the project directory:**
    ```sh
    cd habbo-furni-asset-pipeline
    ```

3.  **Install Node.js dependencies:**
    ```sh
    cd dependencies/habbo-asset-downloader && npm install && cd ../..
    ```

4.  **Install Python dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

5.  **Configure API Token:**
    *   Rename the `.env.example` file in the project root to `.env`.
    *   Open the `.env` file and add your API token from `habbofurni.com`.
    ```env
    HABBOFURNI_API_TOKEN="your_token_here"
    ```

## Usage

You can run the entire pipeline or start from a specific step using the `--start-at` argument.

#### Run the entire pipeline
```sh
python pipeline.py
```

#### Skip to Step 2 (Extraction & Rendering)
```sh
python pipeline.py --start-at 2
```

#### Skip to Step 3 (Metadata Download & Processing)
```sh
python pipeline.py --start-at 3
```

## Maintaining the Pipeline

### Updating Dependencies (Submodules)

The submodules in the `dependencies` folder are pinned to a specific commit. If you update one of the dependency projects on GitHub, the pipeline won't use it automatically.

To pull the latest version of a submodule, run the following command from the project's root directory:

```sh
git submodule update --remote
```

After running the update, you must commit and push the change to save the new reference:

```sh
git add .
git commit -m "chore(deps): update submodule to latest version"
git push
```