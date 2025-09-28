AI Audio Generator

Live Demo:[AI Audio Generator on Render](https://ai-audio-generator-1.onrender.com)

Project Description
AI Audio Generator is a web application that allows users to:  
- Convert text to AI-generated speech
- Transform voice files into AI-generated voice
- Download and manage generated audio files  
- Keep a session-based audio history  

It is mobile-friendly and easy to use, making audio generation accessible from anywhere.

Features
- Text-to-Speech: Convert any text input into female AI voice.  
- Voice-to-AI Voice: Upload an audio file and get AI-modified speech.  
- Audio History: View, download, or delete previously generated audio files.  
- Responsive Design: Works well on desktop and mobile devices.  
- Session-Based Storage: Each session stores audio separately.  

Technologies Used
- Backend:Python, Flask  
- Frontend:HTML, CSS, JavaScript  
-Libraries:gTTS, SpeechRecognition, Pydub, Werkzeug  
- Deployment:Render  

Installation & Setup (Local Development)
1. Clone the repository:
   git clone https://github.com/yourusername/ai-audio-generator.git
   cd ai-audio-generator
2.Create a virtual environment:
  python3 -m venv venv
  source venv/bin/activate  # On Windows: venv\Scripts\activate
3.Install dependencies:
  pip install -r requirements.txt
4.Run the application:
 python app.py


