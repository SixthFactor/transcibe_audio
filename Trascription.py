import streamlit as st
import openai
import os
from pydub import AudioSegment
from tempfile import NamedTemporaryFile
import math

OPENAI_API_KEY = st.secrets["api_key"]
# Set up OpenAI API key
openai.api_key = OPENAI_API_KEY

def get_chunk_length_ms(file_path, target_size_mb=3):
    """
    Calculate the length of each chunk in milliseconds to create chunks of approximately target_size_mb.

    Args:
    file_path (str): Path to the audio file.
    target_size_mb (int): Target size of each chunk in megabytes. Default is 5 MB.

    Returns:
    int: Chunk length in milliseconds.
    """
    audio = AudioSegment.from_file(file_path)
    file_size_bytes = os.path.getsize(file_path)
    duration_ms = len(audio)

    # Calculate the approximate duration per byte
    duration_per_byte = duration_ms / file_size_bytes

    # Calculate the chunk length in milliseconds for the target size
    chunk_length_ms = target_size_mb * 1024 * 1024 * duration_per_byte
    return math.floor(chunk_length_ms)

def split_audio(audio_file_path, chunk_length_m=3):
    """
    Split an audio file into chunks of specified length.

    Args:
    audio_file_path (str): Path to the audio file.
    chunk_length_ms (int): Length of each chunk in milliseconds.

    Returns:
    list: List of AudioSegment chunks.
    """
    audio = AudioSegment.from_file(audio_file_path)
    chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
    return chunks


# def transcribe(audio_file):
#     try:
#         with open(audio_file, "rb") as audio:
#             response = openai.audio.transcriptions.create(
#                 model="whisper-1",
#                 file=audio,
#                 response_format="text"
#             )
#         return response
    
#     except openai.error.OpenAIError as e:
#         st.error(f"OpenAI API Error: {e}")
#         return None

def transcribe(audio_file):
    with open(audio_file, "rb") as audio:
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
            response_format="text"
        )
    return response

def process_audio_chunks(audio_chunks):
    transcriptions = []
    min_length_ms = 100  # Minimum length required by OpenAI API (0.1 seconds)
    
    for i, chunk in enumerate(audio_chunks):
        if len(chunk) < min_length_ms:
            st.warning(f"Chunk {i} is too short to be processed.")
            continue
        
        with NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
            chunk.export(temp_audio_file.name, format="wav")
            temp_audio_file_path = temp_audio_file.name

        transcription = transcribe(temp_audio_file_path)
        if transcription:
            transcriptions.append(transcription)
            st.write(f"Transcription for chunk {i}: {transcription}")

        os.remove(temp_audio_file_path)
    return " ".join(transcriptions)

st.title("Audio Transcription with OpenAI's Whisper")

uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "ogg", "m4a"])

if 'transcription' not in st.session_state:
    st.session_state.transcription = None

if uploaded_file is not None and st.session_state.transcription is None:
    st.audio(uploaded_file)
    
    # Save uploaded file temporarily
    file_extension = uploaded_file.name.split(".")[-1]
    original_file_name = uploaded_file.name.rsplit('.', 1)[0]  # Get the original file name without extension
    temp_audio_file = f"temp_audio_file.{file_extension}"
    with open(temp_audio_file, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Split and process audio
    with st.spinner('Transcribing...'):
        chunk_length_ms = get_chunk_length_ms(temp_audio_file, target_size_mb)
        audio_chunks = split_audio(temp_audio_file, chunk_length_ms)
        transcription = process_audio_chunks(audio_chunks)
        if transcription:
            st.session_state.transcription = transcription
            st.success('Transcription complete!')
            # st.text_area("Transcription", transcription, key="transcription_area")

            # Save transcription to a text file
            output_file_path = f'{original_file_name}_transcription.txt'
            with open(output_file_path, 'w', encoding='utf-8') as f:
                f.write(transcription)
            st.session_state.output_file_path = output_file_path
            
    # Clean up temporary file
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)

if st.session_state.transcription:
    st.text_area("Transcription", st.session_state.transcription, key="transcription_area_final")
    st.download_button(label="Download Transcription", data=st.session_state.transcription, file_name=st.session_state.output_file_path, mime='text/plain')
