import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import os
import sys
from pathlib import Path
import re

# Configuration
TOOLKIT_SCRIPT = "ARCHIVE-TOOLKIT.py"
CLEANUP_SCRIPT = "ARCHIVE-CLEANUP.py"
EXPORT_SCRIPT = "ARCHIVE-EXPORT.py"
INGEST_SCRIPT = "ARCHIVE-INGEST.py"
MANIFEST_FILE = "classification-manifest.csv"

class ArchiveDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Knowledge Archive Controller")
        self.root.geometry("900x650")
        
        # Configure Styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TButton", padding=6, font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"))
        self.style.configure("Subheader.TLabelframe.Label", font=("Segoe UI", 11, "bold"))

        # Main Container
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Label(header_frame, text="Knowledge Archive Migration Toolkit", style="Header.TLabel").pack(side=tk.LEFT)
        
        # Tabs
        self.tabs = ttk.Notebook(self.main_frame)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        # Dashboard Tab
        self.dashboard_tab = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(self.dashboard_tab, text="Dashboard")
        self.setup_dashboard_tab()

        # Search Tab
        self.search_tab = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(self.search_tab, text="Search Archive")
        self.setup_search_tab()

        # Help Tab
        self.help_tab = ttk.Frame(self.tabs, padding=10)
        self.tabs.add(self.help_tab, text="Help / Directive")
        self.setup_help_tab()

        # Status Bar
        self.status_var = tk.StringVar(value="System Ready")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5)
        self.status_bar.pack(fill=tk.X, pady=(10, 0))

    def setup_dashboard_tab(self):
        # Content Grid
        self.content_frame = ttk.Frame(self.dashboard_tab)
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left Column: Controls
        self.controls_column = ttk.Frame(self.content_frame)
        self.controls_column.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        
        # Workflow Section
        self.workflow_frame = ttk.LabelFrame(self.controls_column, text="Migration Workflow", style="Subheader.TLabelframe", padding="10")
        self.workflow_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.create_step_btn("1. Initialize & Scan", "init", "Generates manifest from staging")
        self.create_step_btn("2. Validate Metadata", "validate", "Checks manifest against taxonomy")
        self.create_step_btn("3. Organize Archive", "run", "Moves and renames files")
        self.create_step_btn("4. Generate Indices", "index", "Updates markdown indices")
        self.create_step_btn("5. View Report", "report", "Shows archive statistics")

        # Utilities Section
        self.utils_frame = ttk.LabelFrame(self.controls_column, text="Utilities", style="Subheader.TLabelframe", padding="10")
        self.utils_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Button(self.utils_frame, text="Open Manifest (CSV)", command=self.open_manifest).pack(fill=tk.X, pady=2)
        ttk.Button(self.utils_frame, text="Ingest from Clipboard", command=lambda: self.run_script(INGEST_SCRIPT)).pack(fill=tk.X, pady=2)
        ttk.Button(self.utils_frame, text="Backup Archive (JSON)", command=lambda: self.run_script(EXPORT_SCRIPT)).pack(fill=tk.X, pady=2)
        ttk.Button(self.utils_frame, text="Cleanup Staging", command=self.confirm_cleanup).pack(fill=tk.X, pady=2)

        # Right Column: Logs
        self.log_frame = ttk.LabelFrame(self.content_frame, text="System Output", style="Subheader.TLabelframe", padding="10")
        self.log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(self.log_frame, state='disabled', height=20, font=("Consolas", 9), bg="#f0f0f0")
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def create_step_btn(self, text, command, tooltip):
        btn = ttk.Button(self.workflow_frame, text=text, command=lambda: self.run_toolkit(command))
        btn.pack(fill=tk.X, pady=3)
        
    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def run_process(self, command):
        self.status_var.set(f"Executing: {' '.join(command)}...")
        self.root.update_idletasks()
        
        def target():
            try:
                # Windows specific flag to hide console window
                startupinfo = None
                if sys.platform == 'win32':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=os.getcwd(),
                    startupinfo=startupinfo
                )
                
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        self.root.after(0, self.log, output.strip())
                
                stderr = process.stderr.read()
                if stderr:
                    self.root.after(0, self.log, f"[ERROR] {stderr.strip()}")
                
                rc = process.poll()
                status_msg = "Operation Complete" if rc == 0 else f"Failed with code {rc}"
                self.root.after(0, self.status_var.set, status_msg)
                
            except Exception as e:
                self.root.after(0, self.log, f"Execution failed: {e}")
                self.root.after(0, self.status_var.set, "System Error")

        threading.Thread(target=target, daemon=True).start()

    def run_toolkit(self, arg):
        self.log(f"\n>>> python {TOOLKIT_SCRIPT} {arg}")
        self.run_process(["python", TOOLKIT_SCRIPT, arg])

    def run_script(self, script_name, args=[]):
        self.log(f"\n>>> python {script_name} {' '.join(args)}")
        self.run_process(["python", script_name] + args)

    def open_manifest(self):
        manifest_path = Path(MANIFEST_FILE)
        if manifest_path.exists():
            try:
                os.startfile(manifest_path)
                self.log(f"[INFO] Opened {manifest_path}")
            except Exception as e:
                self.log(f"[ERROR] Could not open file: {e}")
        else:
            self.log(f"[WARN] Manifest {MANIFEST_FILE} not found. Run 'Initialize' first.")

    def confirm_cleanup(self):
        if messagebox.askyesno("Confirm Cleanup", "This will permanently delete the staging directory.\n\nAre you sure?"):
            self.run_script(CLEANUP_SCRIPT, ["--force"])

    def setup_search_tab(self):
        # Search Controls
        controls_frame = ttk.Frame(self.search_tab)
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(controls_frame, text="Domain:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_domain_var = tk.StringVar()
        ttk.Entry(controls_frame, textvariable=self.search_domain_var).pack(side=tk.LEFT, padx=(0, 15), fill=tk.X, expand=True)
        
        ttk.Label(controls_frame, text="Tag:").pack(side=tk.LEFT, padx=(0, 5))
        self.search_tag_var = tk.StringVar()
        ttk.Entry(controls_frame, textvariable=self.search_tag_var).pack(side=tk.LEFT, padx=(0, 15), fill=tk.X, expand=True)
        
        ttk.Button(controls_frame, text="Search", command=self.perform_search).pack(side=tk.LEFT)

        # Treeview Frame
        tree_frame = ttk.Frame(self.search_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        # Results Treeview
        columns = ("filename", "domain", "tags", "path")
        self.results_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.results_tree.heading("filename", text="Filename")
        self.results_tree.heading("domain", text="Domain")
        self.results_tree.heading("tags", text="Tags")
        self.results_tree.heading("path", text="Path")
        
        self.results_tree.column("filename", width=200)
        self.results_tree.column("domain", width=150)
        self.results_tree.column("tags", width=200)
        self.results_tree.column("path", width=300)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscroll=scrollbar.set)
        
        self.results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.results_tree.bind("<Double-1>", self.on_result_double_click)

    def perform_search(self):
        domain_query = self.search_domain_var.get().lower().strip()
        tag_query = self.search_tag_var.get().lower().strip()
        
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
            
        archive_path = Path("knowledge-archive")
        if not archive_path.exists():
            messagebox.showerror("Error", "Archive directory not found.")
            return

        count = 0
        self.status_var.set("Searching...")
        self.root.update_idletasks()

        for file_path in archive_path.rglob("*.md"):
             if "taxonomy" in file_path.parts: continue
             
             try:
                 with open(file_path, 'r', encoding='utf-8') as f:
                     content = f.read()
                 
                 frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
                 if not frontmatter_match: continue
                 
                 fm_text = frontmatter_match.group(1)
                 
                 domain_match = re.search(r'patterndomain:\s*(.+)', fm_text)
                 domain = domain_match.group(1).strip() if domain_match else "unknown"
                 
                 tags_match = re.search(r'patterntags:\s*(.+)', fm_text)
                 tags_str = tags_match.group(1).strip() if tags_match else "[]"
                 tags_clean = tags_str.replace('[', '').replace(']', '').replace('"', '').replace("'", "")
                 tags_list = [t.strip().lower() for t in tags_clean.split(',') if t.strip()]
                 
                 match_domain = not domain_query or domain_query in domain.lower()
                 match_tag = not tag_query or any(tag_query in t for t in tags_list)
                 
                 if match_domain and match_tag:
                     self.results_tree.insert("", tk.END, values=(file_path.name, domain, tags_clean, str(file_path)))
                     count += 1
                     
             except Exception as e:
                 print(f"Error reading {file_path}: {e}")
        
        self.status_var.set(f"Search complete. Found {count} files.")

    def on_result_double_click(self, event):
        selection = self.results_tree.selection()
        if not selection: return
        item = selection[0]
        values = self.results_tree.item(item, "values")
        file_path = values[3]
        try:
            os.startfile(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")

    def setup_help_tab(self):
        self.help_text = scrolledtext.ScrolledText(self.help_tab, state='disabled', font=("Consolas", 10), padx=10, pady=10)
        self.help_text.pack(fill=tk.BOTH, expand=True)
        self.load_readme()

    def load_readme(self):
        readme_path = Path("README.md")
        content = "README.md not found."
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                content = f"Error loading README: {e}"
        self.help_text.config(state='normal')
        self.help_text.delete(1.0, tk.END)
        self.help_text.insert(tk.END, content)
        self.help_text.config(state='disabled')

if __name__ == "__main__":
    root = tk.Tk()
    app = ArchiveDashboard(root)
    root.mainloop()