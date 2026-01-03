# Knowledge Archive

## Architectural Intent
This archive treats personal experience and technical analysis as a single maturation pipeline. The core principle is that data is not split by genre, but by **Maturation Stage**. The goal is to transform raw inputs into a queryable, formalized knowledge base.

## Data Ingestion (NotebookLM)
To pull data from NotebookLM into the archive:

### Option A: Clipboard Ingestion (Recommended)
1.  **Copy Content**: Select text in NotebookLM and copy it (`Ctrl+C` / `Cmd+C`).
2.  **Ingest**: In the Archive Dashboard, click **"Ingest from Clipboard"** (under Utilities).
3.  **Verify**: The text is automatically saved as a timestamped markdown file in `notebooklm-import-raw/`.

### Option B: Manual Staging
1.  **Export Content**: Copy your notes or source text.
2.  **Create Markdown**: Paste the text into a new file with a `.md` extension.
3.  **Stage File**: Save this file into the `notebooklm-import-raw/` directory.

### Processing
Once staged, run the **"1. Initialize & Scan"** command in the toolkit to detect and classify the new data.

## Directory Structure
The archive follows a `Pattern-Domain > Maturation-Stage` hierarchy:

*   **`[pattern-domain]/`**: The top-level category of the knowledge (e.g., `tradecraft`, `forensic-psychology`).
    *   **`experiential_data/`**: Raw accounts, high texture, single observations.
    *   **`analytical_synthesis/`**: Pattern articulation, partial theory, connecting dots.
    *   **`formalized_frameworks/`**: Refined, minimal narrative, teaching-ready doctrines.
*   **`taxonomy/`**: Contains the JSON definitions for valid domains and tags.

## Metadata Schema
Every document in this archive contains a standardized YAML frontmatter block:

```yaml
---
patterndomain: "string"           # Matches the top-level directory
maturationstage: "string"         # experientialdata | analyticalsynthesis | formalizedframework
patterntags: ["tag1", "tag2"]     # Array of tags from taxonomy
validationstatus: "string"        # singleobservation | multiinstanceconfirmation | framework_ready
instructionalreadiness: "string"  # internalreference | synthesisinprogress | teaching_ready
temporal_context:
  experience_date: "YYYY-MM-DD"
  analysis_date: "YYYY-MM-DD"
provenance: "string"              # personaldocumentation | collaborativework | external_synthesis
source: "notebooklm"
source_url: "string"              # URL to the original NotebookLM source
related_links: ["url1", "url2"]   # External research papers
import_date: "YYYY-MM-DD"
---
```

## Maintenance
This archive is managed via the `ARCHIVE-TOOLKIT.py` script.

*   **Organization**: Files are moved and renamed based on the `classification-manifest.csv`.
*   **Indexing**: Domain-specific indices are generated in the `_indexes/` directory at the project root.
*   **Validation**: The toolkit validates metadata against the JSON files in the `taxonomy/` folder.