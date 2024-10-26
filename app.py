from flask import Flask, request, jsonify, url_for, render_template, send_file
from gtts import gTTS
from PyPDF2 import PdfReader
import os
import time

app = Flask(__name__)

# Ensure the 'temp' directory exists
temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'temp')
os.makedirs(temp_dir, exist_ok=True)

# Global variable to track progress
conversion_progress = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_pdf():
    global conversion_progress
    conversion_progress = {}  # Reset progress for new upload

    try:
        if 'pdf' not in request.files:
            return jsonify({"success": False, "message": "No file part"}), 400

        pdf_file = request.files['pdf']
        if pdf_file.filename == '':
            return jsonify({"success": False, "message": "No selected file"}), 400

        if pdf_file and pdf_file.filename.endswith('.pdf'):
            temp_pdf_path = os.path.join(temp_dir, pdf_file.filename)
            pdf_file.save(temp_pdf_path)

            pdf_text = extract_text_from_pdf(temp_pdf_path)
            if not pdf_text.strip():
                return jsonify({"success": False, "message": "PDF extraction failed"}), 500

            audio_path = convert_text_to_speech(pdf_text, pdf_file.filename)
            os.remove(temp_pdf_path)

            # Extract only the filename for the audio file
            audio_filename = f"{pdf_file.filename}.mp3"
            audio_url = url_for('download_file', filename=audio_filename)
            return jsonify({"success": True, "audio_url": audio_url})

        return jsonify({"success": False, "message": "Invalid file type"}), 400

    except Exception as e:
        return jsonify({"success": False, "message": "Internal server error"}), 500

@app.route('/progress')
def progress():
    global conversion_progress
    return jsonify({"progress": conversion_progress.get("progress", 0)})

def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def convert_text_to_speech(text, filename):
    global conversion_progress
    tts = gTTS(text=text, lang='en')
    
    # Simulate progress (you can implement actual progress tracking based on your needs)
    for i in range(0, 101, 20):
        time.sleep(0.5)  # Simulating time taken for conversion
        conversion_progress["progress"] = i

    audio_path = os.path.join(temp_dir, f"{filename}.mp3")
    tts.save(audio_path)
    conversion_progress["progress"] = 100  # Mark complete
    return audio_path

@app.route('/download/<filename>')
def download_file(filename):
    audio_path = os.path.join(temp_dir, filename)
    if os.path.exists(audio_path):
        return send_file(audio_path, as_attachment=True)
    else:
        return jsonify({"success": False, "message": "File not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)
