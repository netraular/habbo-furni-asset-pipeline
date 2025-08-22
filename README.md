# Habbo Asset Pipeline

This repository contains an automated pipeline to fetch, process, and organize Habbo furniture assets, preparing them for use in other applications.

The orchestrator is built with Python and coordinates several external tools (managed as Git Submodules) to create a consistent and reliable asset workflow.

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed on your system:
- [Python 3.8+](https://www.python.org/)
- [Node.js 15.0+](https://nodejs.org/) (which includes npm)

### Installation

This project uses **Git Submodules** to manage its dependencies. To clone the repository and its dependencies correctly, use the `--recurse-submodules` flag:

```bash
git clone --recurse-submodules https://github.com/your-username/habbo-asset-pipeline.git
cd habbo-asset-pipeline
```

If you have already cloned the repository without the submodules, you can initialize them with this command:

```bash
git submodule update --init --recursive
```

## 🛠️ Usage

The entire pipeline is controlled by the main orchestrator script. The first time you run it, it will automatically install the necessary Node.js dependencies for its tools.

To run the full pipeline, execute the following command from the root of the project:

```bash
python main_orchestrator.py
```

This will begin the process of fetching and processing all required assets, placing the final output in the `habbo_assets` directory.

---

## 📚 Pipeline Workflow & Backup Methods

This pipeline is designed to be resilient. For critical steps, alternative methods are documented in case the primary tool fails.

### Step 1: Download SWF Files

-   **Primary Method:** The pipeline uses [higoka/habbo-downloader](https://github.com/higoka/habbo-downloader) to efficiently download all furniture `.swf` files from Habbo's servers. This is the fastest and most comprehensive method for bulk downloads.

-   **Backup Method:** If the primary downloader fails or you need a specific furni quickly, you can use the public API provided by [habbofurni.com](https://habbofurni.com/). Note that this method is significantly slower for bulk downloads and should be used as a fallback.

### Step 2: Decompress SWF Files
*(Coming soon...)*

### Step 3: Render Sprites & Generate Data
*(Coming soon...)*

### Step 4: Fetch Metadata from Web API
*(Coming soon...)*

### Step 5: Merge All Data Sources
*(Coming soon...)*

---

## 📂 Project Structure

-   `main_orchestrator.py`: The main Python script that controls the entire pipeline.
-   `dependencies/`: Contains all external tools, managed as Git submodules. These are not part of this repository's source code but are essential for its operation.
-   `habbo_assets/`: The output directory where all final, processed assets will be stored. This folder is ignored by Git.
-   `README.md`: This file.
