import json
import os
import shutil
from pathlib import Path
import urllib.request

DATA_FILE = Path.home() / ".amazon_search_offline.json"
EXPORT_DIR = Path(rstr(Path.home() / "amazon_search", "duplicates_export"))

if EXPORT_DIR.exists():
    shutil.rmtree(EXPORT_DIR)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

products = data.get("products", [])
families = {}

for p in products:
    fid = p.get("family_id")
    if fid:
        if fid not in families:
            families[fid] = []
        families[fid].append(p)

duplicate_count = 0
for fid, members in families.items():
    if len(members) > 1:
        duplicate_count += 1
        fam_dir = EXPORT_DIR / f"family_{fid[:8]}_{len(members)}_items"
        fam_dir.mkdir(exist_ok=True)
        
        for idx, m in enumerate(members):
            thumb = m.get("thumbnail")
            if thumb and thumb.startswith("http"):
                try:
                    ext = thumb.split(".")[-1]
                    if len(ext) > 4: ext = "jpg"
                    safe_asin = m.get("asin", f"unknown_{idx}")
                    req = urllib.request.Request(thumb, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req, timeout=5) as response, open(fam_dir / f"{safe_asin}.{ext}", 'wb') as out_file:
                        shutil.copyfileobj(response, out_file)
                except Exception as e:
                    print(f"Errore download {thumb}: {e}")

print(f"Esportazione completata. Create {duplicate_count} cartelle di duplicati in {EXPORT_DIR.resolve()}")
