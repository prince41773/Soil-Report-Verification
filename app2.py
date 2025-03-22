import streamlit as st
import PyPDF2
import requests
import os
import json
from gtts import gTTS
from deep_translator import GoogleTranslator

# Constants
GEMINI_API_KEY = "AIzaSyCWlm2xFLWYLlpgvZzfJt4ZexmNDDETXBQ"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

# UI Configuration
st.set_page_config(page_title="Soil Report Verification", layout="wide")
st.title("🌱 Organic Farming Soil Verification")
st.write("Upload your soil report and get AI-powered verification results.")

# File Upload
uploaded_file = st.file_uploader("Upload your soil report (PDF)", type=["pdf"])

# Language Selection
languages = {"English": "en", "Hindi": "hi", "Gujarati": "gu"}
selected_language = st.selectbox("Choose Language", list(languages.keys()))

# Function to Extract Text from PDF
def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return text

# Function to Analyze Soil Report with Gemini API
def analyze_soil_report(text):
    payload = {"contents": [{"parts": [{"text": text}]}]}
    response = requests.post(API_URL, headers={"Content-Type": "application/json"}, json=payload)
    if response.status_code == 200:
        response_json = response.json()
        
        candidates = response_json.get("candidates", [{}])
        if candidates and "content" in candidates[0]:
            response_text = candidates[0]["content"]["parts"][0].get("text", "No valid response from AI.")
            return response_text
    return "AI could not analyze the report. Please try again."

# Function to Translate Text with Validation
def translate_text(text, target_lang):
    if not isinstance(text, str) or not text.strip():
        return "Translation not available: No valid input."
    if len(text) > 5000:
        text = text[:5000]  # Truncate text to max limit
    return GoogleTranslator(source="auto", target=target_lang).translate(text)

# Function for Text-to-Speech
def text_to_speech(text, lang_code):
    tts = gTTS(text, lang=lang_code)
    tts.save("output.mp3")
    return "output.mp3"

# Process Uploaded File
if uploaded_file:
    st.subheader("📄 Extracted Soil Report Data")
    pdf_text = extract_text_from_pdf(uploaded_file)
    st.text_area("Extracted Text", pdf_text, height=200)
    
    if st.button("Analyze Soil Report 🧪"):
        with st.spinner("Analyzing soil report..."):
            ai_response = analyze_soil_report(pdf_text)
            if "AI could not analyze the report" in ai_response:
                st.error(ai_response)
            else:
                short_advice = ""  # Extract simplified advice
                if "not suitable" in ai_response.lower():
                    short_advice = "❌ Your soil is currently not suitable for organic farming. Improve it by adding compost, reducing chemical fertilizers, and maintaining soil moisture."
                elif "suitable" in ai_response.lower():
                    short_advice = "✅ Your soil is suitable for organic farming! Your report has been submitted for verification. If approved, you will receive your organic farming certificate soon."
                else:
                    short_advice = " Your soil is currently not suitable for organic farming. Improve it by adding compost, reducing chemical fertilizers, and maintaining soil moisture. AI has analyzed your report. Follow expert recommendations to improve soil quality.  If you have Low Nitrogen then add compost or grow legume crops (like beans and peas).  If you have High pH then add organic compost or sulfur to balance pH levels.  If you have Low Potassium then use banana peels or wood ash as natural fertilizers.  If you have Low Phosphorus then apply bone meal or rock phosphate."
                
                translated_response = translate_text(short_advice, languages[selected_language])
                audio_file = text_to_speech(translated_response, languages[selected_language])
                
                st.subheader("🌍 AI Analysis Result")
                st.write(translated_response)
                st.audio(audio_file, format="audio/mp3")

# Footer
st.markdown("---")
st.markdown("Developed for Natural Farming Verification 🌿")
