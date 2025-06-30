# processing.py
import os
import torch
from pyannote.audio import Pipeline
from whisper import load_model as load_whisper_model
from pydub import AudioSegment
import time
from imageio_ffmpeg import get_ffmpeg_exe

# Make sure pydub uses the bundled ffmpeg
AudioSegment.converter = get_ffmpeg_exe()

# --- Konfiguration ---
# Laden der API-Keys aus den Umgebungsvariablen
HUGGINGFACE_API_KEY = os.environ.get("HUGGINGFACE_API_KEY")

# Pfad für Diarisierungs-Pipeline-Modell
DIARIZATION_PIPELINE_PATH = "pyannote/speaker-diarization-3.1"


def convert_to_wav(audio_path):
    """Konvertiert eine Audiodatei ins WAV-Format, falls sie es nicht bereits ist."""
    file_extension = os.path.splitext(audio_path)[1].lower()
    if file_extension == ".wav":
        return audio_path

    try:
        sound = AudioSegment.from_file(audio_path)
        wav_path = os.path.splitext(audio_path)[0] + ".wav"
        sound.export(wav_path, format="wav")
        print(f"Successfully converted {audio_path} to {wav_path}")
        return wav_path
    except Exception as e:
        print(f"Error during audio conversion: {e}")
        raise


def run_diarization(wav_path):
    """
    Führt die Sprecher-Diarisierung mit pyannote.audio durch.
    Gibt eine Liste von Segmenten mit Sprecher-ID, Start- und Endzeit zurück.
    """
    if not HUGGINGFACE_API_KEY:
        raise ValueError("HUGGINGFACE_API_KEY ist nicht gesetzt.")

    try:
        print("Loading diarization pipeline...")
        # Lade die Pipeline mit Authentifizierungstoken
        pipeline = Pipeline.from_pretrained(
            DIARIZATION_PIPELINE_PATH,
            use_auth_token=HUGGINGFACE_API_KEY
        )
        print("Diarization pipeline loaded.")

        print(f"Starting diarization for {wav_path}...")
        diarization_result = pipeline(wav_path)
        print("Diarization complete.")

        segments = []
        for turn, _, speaker in diarization_result.itertracks(yield_label=True):
            segments.append({
                "speaker": speaker,
                "start": turn.start,
                "end": turn.end,
                "transcript": "" # Platzhalter für Transkription
            })
        
        # Sortiere Segmente nach Startzeit
        segments.sort(key=lambda x: x["start"])
        return segments

    except Exception as e:
        print(f"Error during diarization: {e}")
        raise


def run_transcription(wav_path, model_size="base"):
    """
    Führt die Transkription mit Whisper durch.
    Gibt den vollständigen Text und Wort-Zeitstempel zurück.
    """
    try:
        print(f"Loading Whisper model ({model_size})...")
        # Whisper-Modell laden
        device = "cuda" if torch.cuda.is_available() else "cpu"
        whisper_model = load_whisper_model(model_size, device=device)
        print("Whisper model loaded.")

        print(f"Starting transcription for {wav_path}...")
        transcription_result = whisper_model.transcribe(wav_path, word_timestamps=True)
        print("Transcription complete.")

        return transcription_result

    except Exception as e:
        print(f"Error during transcription: {e}")
        raise

def combine_results(diarization_segments, transcription_result):
    """

    Kombiniert die Ergebnisse von Diarisierung und Transkription.
    Fügt den transkribierten Text in die entsprechenden Sprechersegmente ein.
    """
    final_segments = []
    
    # Transcription result might contain multiple segments. We need to collect all words.
    all_words = []
    if "segments" in transcription_result:
        for segment in transcription_result["segments"]:
            if "words" in segment:
                all_words.extend(segment["words"])

    if not all_words and "text" in transcription_result:
        # Fallback for transcriptions without word timestamps
        # This is a simple assignment and might not be accurate
        if diarization_segments:
            diarization_segments[0]['transcript'] = transcription_result['text']
            return diarization_segments

    for dia_segment in diarization_segments:
        segment_text_parts = []
        for word_info in all_words:
            # Check if the word's midpoint falls within the diarization segment
            word_mid_time = (word_info.get('start', 0) + word_info.get('end', 0)) / 2
            if dia_segment['start'] <= word_mid_time < dia_segment['end']:
                segment_text_parts.append(word_info['word'])
        
        # Join words with spaces
        dia_segment['transcript'] = "".join(segment_text_parts).strip()
        final_segments.append(dia_segment)

    return final_segments

def process_audio(audio_path, model_size="base"):
    """
    Hauptverarbeitungs-Pipeline: Konvertierung, Diarisierung, Transkription, Kombination.
    """
    start_time = time.time()
    
    # 1. In WAV konvertieren (falls nötig)
    print("Step 1: Converting to WAV...")
    wav_path = convert_to_wav(audio_path)
    
    # 2. Diarisierung durchführen
    print("
Step 2: Running Diarization...")
    diarization_segments = run_diarization(wav_path)
    
    # 3. Transkription durchführen
    print("
Step 3: Running Transcription...")
    transcription_result = run_transcription(wav_path, model_size)
    
    # 4. Ergebnisse kombinieren
    print("
Step 4: Combining results...")
    final_protocol = combine_results(diarization_segments, transcription_result)

    # Aufräumen: Lösche die konvertierte WAV-Datei, wenn sie erstellt wurde
    if wav_path != audio_path and os.path.exists(wav_path):
        try:
            os.remove(wav_path)
            print(f"Cleaned up temporary WAV file: {wav_path}")
        except OSError as e:
            print(f"Error removing temporary WAV file {wav_path}: {e}")
            
    end_time = time.time()
    print(f"
Total processing time: {end_time - start_time:.2f} seconds")
    
    return {
        "protocol": final_protocol,
        "word_timestamps": "segments" in transcription_result and "words" in transcription_result["segments"][0]
    }
