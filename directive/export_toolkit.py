import os
import json
import zipfile
import argparse
from pathlib import Path

ROOT_DIR = Path(os.getcwd())
ARCHIVE_DIR = ROOT_DIR / "archive"
INDEX_DIR = ROOT_DIR / "_indexes"
OUTPUT_JSON = ROOT_DIR / "knowledge_bundle.json"
OUTPUT_ZIP = ROOT_DIR / "knowledge_archive.zip"

def bundle_to_json():
    """Bundles all markdown files in the archive into a single JSON file."""
    if not ARCHIVE_DIR.exists():
        print(f"[ERROR] Archive directory not found: {ARCHIVE_DIR}")
        return

    print(f"[INFO] Bundling archive to {OUTPUT_JSON}...")
    bundle = []

    for p in ARCHIVE_DIR.rglob('*.md'):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse Frontmatter
            meta = {}
            body = content
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    fm_lines = parts[1].strip().split('\n')
                    for line in fm_lines:
                        if ':' in line:
                            k, v = line.split(':', 1)
                            val = v.strip()
                            # Try to parse JSON lists in frontmatter
                            if val.startswith('[') and val.endswith(']'):
                                try:
                                    val = json.loads(val)
                                except:
                                    pass
                            meta[k.strip()] = val
                    body = parts[2].strip()

            entry = {
                "filename": p.name,
                "path": p.relative_to(ROOT_DIR).as_posix(),
                "metadata": meta,
                "content": body
            }
            bundle.append(entry)
        except Exception as e:
            print(f"[WARN] Failed to process {p.name}: {e}")

    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(bundle, f, indent=2)
    
    print(f"[SUCCESS] Bundled {len(bundle)} files into JSON.")

def create_zip_archive():
    """Zips the archive and indexes directories."""
    if not ARCHIVE_DIR.exists():
        print(f"[ERROR] Archive directory not found.")
        return

    print(f"[INFO] Creating zip archive at {OUTPUT_ZIP}...")
    
    with zipfile.ZipFile(OUTPUT_ZIP, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add Archive
        for root, _, files in os.walk(ARCHIVE_DIR):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(ROOT_DIR)
                zf.write(file_path, arcname)
        
        # Add Indexes
        if INDEX_DIR.exists():
            for root, _, files in os.walk(INDEX_DIR):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(ROOT_DIR)
                    zf.write(file_path, arcname)

    print(f"[SUCCESS] Archive zipped successfully.")

def verify_bundle():
    """Verifies the integrity of the generated JSON bundle."""
    if not OUTPUT_JSON.exists():
        print(f"[ERROR] Bundle file not found: {OUTPUT_JSON}")
        return

    print(f"[INFO] Verifying {OUTPUT_JSON}...")
    try:
        with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        issues = []
        for i, entry in enumerate(data):
            fname = entry.get("filename", f"Entry {i}")
            meta = entry.get("metadata", {})
            
            # Critical fields check
            if not meta.get("patterndomain"):
                issues.append(f"[MISSING] {fname}: patterndomain")
            if not meta.get("maturationstage"):
                issues.append(f"[MISSING] {fname}: maturationstage")
            
            # Type check tags (should be a list if parsed correctly)
            tags = meta.get("patterntags")
            if tags is not None and not isinstance(tags, list):
                 issues.append(f"[TYPE] {fname}: patterntags is {type(tags)}, expected list")

        if issues:
            print(f"[WARN] Found {len(issues)} issues:")
            for issue in issues:
                print(issue)
        else:
            print(f"[SUCCESS] Verified {len(data)} entries. Metadata structure looks correct.")

    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Knowledge Archive Export Toolkit")
    parser.add_argument("--json", action="store_true", help="Export to JSON bundle")
    parser.add_argument("--zip", action="store_true", help="Export to ZIP archive")
    parser.add_argument("--verify", action="store_true", help="Verify the generated JSON bundle")
    parser.add_argument("--all", action="store_true", help="Export both")
    
    args = parser.parse_args()

    if args.json or args.all:
        bundle_to_json()
    if args.zip or args.all:
        create_zip_archive()
    if args.verify or args.all:
        verify_bundle()
    
    if not (args.json or args.zip or args.verify or args.all):
        print("[INFO] No action specified. Use --json, --zip, --verify, or --all.")