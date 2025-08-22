# Habbo Furni Asset Pipeline

An automated pipeline to download, process, and organize Habbo Hotel assets. This project orchestrates a multi-step workflow to transform raw game files into a usable format for applications like room decorators.

## The Pipeline Workflow

The entire process is designed as a 4-step pipeline. Each step prepares data for the next, with the final goal of producing a comprehensive and easy-to-use set of assets.

---

### ✅ Step 1: Download SWF Files & Gamedata

This initial step is responsible for fetching the raw asset files from Habbo servers.

*   **Primary Method:** The pipeline uses a forked version of **[higoka/habbo-downloader](https://github.com/higoka/habbo-downloader)**, managed as a Git submodule, to execute the downloads.

> **Status:** Fully implemented in `pipeline.py`.

---

### ✅ Step 2: Extract, Render & Generate Data

This crucial step processes the raw SWF files, extracting their content, rendering assets, and generating structured data files.

*   It uses the **[Habbo-SWF-Furni-Extractor](https://github.com/netraular/Habbo-SWF-Furni-Extractor)** project, a custom .NET tool managed as a submodule.
*   The tool processes all files from `/assets/furnitures` and produces a structured output in `/assets/extracted`, which includes:
    *   Rendered PNGs of the furni assets.
    *   `furni.json`: Contains merged XML data describing the furni's logic.
    *   `renderdata.json`: Contains data needed to reconstruct and render the furni isometrically.

> **Status:** **Fully implemented** in `pipeline.py`.

---

### 🔲 Step 3: Fetch Metadata from Web API

To enrich the local data, this step will fetch additional metadata (like release dates, categories, etc.) from an external web API.

> **Status:** Not yet implemented.

---

### 🔲 Step 4: Merge All Data Sources

This is the final data processing step. A custom script will merge the information from all previous steps into a single, unified data structure.

*   It will combine the local data (`furni.json` from Step 2) with the downloaded gamedata (from Step 1) and the external API metadata (from Step 3).

> **Status:** Not yet implemented.

---

### Final Output Consumer
(Section remains the same)

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

3.  **Install the downloader's dependencies:**
    ```sh
    cd dependencies/habbo-asset-downloader
    npm install
    cd ../..
    ```

## Usage

You can run the entire pipeline or start from a specific step using the `--start-at` argument.

#### Run the entire pipeline (from Step 1)
```sh
python pipeline.py
```

#### Skip downloads and start from Step 2 (Extraction)
This is useful if you have already downloaded the assets.
```sh
python pipeline.py --start-at 2
```

## Maintaining the Pipeline

### Updating Dependencies (Submodules)

The submodules in the `dependencies` folder are pinned to a specific commit. If you update one of the dependency projects on GitHub (e.g., you push a new version of `Habbo-SWF-Furni-Extractor`), the pipeline won't use it automatically.

To pull the latest version of a submodule into the pipeline, run the following command from the project's root directory:

```sh
git submodule update --remote
```

After running the update, you will see that the submodule reference has changed. You must then commit and push this change to save it:

```sh
git add .
git commit -m "chore(deps): update submodule to latest version"
git push
```