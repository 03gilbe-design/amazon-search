import json
import glob
from pathlib import Path

home = Path.home()
files = glob.glob(str(home / '.amazon_search_offline*.json'))
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
            print(f'{Path(f).name}: {len(data.get("products", []))} prodotti, Query: {data.get("query", "N/A")}')
    except Exception as e:
        print(f'{Path(f).name}: error {e}')
