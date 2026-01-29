import requests
from bs4 import BeautifulSoup
import os
import sys

# --- CONFIGURAZIONE TARGET ---
TARGETS = [
    {"nome": "DeMaCS - Master", "url": "https://demacs.unical.it/didattica/master/"},
    {"nome": "Matematica Unical - Master", "url": "https://www.mat.unical.it/didattica/master/"},
    {"nome": "DESF - Post Laurea", "url": "https://desf.unical.it/didattica/formazione-post-laurea/"},
    {"nome": "DESF - Didattica", "url": "https://desf.unical.it/didattica/"},
    {"nome": "Unical - Bacheca Alta Formazione", "url": "https://www.unical.it/didattica/offerta-formativa/master-e-alta-formazione/"},
    {"nome": "Unical - Offerta Formativa", "url": "https://www.unical.it/didattica/offerta-formativa/master/"}
]

# --- KEYWORDS ---
KEYWORDS_ARGOMENTO = ["data science", "artificial intelligence", "intelligenza artificiale", "bando unico"]
KEYWORDS_AZIONE = ["bando", "ammissione", "iscrizione", "domanda", "selezione"]
KEYWORDS_ANNO = ["2026", "2027"]

HEADERS = {'User-Agent': 'Mozilla/5.0 (GitHub Action Unical Sniper) Gecko/20100101 Firefox/88.0'}

def send_telegram_alert(message):
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("ERRORE: Credenziali Telegram mancanti nelle Variabili d'Ambiente!")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=payload)
        print(f"Notifica Telegram inviata: {message}")
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

def check_targets():
    found_something = False
    
    for target in TARGETS:
        print(f"Controllando: {target['nome']}...")
        try:
            response = requests.get(target['url'], headers=HEADERS, timeout=20)
            if response.status_code != 200:
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text().lower()
            
            # Logica di matching
            has_argomento = any(k in text for k in KEYWORDS_ARGOMENTO)
            has_azione = any(k in text for k in KEYWORDS_AZIONE)
            has_anno = any(k in text for k in KEYWORDS_ANNO)
            
            if has_argomento and has_azione and has_anno:
                msg = (f"🚨 **ALLARME UNICAL SNIPER** 🚨\n\n"
                       f"Trovato possibile bando su: *{target['nome']}*\n"
                       f"🔗 [Clicca qui per vedere]({target['url']})")
                send_telegram_alert(msg)
                found_something = True
                
        except Exception as e:
            print(f"Errore su {target['nome']}: {e}")

    if not found_something:
        print("Nessun bando trovato in questo ciclo.")

if __name__ == "__main__":
    check_targets()