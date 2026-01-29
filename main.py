import requests
from bs4 import BeautifulSoup
import os
import sys

# --- CONFIGURAZIONE TARGET ---
TARGETS = [
    {"nome": "DeMaCS - Master", "url": "https://demacs.unical.it/didattica/master/"},
    {"nome": "Matematica Unical - Master", "url": "https://www.mat.unical.it/didattica/master/"},
    {"nome": "DESF - Post Laurea", "url": "https://desf.unical.it/didattica/formazione-post-laurea/"},
    {"nome": "Unical - Bacheca Alta Formazione", "url": "https://www.unical.it/didattica/offerta-formativa/master-e-alta-formazione/"},
    {"nome": "Unical - Offerta Formativa", "url": "https://www.unical.it/didattica/offerta-formativa/master/"}
]

# --- CONFIGURAZIONE PAROLE CHIAVE (User Defined) ---

# 1. NOME DEL MASTER (Basta trovarne UNO)
# Copre sia il nome lungo ufficiale, sia gli acronimi, sia le varianti comuni
NAME_VARIANTS = [
    "ai&ds", 
    "ai & ds", 
    "master universitario di ii livello in artificial intelligence & data science",
    "artificial intelligence & data science", # Variante senza "Master..." per sicurezza
    "artificial intelligence and data science" # Variante con "and"
]

# 2. EDIZIONE (Basta trovarne UNO)
EDITION_VARIANTS = [
    "quarta", 
    "4", 
    "iv"
]

# 3. ANNO ACCADEMICO (Basta trovarne UNO)
YEAR_VARIANTS = [
    "2026/2027", 
    "2026-2027", 
    "2026 2027"
]

# 4. BONUS TRIGGER (Se trova questo associato al master, vince subito)
SPECIAL_KEYWORDS = [
    "patti territoriali"
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (GitHub Action Unical Sniper Elite) Gecko/20100101 Firefox/88.0'}

def send_telegram_alert(message):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("ERRORE: Credenziali Telegram mancanti!")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
        print(f"Notifica Telegram inviata.")
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

def check_targets():
    found_something = False
    print("--- INIZIO SCANSIONE ELITE (V5) ---")
    
    for target in TARGETS:
        print(f"Analisi: {target['nome']}...")
        try:
            response = requests.get(target['url'], headers=HEADERS, timeout=25)
            if response.status_code != 200:
                print(f"-> Errore HTTP {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # --- SCANSIONE LINK ---
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                # Normalizziamo tutto in minuscolo per il confronto
                link_text = link.get_text().lower().strip()
                link_url = link['href'].lower()
                full_string = link_text + " " + link_url 

                # --- LOGICA DI ABBINAMENTO ---
                
                # Check 1: È il master giusto?
                has_name = any(k in full_string for k in NAME_VARIANTS)
                
                # Check 2: È l'edizione/anno giusto?
                has_edition = any(k in full_string for k in EDITION_VARIANTS)
                has_year = any(k in full_string for k in YEAR_VARIANTS)
                has_special = any(k in full_string for k in SPECIAL_KEYWORDS)

                # CONDIZIONE DI ALLARME:
                # Deve esserci il NOME + (Edizione OPPURE Anno OPPURE Patti Territoriali)
                if has_name and (has_edition or has_year or has_special):
                    
                    # Ricostruzione Link
                    original_url = link['href']
                    if original_url.startswith("/"):
                        base = "https://demacs.unical.it" if "demacs" in target['url'] else "https://www.unical.it"
                        final_link = base + original_url
                    elif not original_url.startswith("http"):
                        final_link = target['url'] + original_url
                    else:
                        final_link = original_url

                    msg = (f"🎯 **BERSAGLIOCENTRATO!**\n\n"
                           f"Trovato bando compatibile!\n"
                           f"📄 *Testo:* {link_text}\n"
                           f"🔗 [CLICCA QUI]({final_link})\n"
                           f"Fonte: {target['nome']}")
                    
                    send_telegram_alert(msg)
                    found_something = True
                    print(f"!!! TROVATO: {final_link}")
                    break 

        except Exception as e:
            print(f"Errore tecnico su {target['nome']}: {e}")

    if not found_something:
        print("Nessun target rilevato. Continuo a monitorare.")

if __name__ == "__main__":
    check_targets()