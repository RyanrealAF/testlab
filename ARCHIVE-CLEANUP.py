import shutil
import argparse
from pathlib import Path

# Configuration
ROOT_DIR = Path.cwd()
STAGING_DIR = ROOT_DIR / "notebooklm-import-raw"

def cleanup_staging(force=False):
    """
    Removes the staging directory and all its contents (including empty subdirectories).
    """
    if not STAGING_DIR.exists():
        print(f"[INFO] Staging directory {STAGING_DIR} does not exist. Nothing to clean.")
        return

    # Check for remaining files (unprocessed)
    remaining_files = [f for f in STAGING_DIR.rglob("*") if f.is_file()]
    
    if remaining_files:
        print(f"[WARN] Staging directory contains {len(remaining_files)} files.")
        if not force:
            print("Files found:")
            for f in remaining_files[:5]:
                print(f" - {f.relative_to(STAGING_DIR)}")
            if len(remaining_files) > 5:
                print(" ...")
            
            confirm = input("These files may be unprocessed. Delete anyway? (yes/no): ")
            if confirm.lower() != "yes":
                print("[INFO] Cleanup aborted.")
                return

    print(f"[INFO] Removing staging area: {STAGING_DIR}...")
    try:
        shutil.rmtree(STAGING_DIR)
        print("[SUCCESS] Cleanup complete. Staging area removed.")
    except Exception as e:
        print(f"[ERROR] Failed to remove staging directory: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Staging Area Cleanup Tool")
    parser.add_argument("--force", action="store_true", help="Force deletion of remaining files without confirmation")
    args = parser.parse_args()
    
    cleanup_staging(args.force)