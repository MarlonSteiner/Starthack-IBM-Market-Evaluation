import requests
import json
import os

# --- Konfiguration ---
# WICHTIG: Setzen Sie Ihren OpenAI API-Schlüssel.
# Am besten als Umgebungsvariable: export OPENAI_API_KEY='dein_schlüssel'
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_API_URL = "https://api.openai.com/v1/responses"

def hole_nachrichten_direkt_von_openai():
    """
    Sendet eine Anfrage an die OpenAI API und bittet um eine JSON-formatierte Antwort.
    """
    if OPENAI_API_KEY == "DEIN_OPENAI_API_SCHLÜSSEL":
        print("Fehler: Bitte setzen Sie Ihren OpenAI API-Schlüssel.")
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    # Dies ist der entscheidende Teil: Ein präziser Prompt, der die KI anweist,
    # die Websuche zu nutzen und die Ausgabe als JSON zu formatieren.
    prompt = """
    Führe eine Websuche nach den wichtigsten Finanznachrichten der letzten Stunde durch.
    Formatiere deine gesamte Antwort als ein valides JSON-Array. 
    Jeder Eintrag im Array soll ein Objekt sein, das eine einzelne Nachricht repräsentiert.
    Jedes Objekt muss genau drei Schlüssel haben:
    1. "URL": der direkte Link zum Originalartikel.
    2. "Quelle": der Name der Nachrichtenseite (z.B. "Bloomberg", "Reuters").
    3. "Inhalt": eine von dir erstellte, detaillierte Zusammenfassung des Artikels.
    
    Gib nichts anderes als dieses JSON-Array aus.
    """
    
    payload = {
        "model": "gpt-5", # oder ein anderes Modell, das Web Search unterstützt
        "tools": [
            {"type": "web_search"}
        ],
        "input": prompt
    }

    print("Sende Anfrage an die OpenAI API... Dies kann einen Moment dauern.")
    
    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        response_data = response.json()
        
        # Die formatierte Antwort befindet sich im 'output_text' der ersten Nachricht.
        for item in response_data:
            if item.get("type") == "message" and item.get("role") == "assistant":
                # Der Text der KI sollte der JSON-String sein, den wir angefordert haben
                json_string = item.get("output_text", "")
                
                # Bereinigen des Strings, falls er von Markdown-Codeblöcken umgeben ist
                if json_string.startswith("```json"):
                    json_string = json_string.strip("```json\n").strip("```")
                
                # Den String in ein Python-Objekt umwandeln
                return json.loads(json_string)
        
        print("Konnte keine gültige JSON-Antwort vom Modell extrahieren.")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Fehler bei der Anfrage an die OpenAI API: {e}")
        return None
    except json.JSONDecodeError:
        print("Fehler: Die Antwort des Modells war kein valides JSON.")
        # Wir geben die rohe Antwort aus, um das Problem zu diagnostizieren
        print("Rohe Modell-Antwort:", item.get("output_text", ""))
        return None

# --- Hauptausführung ---
if __name__ == "__main__":
    nachrichten_daten = hole_nachrichten_direkt_von_openai()
    
    if nachrichten_daten:
        dateiname = "openai_direct_news.json"
        with open(dateiname, 'w', encoding='utf-8') as f:
            json.dump(nachrichten_daten, f, ensure_ascii=False, indent=4)
        print(f"\n✅ Erfolgreich! {len(nachrichten_daten)} Artikel wurden in '{dateiname}' gespeichert.")
    else:
        print("\nEs konnten keine Nachrichten verarbeitet werden.")