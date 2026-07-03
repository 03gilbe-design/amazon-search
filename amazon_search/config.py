"""Load API keys from ~/.tiktok_keys."""
import os
from pathlib import Path


def load_api_key(key_name: str) -> str:
    keys_file = Path.home() / ".tiktok_keys"
    if not keys_file.exists():
        raise FileNotFoundError(f"{keys_file} not found")
    with open(keys_file) as f:
        for line in f:
            if line.startswith(key_name + "="):
                return line.split("=", 1)[1].strip()
    raise ValueError(f"{key_name} not found in {keys_file}")


def setup_env() -> None:
    for env_var, key_name in [
        ("CANOPY_KEY", "CANOPY_KEY"),
        ("SERPAPI_KEY", "SERPAPI_KEY"),
        ("SEARCHAPI_KEY", "SEARCHAPI_KEY"),
        ("GROQ_API_KEY", "GROQ_KEY"),
    ]:
        try:
            os.environ[env_var] = load_api_key(key_name)
        except (FileNotFoundError, ValueError):
            pass  # Missing key is handled at usage time


setup_env()
