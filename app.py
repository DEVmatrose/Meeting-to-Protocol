from flask import Flask, request, jsonify
import os
import uuid
import threading
import json

# Import the processing and summarization logic
from processing import process_audio
from summarizer import run_summarization

app = Flask(__name__)
# Load API Key from environment variable
API_KEY = os.environ.get("MICROSERVICE_API_KEY", "your_default_secret_key")

# --- Job Management ---
JOB_DIR = "job_data"
os.makedirs(JOB_DIR, exist_ok=True)

def get_job_status_from_file(job_id):
    status_file = os.path.join(JOB_DIR, f"{job_id}_status.json")
    if os.path.exists(status_file):
        try:
            with open(status_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading status file {status_file}: {e}")
    return None

def save_job_status_to_file(job_id, status_data):
    status_file = os.path.join(JOB_DIR, f"{job_id}_status.json")
    try:
        with open(status_file, 'w') as f:
            json.dump(status_data, f)
    except IOError as e:
        print(f"Error writing status file {status_file}: {e}")

def get_job_results_from_file(job_id):
    results_file = os.path.join(JOB_DIR, f"{job_id}_results.json")
    if os.path.exists(results_file):
        try:
            with open(results_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error reading results file {results_file}: {e}")
    return None

def save_job_results_to_file(job_id, results_data):
    results_file = os.path.join(JOB_DIR, f"{job_id}_results.json")
    try:
        with open(results_file, 'w') as f:
            json.dump(results_data, f)
    except IOError as e:
        print(f"Error writing results file {results_file}: {e}")

# --- API Key Middleware ---
@app.before_request
def before_request_check():
    if request.path.startswith(('/process', '/status', '/results', '/summarize')):
        if 'X-API-Key' not in request.headers or request.headers['X-API-Key'] != API_KEY:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

# --- Routes ---
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok", "message": "Microservice is running"})

@app.route('/process', methods=['POST'])
def start_processing_audio():
    if 'audio_file' not in request.files:
        return jsonify({"status": "error", "message": "No audio_file part"}), 400
    file = request.files['audio_file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400

    job_id = str(uuid.uuid4())
    temp_audio_path = os.path.join(JOB_DIR, f"{job_id}_{file.filename}")
    try:
        file.save(temp_audio_path)
        model_size = request.form.get('model_size', 'base')
        initial_status = {"job_id": job_id, "status": "processing", "progress": 0, "message": "Upload successful"}
        save_job_status_to_file(job_id, initial_status)
        thread = threading.Thread(target=process_audio_background, args=(job_id, temp_audio_path, model_size))
        thread.start()
        return jsonify({"status": "processing_started", "job_id": job_id}), 202
    except Exception as e:
        error_message = f"Failed to start processing: {str(e)}"
        print(error_message)
        return jsonify({"status": "error", "message": error_message}), 500

def process_audio_background(job_id, audio_path, model_size):
    print(f"Starting background processing for job {job_id}")
    try:
        processing_result = process_audio(audio_path, model_size)
        results_data = {
            "job_id": job_id, "status": "completed",
            "protocol": processing_result.get("protocol"),
            "summary": None, "word_timestamps": processing_result.get("word_timestamps", False)
        }
        save_job_results_to_file(job_id, results_data)
        save_job_status_to_file(job_id, {"job_id": job_id, "status": "completed", "progress": 100, "message": "Processing completed"})
        print(f"Background processing completed for job {job_id}")
    except Exception as e:
        error_message = f"Processing failed: {str(e)}"
        print(f"Error during processing job {job_id}: {error_message}")
        save_job_status_to_file(job_id, {"job_id": job_id, "status": "failed", "message": error_message})
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

@app.route('/status/<job_id>', methods=['GET'])
def get_status(job_id):
    status = get_job_status_from_file(job_id)
    if status is None:
        return jsonify({"status": "error", "message": "Job ID not found"}), 404
    return jsonify(status)

@app.route('/results/<job_id>', methods=['GET'])
def get_results(job_id):
    status = get_job_status_from_file(job_id)
    if status is None:
        return jsonify({"status": "error", "message": "Job ID not found"}), 404
    if status.get("status") != "completed":
        return jsonify({"job_id": job_id, "status": status.get("status"), "message": "Job not completed"}), 409
    results = get_job_results_from_file(job_id)
    if results is None:
        return jsonify({"job_id": job_id, "status": "error", "message": "Results not available"}), 500
    return jsonify(results)

@app.route('/summarize/<job_id>', methods=['POST'])
def summarize_protocol(job_id):
    status = get_job_status_from_file(job_id)
    if status is None or status.get("status") != "completed":
        return jsonify({"status": "error", "message": "Job not completed or found"}), 404
    
    results = get_job_results_from_file(job_id)
    if results is None or 'protocol' not in results:
        return jsonify({"status": "error", "message": "Protocol data not available"}), 500

    if not request.is_json:
        return jsonify({"status": "error", "message": "Request must be JSON"}), 400

    req_data = request.get_json()
    model_identifier = req_data.get('model') # e.g., "gpt-4o", "bart-large-cnn", "ollama"
    ollama_url = req_data.get('ollama_url') # e.g., "http://<TAILSCALE_IP>:11434"
    
    if not model_identifier:
        return jsonify({"status": "error", "message": "Model identifier must be provided"}), 400
    
    try:
        summary_text = run_summarization(
            segments=results['protocol'],
            model_identifier=model_identifier,
            custom_url=ollama_url
        )
        
        results['summary'] = summary_text
        save_job_results_to_file(job_id, results)
        
        return jsonify({
            "job_id": job_id, "status": "summary_completed",
            "summary": summary_text
        }), 200
    except Exception as e:
        error_message = f"Summary generation failed: {str(e)}"
        print(f"Error during summarization for job {job_id}: {error_message}")
        return jsonify({"job_id": job_id, "status": "error", "message": error_message}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
