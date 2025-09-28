import os
import secrets
from flask import Flask, render_template, request, redirect, url_for, session
from gtts import gTTS
import speech_recognition as sr
from datetime import datetime
from werkzeug.utils import secure_filename
from pydub import AudioSegment  # NEW - for format conversion

# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # secure random session key

# Directory to store audio files
BASE_AUDIO_DIR = "static/audio"

if not os.path.exists(BASE_AUDIO_DIR):
    os.makedirs(BASE_AUDIO_DIR)

# --- Helper Functions ---

def get_user_dir():
    """Create/get a folder for the current user session"""
    if 'id' not in session:
        session['id'] = secrets.token_hex(8)
    user_dir = os.path.join(BASE_AUDIO_DIR, session['id'])
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    return user_dir

def save_text_to_audio(text):
    """Convert text to audio using gTTS"""
    filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
    user_dir = get_user_dir()
    filepath = os.path.join(user_dir, filename)
    tts = gTTS(text=text, lang='en')
    tts.save(filepath)
    return filename

def convert_voice_to_text(audio_file):
    """Convert uploaded audio (any format) to text"""
    r = sr.Recognizer()

    # Convert to WAV before processing
    wav_path = audio_file.rsplit(".", 1)[0] + "_converted.wav"
    try:
        sound = AudioSegment.from_file(audio_file)
        sound.export(wav_path, format="wav")
    except Exception as e:
        print(f"[ERROR] Failed to convert file: {e}")
        return None

    # Speech Recognition
    try:
        with sr.AudioFile(wav_path) as source:
            audio = r.record(source)
            text = r.recognize_google(audio)
    except sr.UnknownValueError:
        text = None
    except sr.RequestError as e:
        print(f"[ERROR] Google Speech API request failed: {e}")
        text = None

    # Clean up converted file
    if os.path.exists(wav_path):
        os.remove(wav_path)

    return text

# --- Routes ---

@app.route("/", methods=["GET", "POST"])
def index():
    audio_file = None
    history = []

    user_dir = get_user_dir()

    # Load history
    if os.path.exists(user_dir):
        for f in sorted(os.listdir(user_dir), reverse=True):
            history.append({"filename": f, "timestamp": f[:14]})

    if request.method == "POST":
        # Text-to-Audio
        if "text_input" in request.form:
            text = request.form["text_input"].strip()
            if text:
                filename = save_text_to_audio(text)
                audio_file = filename

        # Voice-to-Audio
        elif "voice_input" in request.files:
            file = request.files["voice_input"]
            if file and file.filename:
                safe_filename = secure_filename(file.filename)
                temp_path = os.path.join(user_dir, safe_filename)
                file.save(temp_path)
                text = convert_voice_to_text(temp_path)
                if text:
                    filename = save_text_to_audio(text)
                    audio_file = filename
                os.remove(temp_path)

        return redirect(url_for("index"))

    return render_template("index.html", audio_file=audio_file, history=history)

@app.route("/delete/<audio_filename>", methods=["POST"])
def delete_audio(audio_filename):
    user_dir = get_user_dir()
    file_path = os.path.join(user_dir, audio_filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    return redirect(url_for("index"))

# --- Run App ---
if __name__ == "__main__":
    app.run(debug=True)
