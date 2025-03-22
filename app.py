from flask import Flask, render_template_string, request, jsonify, send_file
from fastapi import FastAPI, UploadFile, File
import uvicorn
import threading
import PyPDF2
import requests
import os
from io import BytesIO
from gtts import gTTS
from deep_translator import GoogleTranslator
from flask_cors import CORS

# Constants
GEMINI_API_KEY = "AIzaSyCWlm2xFLWYLlpgvZzfJt4ZexmNDDETXBQ"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# Flask & FastAPI Setup
flask_app = Flask(__name__)
CORS(flask_app)
fastapi_app = FastAPI()

# Language Mapping
languages = {"English": "en", "Hindi": "hi", "Gujarati": "gu"}

# HTML Template (No External Files)
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Soil Report Verification</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background-color: #f4f4f4; }
        .container { max-width: 600px; margin: 50px auto; padding: 20px; background: white; border-radius: 8px; box-shadow: 0px 0px 10px gray; }
        button { padding: 10px; background-color: green; color: white; border: none; cursor: pointer; }
        button:hover { background-color: darkgreen; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌱 Organic Farming Soil Verification</h1>
        <p>Upload your soil report and get AI-powered verification results.</p>

        <label for="language">Choose Language:</label>
        <select id="language">
            <option value="English">English</option>
            <option value="Hindi">Hindi</option>
            <option value="Gujarati">Gujarati</option>
        </select>

        <input type="file" id="fileInput">
        <button onclick="analyzeSoil()">Analyze Soil Report 🧪</button>

        <div id="result"></div>
        <audio id="audioPlayer" controls style="display:none;"></audio>
    </div>

    <script>
        function analyzeSoil() {
            let fileInput = document.getElementById("fileInput").files[0];
            let language = document.getElementById("language").value;

            if (!fileInput) {
                alert("Please upload a soil report PDF.");
                return;
            }

            let formData = new FormData();
            formData.append("file", fileInput);
            formData.append("lang", language);

            fetch("/analyze", {
                method: "POST",
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById("result").innerHTML = `<p>${data.text}</p>`;
                let audioPlayer = document.getElementById("audioPlayer");
                audioPlayer.src = "/get_audio";
                audioPlayer.style.display = "block";
            })
            .catch(error => console.error("Error:", error));
        }
    </script>
</body>
</html>
"""

# Function to Extract Text from PDF
def extract_text_from_pdf(file_bytes):
    reader = PyPDF2.PdfReader(file_bytes)
    text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return text

# Function to Analyze Soil Report with Gemini AI
def analyze_soil_report(text):
    payload = {"contents": [{"parts": [{"text": text}]}]}
    response = requests.post(API_URL, headers={"Content-Type": "application/json"}, json=payload)
    
    if response.status_code == 200:
        response_json = response.json()
        candidates = response_json.get("candidates", [{}])
        if candidates and "content" in candidates[0]:
            return candidates[0]["content"]["parts"][0].get("text", "No valid response from AI.")
    
    return "AI could not analyze the report. Please try again."

# Function to Generate Short Advice from AI Response
def generate_advice(ai_response):
    if "not suitable" in ai_response.lower():
        return "❌ Your soil is not suitable for organic farming. Add compost, avoid chemical fertilizers, and improve drainage."
    elif "suitable" in ai_response.lower():
        return "✅ Your soil is suitable for organic farming! Your report has been submitted for verification."
    else:
        return ("Your soil needs improvements. "
                "If Low Nitrogen: Add compost or grow legumes. "
                "If High pH: Add compost or sulfur. "
                "If Low Potassium: Use banana peels or wood ash. "
                "If Low Phosphorus: Apply bone meal or rock phosphate.")

# Function to Translate Text
def translate_text(text, target_lang):
    if not text.strip():
        return "Translation not available."
    return GoogleTranslator(source="auto", target=target_lang).translate(text)

# Function for Text-to-Speech
def text_to_speech(text, lang_code):
    tts = gTTS(text, lang=lang_code)
    audio_path = "output.mp3"
    tts.save(audio_path)
    return audio_path

# Flask Route for UI
@flask_app.route("/")
def home():
    return render_template_string(html_template)

# Flask Route for File Upload & AI Analysis
@flask_app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files["file"]
    language = request.form["lang"]
    lang_code = languages.get(language, "en")

    file_bytes = BytesIO(file.read())
    extracted_text = extract_text_from_pdf(file_bytes)
    
    if not extracted_text:
        return jsonify({"error": "Could not extract text from PDF."})

    ai_response = analyze_soil_report(extracted_text)
    short_advice = generate_advice(ai_response)
    translated_response = translate_text(short_advice, lang_code)

    # Generate Audio
    text_to_speech(translated_response, lang_code)
    
    return jsonify({"text": translated_response})

# Flask Route to Serve Audio
@flask_app.route("/get_audio")
def get_audio():
    return send_file("output.mp3", mimetype="audio/mpeg")

# FastAPI Endpoint for MERN Stack
@fastapi_app.post("/process_pdf/")
async def process_pdf(file: UploadFile, lang: str = "English"):
    lang_code = languages.get(lang, "en")
    file_bytes = BytesIO(await file.read())

    extracted_text = extract_text_from_pdf(file_bytes)
    ai_response = analyze_soil_report(extracted_text)
    short_advice = generate_advice(ai_response)
    translated_response = translate_text(short_advice, lang_code)

    text_to_speech(translated_response, lang_code)

    return {"text": translated_response, "audio": "/get_audio"}

# Run FastAPI in a Separate Thread
def run_fastapi():
    uvicorn.run(fastapi_app, host="0.0.0.0", port=8001)

if __name__ == "__main__":
    threading.Thread(target=run_fastapi, daemon=True).start()
    flask_app.run(host="0.0.0.0", port=5000, debug=True)
