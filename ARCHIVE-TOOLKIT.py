import os
import csv
import json
import argparse
import re
from pathlib import Path
import datetime

# Configuration
ROOT_DIR = Path.cwd()
STAGING_DIR = ROOT_DIR / "notebooklm-import-raw"
ARCHIVE_DIR = ROOT_DIR / "knowledge-archive"
TAXONOMY_DIR = ARCHIVE_DIR / "taxonomy"
MANIFEST_FILE = ROOT_DIR / "classification-manifest.csv"

# Taxonomy Stubs (Placeholder defaults as actual JSONs were not provided)
DEFAULT_DOMAINS = [
    {"id": "forensic-psychology", "description": "Analysis of psychological manipulation and coercive control."},
    {"id": "tradecraft", "description": "Operational tactics, techniques, and procedures."},
    {"id": "neurobiology", "description": "Biological and neurological impacts of psychological stress."},
    {"id": "social-engineering", "description": "Manipulation of social structures and human behavior."},
    {"id": "tactical-doctrine", "description": "Strategic principles of non-kinetic warfare and asymmetric engagement."}
]

DEFAULT_TAGS = [
    {"id": "humint", "description": "Human Intelligence"},
    {"id": "non-kinetic", "description": "Non-physical warfare tactics"},
    {"id": "gaslighting", "description": "Psychological manipulation to sow doubt"},
    {"id": "c-ptsd", "description": "Complex Post-Traumatic Stress Disorder"},
    {"id": "civilian-weaponization", "description": "Use of civilians as proxies in conflict"},
    {"id": "smear-campaign", "description": "Systematic reputation destruction"},
    {"id": "cognitive-collapse", "description": "Breakdown of cognitive function under stress"},
    {"id": "plausible-deniability", "description": "Ability to deny involvement in operations"},
    {"id": "code-snippet", "description": "Technical implementation details"},
    {"id": "reflection", "description": "Personal retrospective analysis"}
]

def initialize_directories():
    """
    Objective 1: Directory Initialization
    Initialize the directory skeleton and ensure taxonomy folder is populated.
    """
    dirs = [
        STAGING_DIR,
        ARCHIVE_DIR,
        TAXONOMY_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        print(f"Verified directory: {d}")
    
    # Create dummy taxonomy stubs if missing
    domain_file = TAXONOMY_DIR / "domains.json"
    if not domain_file.exists():
        with open(domain_file, 'w') as f:
            json.dump(DEFAULT_DOMAINS, f, indent=2)
            
    tags_file = TAXONOMY_DIR / "tags.json"
    if not tags_file.exists():
        with open(tags_file, 'w') as f:
            json.dump(DEFAULT_TAGS, f, indent=2)

def extract_snippet(content, word_count=75):
    """
    Objective 4: Refine Indexing Logic
    Extract the first 50-100 words of content, skipping YAML frontmatter.
    """
    # Remove YAML frontmatter if present (content between --- and --- at start)
    content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
    
    # Basic cleanup of markdown symbols could be added here if needed
    words = content.split()
    snippet = ' '.join(words[:word_count])
    return snippet

def suggest_metadata(content, filename):
    """
    Objective 3: Heuristic for initial classification
    Suggest initial patterndomain, patterntags, and maturationstage based on content.
    """
    lower_content = content.lower()
    domain = "social-engineering" # Default fallback
    tags = []
    stage = "experientialdata"
    
    if "doctrine" in lower_content:
        stage = "formalizedframework"
    
    # Simple heuristics based on keywords
    if "code" in lower_content or "function" in lower_content or "def " in lower_content:
        domain = "tradecraft"
        tags.append("code-snippet")
    elif "journal" in lower_content or "diary" in lower_content or "felt" in lower_content:
        domain = "forensic-psychology"
        tags.append("reflection")
        
    return domain, ";".join(tags), stage

def generate_manifest():
    """
    Objective 3: Phase 2 Initiation (Manifest Generation)
    Analyze files in staging and generate classification-manifest.csv.
    """
    if not STAGING_DIR.exists():
        print(f"Error: Staging directory {STAGING_DIR} not found.")
        return

    files_data = []
    
    # Objective 2: Fix pathing logic to ensure it handles nested directories (rglob)
    for file_path in STAGING_DIR.rglob("*.md"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            snippet = extract_snippet(content)
            domain, tags, stage = suggest_metadata(content, file_path.name)
            
            files_data.append({
                "original_path": str(file_path.relative_to(ROOT_DIR)),
                "filename": file_path.name,
                "suggested_domain": domain,
                "suggested_tags": tags,
                "maturation_stage": stage,
                "validation_status": "singleobservation",
                "instructional_readiness": "internalreference",
                "experience_date": datetime.date.today().isoformat(),
                "provenance": "personaldocumentation",
                "source_url": "",
                "related_links": "",
                "snippet": snippet,
                "status": "pending"
            })
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    with open(MANIFEST_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["original_path", "filename", "suggested_domain", "suggested_tags", 
                      "maturation_stage", "validation_status", "instructional_readiness",
                      "experience_date", "provenance", "source_url", "related_links", "snippet", "status"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data in files_data:
            writer.writerow(data)
            
    print(f"Manifest generated at {MANIFEST_FILE} with {len(files_data)} entries.")
    
    # Display first 5 for immediate feedback as requested
    print("\n--- First 5 Files Analysis ---")
    for i, data in enumerate(files_data[:5]):
        print(f"{i+1}. {data['filename']}")
        print(f"   Domain: {data['suggested_domain']}")
        print(f"   Tags: {data['suggested_tags']}")
        print(f"   Snippet: {data['snippet'][:100]}...")

def organize_archive():
    """
    Objective 3: Phase 3 (Organization)
    Move files based on manifest and inject metadata.
    """
    if not MANIFEST_FILE.exists():
        print(f"Error: Manifest {MANIFEST_FILE} not found. Run 'init' first.")
        return

    print("Starting Phase 3: Organization...")
    
    with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Maturation stage to folder mapping
    stage_map = {
        "experientialdata": "experiential_data",
        "analyticalsynthesis": "analytical_synthesis",
        "formalizedframework": "formalized_frameworks"
    }

    success_count = 0
    
    for row in rows:
        try:
            source_path = ROOT_DIR / row["original_path"]
            if not source_path.exists():
                print(f"Skipping missing file: {row['original_path']}")
                continue

            # Extract metadata
            domain = row.get("suggested_domain", "mixed-pattern")
            stage = row.get("maturation_stage", "experientialdata")
            tags = [t.strip() for t in row.get("suggested_tags", "").split(";") if t.strip()]
            links = [l.strip() for l in row.get("related_links", "").split(";") if l.strip()]
            
            # Determine target directory
            stage_folder = stage_map.get(stage, "experiential_data")
            target_dir = ARCHIVE_DIR / domain / stage_folder
            target_dir.mkdir(parents=True, exist_ok=True)

            # Generate new filename: domain-slug-date.md
            slug = re.sub(r'[^a-z0-9-]', '', row["filename"].lower().replace('.md', '').replace(' ', '-'))
            import_date = datetime.date.today().isoformat()
            new_filename = f"{domain}-{slug}-{import_date}.md"
            target_path = target_dir / new_filename

            # Prepare YAML Frontmatter
            frontmatter = f"""---
patterndomain: {domain}
maturationstage: {stage}
patterntags: {json.dumps(tags)}
validationstatus: {row.get("validation_status", "singleobservation")}
instructionalreadiness: {row.get("instructional_readiness", "internalreference")}
temporal_context:
  experience_date: {row.get("experience_date", import_date)}
  analysis_date: {import_date}
provenance: {row.get("provenance", "personaldocumentation")}
source: "notebooklm"
source_url: "{row.get("source_url", "")}"
related_links: {json.dumps(links)}
import_date: {import_date}
---

"""
            # Read original content, strip existing frontmatter, and write new file
            with open(source_path, 'r', encoding='utf-8') as f:
                content = f.read()
                content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)

            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(frontmatter + content)

            # Remove original file
            os.remove(source_path)
            success_count += 1
            print(f"Moved: {row['filename']} -> {target_path.relative_to(ROOT_DIR)}")

        except Exception as e:
            print(f"Error processing {row.get('filename', 'unknown')}: {e}")

    print(f"Organization complete. {success_count} files processed.")

def validate_manifest():
    """
    Objective: Validate the manifest against taxonomy files.
    """
    if not MANIFEST_FILE.exists():
        print(f"Error: Manifest {MANIFEST_FILE} not found. Run 'init' first.")
        return

    # Load Taxonomy
    domains_file = TAXONOMY_DIR / "domains.json"
    tags_file = TAXONOMY_DIR / "tags.json"
    
    valid_domains = set()
    valid_tags = set()

    try:
        if domains_file.exists():
            with open(domains_file, 'r') as f:
                data = json.load(f)
                # Handle both list of strings and list of dicts with 'id'
                if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    valid_domains = {item.get('id') for item in data}
                elif isinstance(data, list):
                    valid_domains = set(data)
        
        if tags_file.exists():
            with open(tags_file, 'r') as f:
                data = json.load(f)
                if data and isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    valid_tags = {item.get('id') for item in data}
                elif isinstance(data, list):
                    valid_tags = set(data)
    except Exception as e:
        print(f"Error loading taxonomy: {e}")
        return

    print("Validating manifest against taxonomy...")
    issues = []
    
    with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row['filename']
            domain = row.get('suggested_domain')
            tags = [t.strip() for t in row.get('suggested_tags', '').split(';') if t.strip()]
            
            if domain and domain not in valid_domains:
                issues.append(f"File '{filename}': Invalid domain '{domain}'. Expected one of {sorted(list(valid_domains))}")
            
            for tag in tags:
                if tag not in valid_tags:
                    issues.append(f"File '{filename}': Invalid tag '{tag}'. Expected one of {sorted(list(valid_tags))}")

    if issues:
        print(f"Validation failed with {len(issues)} issues:")
        for issue in issues[:10]: # Limit output
            print(f" - {issue}")
        if len(issues) > 10:
            print(f" ... and {len(issues) - 10} more.")
    else:
        print("Validation successful! Manifest is compliant with taxonomy.")

def generate_indices():
    """
    Objective 4: Indexing
    Generate markdown indices based on the organized archive.
    """
    print("Generating indices...")
    indices_dir = ROOT_DIR / "_indexes"
    indices_dir.mkdir(exist_ok=True)
    
    # Scan archive
    index_data = {} # domain -> list of files
    
    for file_path in ARCHIVE_DIR.rglob("*.md"):
        if "taxonomy" in file_path.parts:
            continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract frontmatter domain using regex
            match = re.search(r'patterndomain:\s*(.+)', content)
            if match:
                domain = match.group(1).strip()
                if domain not in index_data:
                    index_data[domain] = []
                
                index_data[domain].append({
                    "filename": file_path.name,
                    "path": str(file_path.relative_to(ROOT_DIR)).replace('\\', '/'),
                    "snippet": extract_snippet(content)
                })
        except Exception as e:
            print(f"Skipping {file_path.name}: {e}")

    # Write Index Files
    for domain, files in index_data.items():
        index_file = indices_dir / f"{domain}-index.md"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(f"# Index: {domain}\n\n")
            for entry in files:
                f.write(f"## [{entry['filename']}](../{entry['path']})\n")
                f.write(f"{entry['snippet']}...\n\n")
    
    print(f"Generated indices for {len(index_data)} domains.")

def generate_report():
    """
    Objective: Generate a summary report of the archive.
    """
    print("Generating Archive Report...")
    
    if not ARCHIVE_DIR.exists():
        print("Archive directory not found.")
        return

    stats = {
        "total_files": 0,
        "domains": {},
        "stages": {}
    }

    for file_path in ARCHIVE_DIR.rglob("*.md"):
        if "taxonomy" in file_path.parts or file_path.name.lower() == "readme.md":
            continue
            
        stats["total_files"] += 1
        
        try:
            # Structure: ARCHIVE_DIR / domain / stage / file
            rel_parts = file_path.relative_to(ARCHIVE_DIR).parts
            if len(rel_parts) >= 2:
                domain = rel_parts[0]
                stage = rel_parts[1]
                
                stats["domains"][domain] = stats["domains"].get(domain, 0) + 1
                stats["stages"][stage] = stats["stages"].get(stage, 0) + 1
        except Exception:
            pass

    print("\n=== Knowledge Archive Statistics ===")
    print(f"Total Documents: {stats['total_files']}")
    
    print("\n--- By Domain ---")
    for domain, count in sorted(stats["domains"].items()):
        print(f"  {domain}: {count}")
        
    print("\n--- By Maturation Stage ---")
    for stage, count in sorted(stats["stages"].items()):
        print(f"  {stage}: {count}")
    print("====================================")

def main():
    parser = argparse.ArgumentParser(description="Knowledge Archive Migration Toolkit")
    parser.add_argument("command", choices=["init", "run", "validate", "index", "report"], help="Command to execute")
    
    args = parser.parse_args()
    
    if args.command == "init":
        initialize_directories()
        generate_manifest()
    elif args.command == "validate":
        validate_manifest()
    elif args.command == "run":
        organize_archive()
    elif args.command == "index":
        generate_indices()
    elif args.command == "report":
        generate_report()

if __name__ == "__main__":
    main()