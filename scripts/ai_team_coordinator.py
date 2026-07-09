import time
import random

class BaseAgent:
    def __init__(self, name, role, goal):
        self.name = name
        self.role = role
        self.goal = goal
        self.memory = []

    def log(self, message):
        print(f"[{self.role} - {self.name}] {message}")

class SemanticAnalyzerAgent(BaseAgent):
    def process_words(self, text_data):
        self.log(f"Analizzando i dati grezzi: estrazione pattern...")
        time.sleep(1) # Simula elaborazione
        # Livello 1 -> Livello 2 (Parole -> Frasi) come da appunti
        semantics = {"keyword_clusters": ["girasole", "collare in tessuto", "pattern floreale"], "noise_score": 0.8}
        self.log(f"Semantica estratta: {semantics['keyword_clusters']}")
        return semantics

class NoiseFilterAgent(BaseAgent):
    def remove_duplicates(self, data, semantics):
        self.log("Avvio RANSAC e filtraggio duplicati visuali...")
        time.sleep(1.5)
        if semantics["noise_score"] > 0.5:
            self.log("Alto livello di rumore rilevato! Scarto i doppioni certi (100% match).")
        clean_data = ["Prodotto_A_Unico", "Prodotto_B_Unico", "Prodotto_C_Unico"]
        self.log(f"Dati puliti pronti: {clean_data}")
        return clean_data

class UIOrchestratorAgent(BaseAgent):
    def generate_sunflower_view(self, clean_data):
        self.log("Organizzazione dati per interfaccia 'Sunflower'...")
        time.sleep(1)
        sunflower_nodes = {
            "center": clean_data[0],
            "satellites": clean_data[1:]
        }
        self.log(f"Interfaccia pronta. Centro: {sunflower_nodes['center']}, Satelliti: {sunflower_nodes['satellites']}")
        return sunflower_nodes

class OrchestratorCrew:
    def __init__(self):
        print("\n--- INIZIALIZZAZIONE TEAM SUPREME ---")
        self.sem_agent = SemanticAnalyzerAgent("Alpha", "Analista Semantico", "Trovare pattern Parola->Frase")
        self.noise_agent = NoiseFilterAgent("Beta", "Filtro Rumore", "Rimuovere duplicati e isolare i prodotti")
        self.ui_agent = UIOrchestratorAgent("Gamma", "Architetto UI", "Mappare i dati per l'interfaccia a raggiera")

    def kickoff(self, raw_data):
        print("\n--- AVVIO PROCESSO MULTI-AGENTE ---")
        
        # 1. Analisi Semantica
        semantics = self.sem_agent.process_words(raw_data)
        
        # 2. Rimozione Rumore basata sulla semantica
        clean_data = self.noise_agent.remove_duplicates(raw_data, semantics)
        
        # 3. Generazione Struttura UI
        final_ui_state = self.ui_agent.generate_sunflower_view(clean_data)
        
        print("\n--- PROCESSO COMPLETATO ---")
        return final_ui_state

if __name__ == "__main__":
    crew = OrchestratorCrew()
    # Dati grezzi fittizi (risultati di ricerca sporchi)
    raw_amazon_data = ["img_collare_1.jpg", "img_collare_1_duplicato.jpg", "img_collare_girasoli.jpg", "img_guinzaglio.jpg"]
    
    # Esecuzione del workflow
    risultato = crew.kickoff(raw_amazon_data)
    print(f"Stato Finale per il Frontend: {risultato}")
