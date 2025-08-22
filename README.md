# Habbo Furni Asset Pipeline

An automated pipeline to download, process, and organize Habbo Hotel assets. This project orchestrates a multi-step workflow to transform raw game files into a usable format for applications like room decorators.

## The Pipeline Workflow

The entire process is designed as a 5-step pipeline. Each step prepares data for the next, with the final goal of producing a comprehensive and easy-to-use set of assets.

---

### ✅ Step 1: Download SWF Files & Gamedata

This initial step is responsible for fetching the raw asset files from Habbo servers.

*   **Primary Method:** The pipeline uses a forked version of **[higoka/habbo-downloader](https://github.com/higoka/habbo-downloader)**, managed as a Git submodule, to execute the downloads.
*   **Alternative Source 1:** The original `habbo-downloader` repository contains a `resources` folder with a large cache of SWF files that can be used directly as a backup.
*   **Alternative Source 2:** For a more targeted but slower approach, the **[habbofurni.com API](https://habbofurni.com/)** can also be used to fetch individual assets.

> **Status:** This step is **fully implemented** in `pipeline.py`.

---

### 🔲 Step 2: Decompress SWF Files

The downloaded `.swf` files are compressed. This step will decompress them to allow access to the raw shapes, sprites, and metadata within.

> **Status:** Not yet implemented.
> *Note: A similar project exists for this, but it is currently non-functional and will require adaptation.*

---

### 🔲 Step 3: Render Sprites & Generate Data

Once decompressed, the assets inside the SWF files need to be rendered into standard image formats (like PNG) and their configuration data extracted.

*   This step will use a custom script to parse sprite data and generate two key files:
    1.  `furni.json`: Contains merged XML data describing the furni's logic.
    2.  `rendering.json`: Contains data needed to reconstruct and render the furni isometrically.
*   This script is based on concepts from another existing GitHub project for SWF rendering.

> **Status:** Not yet implemented.

---

### 🔲 Step 4: Fetch Metadata from Web API

To enrich the local data, this step will fetch additional metadata (like release dates, categories, etc.) from an external web API.

> **Status:** Not yet implemented.

---

### 🔲 Step 5: Merge All Data Sources

This is the final data processing step. A custom script will merge the information from all previous steps into a single, unified data structure.

*   It will combine the local data (`furni.json`) with the downloaded gamedata (from Step 1) and the external API metadata (from Step 4).

> **Status:** Not yet implemented.

---

### Final Output Consumer

The final, clean assets produced by this pipeline are intended to be used by a separate project: an **Isometric Room Decorator**, which will simulate the Habbo room building experience.

## Getting Started

### Prerequisites

*   [Git](https://git-scm.com/)
*   [Node.js](https://nodejs.org/) (which includes npm)
*   [Python](https://www.python.org/) (version 3.6 or higher)

### Installation

1.  **Clone the repository with its submodule:**
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

Currently, only Step 1 of the pipeline is implemented. To run it:

```sh
python pipeline.py
```

This will create an `/assets` folder and populate it with downloaded and organized files from Habbo servers.