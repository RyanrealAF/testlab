# Knowledge Archive Migration Toolkit

This toolkit automates the migration of raw knowledge files into a structured, indexed archive.

## Workflow

1.  **Initialization**:
    ```bash
    python archive_toolkit.py init
    ```
    - Creates directory structure (`archive`, `taxonomy`, `manifests`).
    - Generates taxonomy stubs.
    - Scans `notebooklm-import-raw` and generates `manifests/classification-manifest.csv`.

2.  **Classification**:
    - Edit `manifests/classification-manifest.csv`.
    - Fill in `pattern_domain` and `pattern_tags` for each file.
    - Verify `maturation_stage`.

3.  **Execution**:
    ```bash
    python archive_toolkit.py run
    ```
    - Moves files to `archive/<domain>/<stage>/`.
    - Injects YAML frontmatter.
    - Generates indexes in `_indexes/`.

4.  **Validation**:
    ```bash
    python archive_toolkit.py validate
    ```
    - Checks for broken links in indexes.
    - Identifies orphaned files.

5.  **Reporting**:
    ```bash
    python archive_toolkit.py report
    ```
    - Displays statistics on domains, stages, and tags.

6.  **Exporting**:
    ```bash
    python export_toolkit.py --all
    ```
    - Generates `knowledge_bundle.json` (metadata + content).
    - Creates `knowledge_archive.zip` (backup of directories).

7.  **Cleanup**:
    ```bash
    python cleanup_toolkit.py --all
    ```
    - Fixes Git warnings by removing `desktop.ini` from `.git`.
    - Removes the `notebooklm-import-raw` staging directory.

## Directory Structure

- `archive/`: Structured knowledge base.
- `_indexes/`: Generated markdown indexes.
- `taxonomy/`: JSON definitions for domains and tags.
- `manifests/`: CSV files for process control.