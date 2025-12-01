from google import genai
from gtts import gTTS
import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
import io, base64, re

# get data from the uploaded file 
def extract_text_from_file(uploaded_file):
    if uploaded_file is None:
        return None

    file_type = uploaded_file.type

    if "text" in file_type:
        return uploaded_file.read().decode("utf-8")

    elif "pdf" in file_type:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    elif "csv" in file_type:
        df = pd.read_csv(uploaded_file)
        return df.to_string()

    elif "excel" in file_type or uploaded_file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(uploaded_file)
        return df.to_string()

    else:
        return None


# translatable launguages
LANG_OPTIONS = {
    "Afrikaans": "af",
    "Arabic": "ar",
    "Bengali": "bn",
    "Chinese (Simplified)": "zh-CN",
    "Chinese (Traditional)": "zh-TW",
    "Czech": "cs",
    "Danish": "da",
    "Dutch": "nl",
    "English": "en",
    "Finnish": "fi",
    "French": "fr",
    "German": "de",
    "Greek": "el",
    "Gujarati": "gu",
    "Hindi": "hi",
    "Hungarian": "hu",
    "Indonesian": "id",
    "Italian": "it",
    "Japanese": "ja",
    "Javanese": "jw",
    "Kannada": "kn",
    "Korean": "ko",
    "Malayalam": "ml",
    "Marathi": "mr",
    "Nepali": "ne",
    "Norwegian": "no",
    "Polish": "pl",
    "Portuguese": "pt",
    "Romanian": "ro",
    "Russian": "ru",
    "Serbian": "sr",
    "Sinhala": "si",
    "Slovak": "sk",
    "Spanish": "es",
    "Sundanese": "su",
    "Swahili": "sw",
    "Swedish": "sv",
    "Tamil": "ta",
    "Telugu": "te",
    "Thai": "th",
    "Turkish": "tr",
    "Ukrainian": "uk",
    "Urdu": "ur",
    "Vietnamese": "vi",
    "Welsh": "cy"
}

# webapp ui
st.set_page_config(page_title="Auto Translate + TTS", layout="centered")

st.markdown(
    "<h1 style='text-align: center; color: #4A90E2;'>🌍 Auto Translate + Text-to-Speech (MP3)</h1>",
    unsafe_allow_html=True
)

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    text_input = st.text_area("📝 Enter text:", placeholder="Type or paste any language text here...", height=150)
    uploaded_file = st.file_uploader("📂 Or upload a file", type=["txt", "pdf", "xlsx", "csv"], accept_multiple_files=False)
    output_language = st.selectbox("🌐 Convert and speak in:", list(LANG_OPTIONS.keys()))
    output_lang_code = LANG_OPTIONS[output_language]
    st.write("")

    if text_input and uploaded_file:
        st.warning("⚠️ Please either type text OR upload a file — not both.")
        st.stop()
    elif not text_input and not uploaded_file:
        st.info("ℹ️ Please enter text or upload a file to continue.")
        st.stop()

    text = extract_text_from_file(uploaded_file) if uploaded_file else text_input

    if st.button("🎧 Generate Audio"):
        with st.spinner("🧠 Detecting language and generating translation..."):
            try:
                client = genai.Client(api_key="AIzaSyBeeGZUXrbQUzaZ6jr1W11I103ntRkx9ak")

                # Step 1: Detect language
                detect_prompt = f"Identify only the language name of this text: {text[:200]}"
                detect_response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=detect_prompt,
                    config={"response_modalities": ["text"]}
                )
                detected_language = detect_response.text.strip()

                # Step 2: Translate text
                translate_prompt = (
                    f"Translate this text from {detected_language} to {output_language}. "
                    f"Respond ONLY with the translated text, no explanation or prefix.\n\n{text}"
                )
                translate_response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=translate_prompt,
                    config={"response_modalities": ["text"]}
                )
                translated_text = translate_response.text.strip()
                translated_text = re.sub(r'(?i)(^translated text:|^translation:)', '', translated_text).strip()

                # Step 3: Generate MP3
                mp3_buffer = io.BytesIO()
                tts = gTTS(translated_text, lang=output_lang_code)
                tts.write_to_fp(mp3_buffer)
                mp3_buffer.seek(0)

                # Step 4: Play audio
                audio_bytes = mp3_buffer.getvalue()
                b64 = base64.b64encode(audio_bytes).decode()
                audio_html = f"""
                <audio controls controlsList="nodownload noplaybackrate">
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                    Your browser does not support the audio element.
                </audio>
                """
                st.success(f"✅ Detected {detected_language}. Translated and spoken in {output_language}.")
                st.markdown(audio_html, unsafe_allow_html=True)

                # Step 5: Download audio using button
                mp3_buffer.seek(0) 
                st.download_button(
                    label="💾 Download MP3",
                    data=mp3_buffer,
                    file_name=f"translated_{output_language}.mp3",
                    mime="audio/mp3"
                )

                st.markdown("#### 📝 Translated Text:")
                st.write(translated_text)

            except Exception as e:
                st.error(f"❌ Error: {e}")
