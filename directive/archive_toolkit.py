import os
import csv
import json
import argparse
import re
from pathlib import Path
from datetime import datetime

# --- Configuration ---
ROOT_DIR = Path(os.getcwd())
STAGING_DIR = ROOT_DIR / "notebooklm-import-raw"
ARCHIVE_DIR = ROOT_DIR / "archive"
TAXONOMY_DIR = ROOT_DIR / "taxonomy"
MANIFEST_DIR = ROOT_DIR / "manifests"
MANIFEST_FILE = MANIFEST_DIR / "classification-manifest.csv"

# --- Taxonomy Stubs ---
DEFAULT_DOMAINS = [
    {"id": "forensic-psychology", "description": "Analysis of psychological manipulation and coercive control."},
    {"id": "tradecraft", "description": "Operational tactics, techniques, and procedures."},
    {"id": "neurobiology", "description": "Biological and neurological impacts of psychological stress."},
    {"id": "social-engineering", "description": "Manipulation of social structures and human behavior."}
]

DEFAULT_TAGS = [
    {"id": "humint", "description": "Human Intelligence"},
    {"id": "non-kinetic", "description": "Non-physical warfare tactics"},
    {"id": "gaslighting", "description": "Psychological manipulation to sow doubt"},
    {"id": "c-ptsd", "description": "Complex Post-Traumatic Stress Disorder"}
]

def init_directories():
    """Initialize the directory skeleton and taxonomy stubs."""
    dirs = [STAGING_DIR, ARCHIVE_DIR, TAXONOMY_DIR, MANIFEST_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"[INFO] Verified directory: {d}")

    # Populate Taxonomy Stubs
    domains_file = TAXONOMY_DIR / "domains.json"
    if not domains_file.exists():
        with open(domains_file, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_DOMAINS, f, indent=2)
        print(f"[INFO] Created taxonomy stub: {domains_file}")

    tags_file = TAXONOMY_DIR / "tags.json"
    if not tags_file.exists():
        with open(tags_file, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_TAGS, f, indent=2)
        print(f"[INFO] Created taxonomy stub: {tags_file}")

def extract_snippet(text, word_count=75):
    """
    Extracts the first 50-100 words of content.
    Skips potential frontmatter (content between --- and --- at start).
    """
    # Normalize newlines
    text = text.strip()
    
    # Simple frontmatter skip if present
    if text.startswith("---"):
        try:
            _, _, content = text.split("---", 2)
            text = content.strip()
        except ValueError:
            pass # Malformed or not frontmatter

    # Remove heavy markdown headers for cleaner text
    text = re.sub(r'#+\s', '', text)
    
    words = text.split()
    snippet = " ".join(words[:word_count])
    if len(words) > word_count:
        snippet += "..."
    
    return snippet

def generate_manifest():
    """Scans staging directory and generates the classification manifest."""
    if not STAGING_DIR.exists():
        print(f"[WARN] Staging directory {STAGING_DIR} does not exist. Please create it and add raw files.")
        return

    records = []
    print(f"[INFO] Scanning {STAGING_DIR}...")

    # Walk through staging directory to handle nested folders
    for root, _, files in os.walk(STAGING_DIR):
        for file in files:
            if file.endswith(".txt") or file.endswith(".md"):
                file_path = Path(root) / file
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    snippet = extract_snippet(content)
                    
                    # Relative path for the manifest
                    rel_path = file_path.relative_to(STAGING_DIR)

                    records.append({
                        "filepath": str(rel_path),
                        "filename": file,
                        "pattern_domain": "", # To be filled by human
                        "pattern_tags": "",   # To be filled by human
                        "maturation_stage": "raw",
                        "snippet": snippet
                    })
                except Exception as e:
                    print(f"[ERROR] Could not process {file}: {e}")

    # Write Manifest
    with open(MANIFEST_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["filepath", "filename", "pattern_domain", "pattern_tags", "maturation_stage", "snippet"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    
    print(f"[SUCCESS] Manifest generated at {MANIFEST_FILE} with {len(records)} entries.")

def organize_archive():
    """
    Phase 3: Reads manifest, moves files to architecture, injects frontmatter.
    """
    if not MANIFEST_FILE.exists():
        # Fallback: Check root directory if not found in manifests/
        fallback = ROOT_DIR / "classification-manifest.csv"
        if fallback.exists():
            print(f"[INFO] Found manifest in root: {fallback}")
            manifest_path = fallback
        else:
            print(f"[ERROR] Manifest file not found: {MANIFEST_FILE}")
            return
    else:
        manifest_path = MANIFEST_FILE

    print(f"[INFO] Processing manifest: {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip if domain is empty (user hasn't classified)
            if not row.get('pattern_domain'):
                print(f"[SKIP] No domain set for {row['filename']}")
                continue

            # Source path
            src_path = STAGING_DIR / row['filepath']
            if not src_path.exists():
                print(f"[WARN] Source file not found: {src_path}")
                continue

            # Determine Destination
            domain = row['pattern_domain'].strip().lower().replace(" ", "-")
            raw_stage = row['maturation_stage'].strip()
            clean_stage = raw_stage.lower().replace(" ", "").replace("-", "")
            
            # Map stage to folder
            stage_map = {
                "experientialdata": "experiential_data",
                "analyticalsynthesis": "analytical_synthesis",
                "formalizedframework": "formalized_frameworks",
                "raw": "experiential_data"
            }
            stage_folder = stage_map.get(clean_stage, "experiential_data")
            
            dest_dir = ARCHIVE_DIR / domain / stage_folder
            dest_dir.mkdir(parents=True, exist_ok=True)
            
            # Clean filename
            dest_filename = row['filename']
            if not dest_filename.endswith(".md"):
                dest_filename = Path(dest_filename).stem + ".md"
            
            dest_path = dest_dir / dest_filename

            # Read Content
            try:
                with open(src_path, 'r', encoding='utf-8', errors='ignore') as f_in:
                    content = f_in.read()
            except Exception as e:
                print(f"[ERROR] Reading {src_path}: {e}")
                continue

            # Prepare Frontmatter
            tags = row.get('pattern_tags', '[]')
            if tags and not tags.startswith('['):
                tags = json.dumps([t.strip() for t in tags.split(',') if t.strip()])
            elif not tags:
                tags = "[]"

            frontmatter = [
                "---",
                f"patterndomain: {domain}",
                f"maturationstage: {raw_stage}",
                f"patterntags: {tags}",
                "validationstatus: singleobservation",
                "instructionalreadiness: internalreference",
                "temporal_context:",
                "  experience_date: ''",
                f"  analysis_date: {datetime.now().strftime('%Y-%m-%d')}",
                "provenance: personaldocumentation",
                "source: notebooklm",
                f"import_date: {datetime.now().strftime('%Y-%m-%d')}",
                "---",
                "",
                content
            ]

            # Write File
            try:
                with open(dest_path, 'w', encoding='utf-8') as f_out:
                    f_out.write("\n".join(frontmatter))
                print(f"[MOVE] {src_path.name} -> {dest_path}")
            except Exception as e:
                print(f"[ERROR] Writing {dest_path}: {e}")

def generate_indexes():
    """
    Phase 4: Generates markdown indexes in _indexes/ based on metadata.
    """
    index_dir = ROOT_DIR / "_indexes"
    index_dir.mkdir(exist_ok=True)
    
    docs = []
    print(f"[INFO] Scanning archive for indexing...")
    
    for p in ARCHIVE_DIR.rglob('*.md'):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Extract Frontmatter
            meta = {}
            if text.startswith("---"):
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    fm_lines = parts[1].strip().split('\n')
                    for line in fm_lines:
                        if ':' in line:
                            k, v = line.split(':', 1)
                            meta[k.strip()] = v.strip()
                    content = parts[2]
                else:
                    content = text
            else:
                content = text

            snippet = extract_snippet(content)
            
            docs.append({
                "path": p.relative_to(ROOT_DIR).as_posix(),
                "name": p.stem,
                "meta": meta,
                "snippet": snippet
            })
        except Exception as e:
            print(f"[WARN] Skipping {p.name}: {e}")

    def write_index(filename, title, key):
        out_path = index_dir / filename
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n")
            groups = {}
            for d in docs:
                val = d['meta'].get(key, "Uncategorized")
                groups.setdefault(val, []).append(d)
            
            for group, items in sorted(groups.items()):
                f.write(f"## {group}\n\n")
                for item in items:
                    f.write(f"### [{item['name']}](../{item['path']})\n")
                    f.write(f"> {item['snippet']}\n\n")
                    f.write(f"- **Domain:** `{item['meta'].get('patterndomain', 'N/A')}`\n")
                    f.write(f"- **Stage:** `{item['meta'].get('maturationstage', 'N/A')}`\n\n")
        print(f"[INDEX] Generated {out_path}")

    write_index("index-maturation.md", "Index by Maturation Stage", "maturationstage")
    write_index("index-domains.md", "Index by Pattern Domain", "patterndomain")
    write_index("index-validation.md", "Index by Validation Status", "validationstatus")

def validate_archive():
    """
    Phase 5: Validation.
    Checks for broken links in indexes and verifies file integrity.
    """
    index_dir = ROOT_DIR / "_indexes"
    if not index_dir.exists():
        print(f"[ERROR] Index directory not found: {index_dir}")
        return

    print("[INFO] Validating indexes...")
    
    issues = []
    indexed_files = set()
    
    # Check links in indexes
    for index_file in index_dir.glob("*.md"):
        print(f"[CHECK] Scanning {index_file.name}...")
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Regex to find markdown links: [text](path)
            links = re.findall(r'\[.*?\]\((.*?)\)', content)
            
            for link in links:
                # Links in indexes are usually relative like ../archive/domain/stage/file.md
                # Resolve relative to the index file
                target_path = (index_dir / link).resolve()
                
                if not target_path.exists():
                    issues.append(f"[BROKEN LINK] In {index_file.name}: {link} -> {target_path} does not exist.")
                else:
                    indexed_files.add(target_path)

        except Exception as e:
            issues.append(f"[ERROR] Could not read {index_file.name}: {e}")

    # Check for orphans (files in archive not referenced in any index)
    print("[CHECK] Scanning for orphaned files...")
    for f in ARCHIVE_DIR.rglob("*.md"):
        if f.resolve() not in indexed_files:
            issues.append(f"[ORPHAN] File exists but not indexed: {f.relative_to(ROOT_DIR)}")

    # Report
    if issues:
        print("\n[WARN] Validation Issues Found:")
        for issue in issues:
            print(issue)
    else:
        print("\n[SUCCESS] All index links verified. Archive integrity confirmed.")

def report_statistics():
    """
    Phase 6: Reporting.
    Generates a summary of the archive content.
    """
    if not ARCHIVE_DIR.exists():
        print(f"[ERROR] Archive directory not found: {ARCHIVE_DIR}")
        return

    print("[INFO] Generating archive statistics...")
    
    stats = {
        "total_files": 0,
        "by_domain": {},
        "by_stage": {},
        "by_tag": {}
    }

    for p in ARCHIVE_DIR.rglob('*.md'):
        stats["total_files"] += 1
        try:
            with open(p, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract simple frontmatter
            domain = "unknown"
            stage = "unknown"
            tags = []
            
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 2:
                    fm = parts[1]
                    for line in fm.split('\n'):
                        line = line.strip()
                        if line.startswith("patterndomain:"):
                            domain = line.split(":", 1)[1].strip()
                        elif line.startswith("maturationstage:"):
                            stage = line.split(":", 1)[1].strip()
                        elif line.startswith("patterntags:"):
                            tag_str = line.split(":", 1)[1].strip()
                            try:
                                tags = json.loads(tag_str)
                            except:
                                pass

            stats["by_domain"][domain] = stats["by_domain"].get(domain, 0) + 1
            stats["by_stage"][stage] = stats["by_stage"].get(stage, 0) + 1
            for tag in tags:
                stats["by_tag"][tag] = stats["by_tag"].get(tag, 0) + 1

        except Exception as e:
            print(f"[WARN] Error reading {p.name}: {e}")

    print("\n=== Archive Migration Report ===")
    print(f"Total Files: {stats['total_files']}")
    
    print("\n--- By Domain ---")
    for k, v in sorted(stats["by_domain"].items()):
        print(f"{k:<25}: {v}")

    print("\n--- By Maturation Stage ---")
    for k, v in sorted(stats["by_stage"].items()):
        print(f"{k:<25}: {v}")
        
    print("\n--- Top Tags ---")
    sorted_tags = sorted(stats["by_tag"].items(), key=lambda x: (-x[1], x[0]))
    for k, v in sorted_tags[:10]:
        print(f"{k:<25}: {v}")
    print("================================")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Knowledge Archive Migration Toolkit")
    parser.add_argument("command", choices=["init", "run", "index", "validate", "report"], help="Command to execute")
    args = parser.parse_args()

    if args.command == "init":
        init_directories()
        generate_manifest()
    elif args.command == "run":
        organize_archive()
        generate_indexes()
    elif args.command == "index":
        generate_indexes()
    elif args.command == "validate":
        validate_archive()
    elif args.command == "report":
        report_statistics()