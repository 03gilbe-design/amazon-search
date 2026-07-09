import sys
import os
import json
from pathlib import Path

# Aggiungi cartella al path
sys.path.append(rstr(Path.home() / "amazon_search", ".claude", "worktrees", "amazon-improvements", "webui"))

from app import JOBS, _build_dataset_job, _precalculate_offline

print("Forcing precalculation script...")
# Assicuriamoci che il dataset sia inizializzato
if "dataset" not in JOBS:
    _build_dataset_job()

job = JOBS["dataset"]
# Forza rimozione cache
SCENES_PATH = Path.home() / ".amazon_search_offline_scenes.json"
if SCENES_PATH.exists():
    SCENES_PATH.unlink()

# Calcola e salva bloccante
print("Running _precalculate_offline synchronously...")
_precalculate_offline(job)

if SCENES_PATH.exists():
    print(f"Success! Created {SCENES_PATH}")
else:
    print("Failed to create scenes JSON.")
