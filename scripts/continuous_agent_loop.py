import asyncio
import sys
from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig

async def loop_autonomo():
    # Diamo all'agente tutti i permessi per usare tool, scrivere file e terminale
    config = LocalAgentConfig(
        system_instructions="""Sei un agente autonomo. Il tuo obiettivo è analizzare i dataset. 
        Non fermarti finché non hai finito tutto. Se incontri un errore, correggilo e continua.""",
        capabilities=CapabilitiesConfig(), 
    )

    print("🤖 Avvio Loop Agente Autonomo...")
    
    async with Agent(config) as agent:
        # Loop infinito: l'IA ragiona, agisce, guarda il risultato e decide se continuare
        task = "Analizza i file JSON in questa cartella e fai il negative sampling. Continua finché non hai finito."
        
        while True:
            print(f"\n[INVIO TASK] {task}")
            response = await agent.chat(task)
            
            # Stampiamo cosa sta facendo/pensando l'agente
            risposta_testuale = ""
            async for token in response:
                risposta_testuale += token
                sys.stdout.write(token)
                sys.stdout.flush()
            
            # Condizione di uscita (se l'agente dichiara di aver finito)
            if "OBIETTIVO COMPLETATO" in risposta_testuale.upper():
                print("\n\n✅ L'agente ha terminato il loop con successo!")
                break
            
            # Se non ha finito, gli passiamo indietro l'output o chiediamo il prossimo passo
            task = "Continua con il prossimo passo. Se hai finito, scrivi 'OBIETTIVO COMPLETATO'."

if __name__ == "__main__":
    asyncio.run(loop_autonomo())
