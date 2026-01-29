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

# --- CONFIGURAZIONE CECCHINO (Precisione Chirurgica) ---
# Cerchiamo la frase specifica del tuo Master
TARGET_NAME_KEYWORDS = ["artificial intelligence", "data science"] 

# Cerchiamo parole che indicano un'apertura REALE (no archivi vecchi)
ACTION_KEYWORDS = ["bando", "ammissione", "selezione", "apertura", "domanda"]

# Filtro Temporale (Fondamentale)
YEAR_KEYWORDS = ["2026", "2027"]

HEADERS = {'User-Agent': 'Mozilla/5.0 (GitHub Action Unical Sniper) Gecko/20100101 Firefox/88.0'}

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
    print("--- INIZIO SCANSIONE CHIRURGICA ---")
    
    for target in TARGETS:
        print(f"Analisi: {target['nome']}...")
        try:
            response = requests.get(target['url'], headers=HEADERS, timeout=25)
            if response.status_code != 200:
                print(f"-> Errore HTTP {response.status_code}")
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # --- STRATEGIA 1: Cerca nei LINK (<a> tags) ---
            # Questo serve per trovare direttamente il PDF o la pagina di dettaglio
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                link_text = link.get_text().lower()
                link_url = link['href']
                
                # Uniamo testo del link e URL per la ricerca (a volte "bando" è nel nome del file pdf)
                full_search_string = (link_text + " " + link_url).lower()

                # VERIFICA 1: Ci sono le parole chiave del Master? (AI + Data Science)
                has_target_name = all(k in full_search_string for k in TARGET_NAME_KEYWORDS)
                
                # VERIFICA 2: C'è l'anno giusto?
                has_year = any(y in full_search_string for y in YEAR_KEYWORDS)
                
                # VERIFICA 3: C'è la parola "bando" o simili?
                has_action = any(a in full_search_string for a in ACTION_KEYWORDS)

                # Se il link soddisfa i criteri, abbiamo fatto centro
                if has_target_name and (has_year or has_action):
                    
                    # Costruisci URL assoluto se è relativo
                    if link_url.startswith("/"):
                        if "unical.it" in target['url']:
                            base_domain = "https://www.unical.it"
                        elif "demacs" in target['url']:
                            base_domain = "https://demacs.unical.it"
                        else:
                            base_domain = target['url'] # Fallback
                        final_link = base_domain + link_url
                    elif not link_url.startswith("http"):
                        final_link = target['url'] + link_url
                    else:
                        final_link = link_url

                    msg = (f"🎯 **BERSAGLIO COLPITO!**\n\n"
                           f"Ho trovato un link specifico per il Master AI & DS!\n"
                           f"📄 *Testo trovato:* {link_text.strip()}\n"
                           f"🔗 [CLICCA QUI PER APRIRE]({final_link})\n"
                           f"Fonte: {target['nome']}")
                    
                    send_telegram_alert(msg)
                    found_something = True
                    print(f"!!! TROVATO LINK SPECIFICO: {final_link}")
                    break # Passa al prossimo sito per non spammare lo stesso link 10 volte

            # --- STRATEGIA 2: Controlla il testo circostante (Se non c'è link diretto) ---
            if not found_something:
                # Cerca blocchi di testo che contengono tutto insieme
                page_text = soup.get_text().lower()
                if all(k in page_text for k in TARGET_NAME_KEYWORDS) and \
                   any(y in page_text for y in YEAR_KEYWORDS) and \
                   any(a in page_text for a in ACTION_KEYWORDS):
                       
                       # Se siamo qui, il master c'è ma il link diretto è difficile da estrarre.
                       # Mandiamo comunque l'alert ma specificando che è generico.
                       msg = (f"⚠️ **ATTENZIONE (Check Testuale)**\n\n"
                              f"Ho rilevato 'AI & Data Science' + '2026/27' nel testo di: *{target['nome']}*\n"
                              f"Non ho trovato un link diretto al PDF, controlla la pagina.\n"
                              f"🔗 [Vai alla pagina]({target['url']})")
                       send_telegram_alert(msg)
                       found_something = True

        except Exception as e:
            print(f"Errore tecnico su {target['nome']}: {e}")

    if not found_something:
        print("Nessun target specifico rilevato.")

if __name__ == "__main__":
    check_targets()