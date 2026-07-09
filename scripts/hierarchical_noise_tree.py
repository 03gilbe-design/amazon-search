import json
from pathlib import Path
import re

dataset_file = Path("C:/Users/Gilberto Bizzo/.amazon_search_offline.json")
try:
    with open(dataset_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    products = data.get('products', [])
except Exception as e:
    products = []
    print("Errore:", e)

# 🌳 DEFINIZIONE DELL'ALBERO DECISIONALE DEL RUMORE (Hierarchical Noise Tree)
# Ogni nodo dell'albero è un filtro (regex) che scarta il rumore in modo progressivo.
noise_tree = {
    "Level_1_Target": {
        "description": "Scarta prodotti non per umani (Animali/Cani/Gatti)",
        "noise_regex": r"(?i)\b(cane|gatto|cani|gatti|antipulci|animale|cucciolo|pets?)\b"
    },
    "Level_2_Category": {
        "description": "Scarta prodotti Elettronici o Chimici (Creme, Massaggiatori, USB)",
        "noise_regex": r"(?i)\b(elettri|usb|massaggiator|shiatsu|crema|pomata|gel|cerott|scaldacollo|termic|riscald|smartwatch)\b"
    },
    "Level_3_Function": {
        "description": "Scarta supporti non ortopedici (Viaggio, Gonfiabili, Russamento)",
        "noise_regex": r"(?i)\b(gonfiabil|aria|viaggio|aereo|russare|snoring|tappi|mascherina|notturno|dormire letto)\b"
    }
}

print("=== AVVIO RICERCA AD ALBERO: CONTROLLO RUMORE LIVELLO PER LIVELLO ===")
print(f"Prodotti totali in ingresso: {len(products)}\n")

survivors = products.copy()
rejected_by_level = {level: [] for level in noise_tree.keys()}

# Attraversamento dell'albero
for level_name, level_data in noise_tree.items():
    print(f">> {level_name.upper()} - {level_data['description']}")
    regex = re.compile(level_data['noise_regex'])
    
    current_survivors = []
    for p in survivors:
        text_to_check = str(p.get("title", "")) + " " + str(p.get("category", ""))
        # Se matcha la regex del rumore, viene "potato" (pruned) dall'albero
        if regex.search(text_to_check):
            rejected_by_level[level_name].append(p)
        else:
            current_survivors.append(p)
    
    scartati = len(survivors) - len(current_survivors)
    survivors = current_survivors
    print(f"   [SCARTATI] Rumore a questo nodo: {scartati} prodotti")
    print(f"   [PASSATI] Prodotti sopravvissuti: {len(survivors)}\n")

print("=== RISULTATO FINALE DELLA RICERCA AD ALBERO ===")
print(f"Segnale Puro (Sopravvissuti a tutti i nodi): {len(survivors)}")
for p in survivors[:5]:
    print(f" [V] {p.get('title')[:60]}...")
print(" [...]\n")

print("Riepilogo Scarti (Rumore) per Ramo:")
for level, rejected in rejected_by_level.items():
    print(f" - {level}: {len(rejected)} prodotti scartati")

# Salvataggio
output_dir = Path("C:/Users/Gilberto Bizzo/amazon_search")
results = {
    "pure_signal": survivors,
    "pruned_noise": rejected_by_level
}

with open(output_dir / "tree_search_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4, ensure_ascii=False)

print(f"\n[OK] Risultati della navigazione ad albero salvati in: tree_search_results.json")
