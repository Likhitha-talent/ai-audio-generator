from flask import Flask, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from gtts import gTTS
import os, uuid, shutil
from werkzeug.utils import secure_filename
import speech_recognition as sr
from pydub import AudioSegment
from datetime import datetime, timedelta
from flask import redirect

app = Flask(__name__)
app.secret_key = 'your_super_secret_key'

# SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///audio.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Create static audio folder
os.makedirs("static/audio", exist_ok=True)

# ------------------- Database Model -------------------
class AudioFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64))
    filename = db.Column(db.String(128))
    text = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()


# ------------------- Helpers -------------------
def generate_unique_filename(extension="mp3"):
    return f"{uuid.uuid4().hex}.{extension}"

def get_user_folder():
    if "id" not in session:
        session["id"] = uuid.uuid4().hex
    user_folder = os.path.join("static/audio", session["id"])
    os.makedirs(user_folder, exist_ok=True)
    return user_folder

def cleanup_old_files(days=1):
    """Remove old folders and delete DB entries older than `days`"""
    now = datetime.utcnow()
    root = "static/audio"
    cutoff = now - timedelta(days=days)
    
    for folder in os.listdir(root):
        folder_path = os.path.join(root, folder)
        if os.path.isdir(folder_path):
            folder_time = datetime.utcfromtimestamp(os.path.getmtime(folder_path))
            if folder_time < cutoff:
                shutil.rmtree(folder_path)
    
    # Delete old records from DB
    AudioFile.query.filter(AudioFile.timestamp < cutoff).delete()
    db.session.commit()

# ------------------- Audio Generation -------------------
def generate_female_audio(text):
    user_folder = get_user_folder()
    filename = generate_unique_filename()
    filepath = os.path.join(user_folder, filename)
    tts = gTTS(text=text, lang="en", tld="com")
    tts.save(filepath)
    
    # Save metadata
    audio_record = AudioFile(user_id=session["id"], filename=filename, text=text)
    db.session.add(audio_record)
    db.session.commit()
    
    return filename

def convert_voice_to_female_ai(input_file):
    user_folder = get_user_folder()
    
    # Convert to WAV if needed
    if not input_file.endswith(".wav"):
        sound = AudioSegment.from_file(input_file)
        input_file = os.path.join(user_folder, "temp.wav")
        sound.export(input_file, format="wav")
    
    r = sr.Recognizer()
    with sr.AudioFile(input_file) as source:
        audio = r.record(source)
        try:
            text = r.recognize_google(audio)
        except sr.UnknownValueError:
            text = "Sorry, could not understand the audio."
        except sr.RequestError:
            text = "Sorry, speech service failed."
    
    filename = generate_unique_filename()
    filepath = os.path.join(user_folder, filename)
    tts = gTTS(text=text, lang="en", tld="com")
    tts.save(filepath)
    
    # Save metadata
    audio_record = AudioFile(user_id=session["id"], filename=filename, text=text)
    db.session.add(audio_record)
    db.session.commit()
    
    return filename

def get_user_audio_history():
    return AudioFile.query.filter_by(user_id=session["id"]).order_by(AudioFile.timestamp.desc()).all()

# ------------------- Routes -------------------
@app.route("/", methods=["GET", "POST"])
def index():
    cleanup_old_files(days=1)  # optional
    
    audio_file = None
    if request.method == "POST":
        if "text_input" in request.form and request.form["text_input"]:
            text = request.form["text_input"]
            audio_file = generate_female_audio(text)
        elif "voice_input" in request.files:
            file = request.files["voice_input"]
            if file.filename != "":
                filename = secure_filename(file.filename)
                user_folder = get_user_folder()
                filepath = os.path.join(user_folder, filename)
                file.save(filepath)
                audio_file = convert_voice_to_female_ai(filepath)
    
    history = get_user_audio_history()
    return render_template("index.html", audio_file=audio_file, history=history)


@app.route("/delete/<int:audio_id>", methods=["POST"])
def delete_audio(audio_id):
    record = AudioFile.query.get_or_404(audio_id)
    # Ensure user can only delete their own files
    if record.user_id != session.get("id"):
        return "Unauthorized", 403

    # Delete file from disk
    file_path = os.path.join("static/audio", record.user_id, record.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    # Delete record from DB
    db.session.delete(record)
    db.session.commit()
    return redirect("/")  # Go back to homepage


if __name__ == "__main__":
    app.run(debug=True)
