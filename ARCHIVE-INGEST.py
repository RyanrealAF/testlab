import tkinter as tk
import datetime
import re
from pathlib import Path

# Configuration
ROOT_DIR = Path.cwd()
STAGING_DIR = ROOT_DIR / "notebooklm-import-raw"

def sanitize_filename(text):
    """Create a safe filename slug from the title text."""
    # Take first 50 chars, alphanumeric + dashes
    slug = re.sub(r'[^a-zA-Z0-9\s-]', '', text).strip().lower()
    slug = re.sub(r'[\s-]+', '-', slug)
    return slug[:50]

def ingest_from_clipboard():
    """Reads text from clipboard and saves to staging."""
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        # Use tkinter to access clipboard
        root = tk.Tk()
        root.withdraw() # Hide the main window
        try:
            content = root.clipboard_get()
        except tk.TclError:
            print("[ERROR] Clipboard is empty or contains non-text data.")
            root.destroy()
            return
        root.destroy()
    except Exception as e:
        print(f"[ERROR] Failed to access clipboard: {e}")
        return

    if not content or not content.strip():
        print("[WARN] Clipboard content is empty.")
        return

    # Generate Filename from first non-empty line
    lines = content.splitlines()
    title_candidate = "untitled"
    for line in lines:
        if line.strip():
            title_candidate = line.strip()
            break
            
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    slug = sanitize_filename(title_candidate)
    if not slug:
        slug = "note"
        
    filename = f"{timestamp}-{slug}.md"
    file_path = STAGING_DIR / filename
    
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[SUCCESS] Ingested to staging: {filename}")
        print(f"          Size: {len(content)} characters")
    except Exception as e:
        print(f"[ERROR] Failed to write file: {e}")

if __name__ == "__main__":
    ingest_from_clipboard()