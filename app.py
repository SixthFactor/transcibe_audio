import streamlit as st
import openai
import os

OPENAI_API_KEY = st.secrets["api_key"]

# Set your OpenAI API key
openai.api_key = OPENAI_API_KEY

def transcribe(audio_file, language):
    transcription = openai.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        response_format="text",
        language=language
    )
    return transcription

st.title("Audio Transcription with OpenAI's Whisper")

uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "m4a"])

language = st.selectbox(
    "Select the language of the audio file",
    ("en", "hi")
)

if uploaded_file is not None:
    st.audio(uploaded_file)
    with st.spinner('Transcribing...'):
        transcription = transcribe(uploaded_file, language)
    st.success('Transcription complete!')
    st.text_area("Transcription", transcription)
