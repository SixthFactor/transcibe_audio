import streamlit as st
import openai
import os
from pydub import AudioSegment
import speech_recognition as sr
from langdetect import detect

OPENAI_API_KEY = st.secrets["api_key"]
# Set up OpenAI API key
openai.api_key = OPENAI_API_KEY

# Function to transcribe audio using OpenAI's Whisper model
def transcribe(audio_file_path):
    with open(audio_file_path, "rb") as audio_file:
        transcription = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
    return transcription
    # return transcription["text"]

# Function to translate text using GPT-3.5
def translate_text(text, target_language):
    messages = [
        {"role": "system", "content": f"You are a translator. Translate the following text to {target_language}."},
        {"role": "user", "content": text},
    ]
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=1024,
        temperature=0.3
    )
    # st.write(response.choices[0].message["content"])
    # return response.choices[0].message[]
    return response.choices[0].message.content

# Streamlit app layout
st.title("Audio Transcription and Translation")

# File uploader
uploaded_file = st.file_uploader("Choose an audio file...", type=["wav", "mp3", "ogg"])

# Target language input
target_language = st.text_input("Enter target language for translation:", "Hindi")

# Initialize session state for transcription
if "transcription" not in st.session_state:
    st.session_state.transcription = None
    st.session_state.detected_language = None

if uploaded_file is not None and st.session_state.transcription is None:
    # Save uploaded file temporarily with its correct extension
    file_extension = uploaded_file.name.split(".")[-1]
    temp_audio_file = f"temp_audio_file.{file_extension}"
    with open(temp_audio_file, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Convert audio to text
    with st.spinner('Transcribing audio...'):
        transcription = transcribe(temp_audio_file)
        st.session_state.transcription = transcription
        detected_language = detect(transcription)
        st.session_state.detected_language = detected_language
        st.write("Original Text:", transcription)
        st.write("Detected Language:", detected_language)

    # Clean up temporary file
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)

# Display the stored transcription
if st.session_state.transcription is not None:
    st.write("Original Text:", st.session_state.transcription)
    st.write("Detected Language:", st.session_state.detected_language)

# Button to trigger translation
if st.session_state.transcription is not None and st.session_state.detected_language != target_language:
    if st.button('Translate Text'):
        with st.spinner('Translating text...'):
            translated_text = translate_text(st.session_state.transcription, target_language)
            st.write("Translated Text:", translated_text)
