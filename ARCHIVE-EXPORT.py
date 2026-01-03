import json
import datetime
from pathlib import Path

# Configuration
ROOT_DIR = Path.cwd()
ARCHIVE_DIR = ROOT_DIR / "knowledge-archive"
INDEX_DIR = ROOT_DIR / "_indexes"
BACKUP_FILENAME = f"knowledge-archive-backup-{datetime.date.today().isoformat()}.json"
EXPORT_FILE = ROOT_DIR / BACKUP_FILENAME

def export_archive():
    """
    Bundles the knowledge-archive and _indexes directories into a single JSON file.
    """
    print(f"Initiating export to {EXPORT_FILE}...")
    
    if not ARCHIVE_DIR.exists():
        print(f"Error: Archive directory {ARCHIVE_DIR} not found.")
        return

    backup_payload = {
        "meta": {
            "export_date": datetime.datetime.now().isoformat(),
            "source_root": str(ROOT_DIR),
            "version": "1.0"
        },
        "files": []
    }

    # Helper to add files
    def add_directory(directory):
        if not directory.exists():
            return
        
        print(f"Scanning {directory.name}...")
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    # Use relative path for portability
                    rel_path = file_path.relative_to(ROOT_DIR).as_posix()
                    
                    # Read content
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    
                    backup_payload["files"].append({
                        "path": rel_path,
                        "content": content
                    })
                except Exception as e:
                    print(f"Failed to read {file_path}: {e}")

    # Scan Core Directories
    add_directory(ARCHIVE_DIR)
    add_directory(INDEX_DIR)

    # Write Backup
    try:
        with open(EXPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(backup_payload, f, indent=2)
        print(f"Success: Export complete. {len(backup_payload['files'])} files bundled.")
    except Exception as e:
        print(f"Error writing backup file: {e}")

if __name__ == "__main__":
    export_archive()