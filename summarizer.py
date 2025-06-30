# summarizer.py
import os
import json
import requests
from openai import OpenAI

# --- Konfiguration ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")

# Lade Modelldefinitionen und Prompt-Template
# Dies ist eine saubere Art, die Konfiguration aus models.py zu importieren
try:
    from models import MODELS, PROMPT_TEMPLATE
except ImportError:
    # Fallback, falls die Datei direkt ausgeführt wird
    MODELS = {
        "gpt-4o": {"api": "openai", "model_id": "gpt-4o"},
        "bart-large-cnn": {"api": "huggingface", "model_id": "facebook/bart-large-cnn"}
    }
    PROMPT_TEMPLATE = "Fasse das folgende Transkript zusammen: {transcript}"


def generate_prompt(segments):
    """Erstellt den finalen Prompt aus den Segmenten und dem Template."""
    # Erstelle ein einfaches textbasiertes Transkript aus den Segmenten
    transcript_text = "
".join(
        f"{s['speaker']} ({s['start']:.2f}s - {s['end']:.2f}s): {s['transcript']}"
        for s in segments
    )
    return PROMPT_TEMPLATE.format(transcript=transcript_text)


def summarize_with_openai(model_id, prompt):
    """Ruft die OpenAI API zur Zusammenfassung auf."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY ist nicht gesetzt.")
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "You are a helpful assistant specialized in summarizing meeting protocols."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        raise


def summarize_with_huggingface(model_id, prompt):
    """Ruft die Hugging Face Inference API zur Zusammenfassung auf."""
    if not HUGGINGFACE_API_KEY:
        raise ValueError("HUGGINGFACE_API_KEY ist nicht gesetzt.")
    
    API_URL = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_length": 512,
            "min_length": 50,
            "do_sample": False
        }
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()  # Wirft einen Fehler bei 4xx oder 5xx Antworten
        result = response.json()
        return result[0]['summary_text']
    except requests.exceptions.RequestException as e:
        print(f"Error calling Hugging Face API: {e}")
        raise


def summarize_with_ollama(model_id, prompt, ollama_url):
    """Ruft eine lokale Ollama Instanz zur Zusammenfassung auf."""
    if not ollama_url:
        raise ValueError("Ollama URL is not provided.")
        
    # Standard-URL für lokale Ollama-API
    full_url = f"{ollama_url.rstrip('/')}/api/generate"

    payload = {
        "model": model_id,
        "prompt": prompt,
        "stream": False # Wir wollen die gesamte Antwort auf einmal
    }

    try:
        response = requests.post(full_url, json=payload)
        response.raise_for_status()
        
        # Die Antwort von Ollama ist ein JSON-String pro Zeile, wir nehmen die letzte
        response_data = json.loads(response.text)
        return response_data.get("response", "").strip()

    except requests.exceptions.RequestException as e:
        print(f"Error calling local Ollama API at {full_url}: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from Ollama response: {e}")
        print(f"Raw response was: {response.text}")
        raise


def run_summarization(segments, model_identifier, custom_url=None):
    """
    Hauptfunktion zur Orchestrierung der Zusammenfassung.
    Wählt die passende API basierend auf dem `model_identifier`.
    `model_identifier` kann eine `model_id` aus MODELS oder 'ollama' sein.
    `custom_url` ist die URL für die Ollama API.
    """
    prompt = generate_prompt(segments)
    
    # Prüfen, ob eine benutzerdefinierte Ollama-URL angegeben wurde
    if model_identifier == 'ollama':
        # Der eigentliche Modellname (z.B. "llama3") wird aus den request-Daten erwartet
        # Hier wird ein Standard-Modellname verwendet, falls nicht anders angegeben
        ollama_model_name = "llama3" # Standard oder aus request holen
        return summarize_with_ollama(ollama_model_name, prompt, custom_url)

    # Standard-Logik für vordefinierte Modelle
    if model_identifier not in MODELS:
        raise ValueError(f"Model '{model_identifier}' not found in defined models.")

    model_info = MODELS[model_identifier]
    api_type = model_info["api"]
    model_id = model_info["model_id"]
    
    if api_type == "openai":
        return summarize_with_openai(model_id, prompt)
    elif api_type == "huggingface":
        return summarize_with_huggingface(model_id, prompt)
    else:
        raise NotImplementedError(f"API type '{api_type}' is not supported.")

