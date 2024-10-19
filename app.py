import streamlit as st
import openai
import os
from pydub import AudioSegment
from tempfile import NamedTemporaryFile
import math
from docx import Document

OPENAI_API_KEY = st.secrets["api_key"]

# Set your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_chunk_length_ms(file_path, target_size_mb):
    """
    Calculate the length of each chunk in milliseconds to create chunks of approximately target_size_mb.

    Args:
    file_path (str): Path to the audio file.
    target_size_mb (int): Target size of each chunk in megabytes.

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

def split_audio(audio_file_path, chunk_length_ms):
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

def transcribe(audio_file):
    """
    Transcribe an audio file using OpenAI Whisper model.

    Args:
    audio_file (str): Path to the audio file.

    Returns:
    str: Transcribed text.
    """
    with open(audio_file, "rb") as audio:
        response = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio,
            response_format="text"
        )
    return response

def process_audio_chunks(audio_chunks):
    """
    Process and transcribe each audio chunk.

    Args:
    audio_chunks (list): List of AudioSegment chunks.

    Returns:
    str: Combined transcription from all chunks.
    """
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

def save_transcription_to_docx(transcription, audio_file_path):
    """
    Save the transcription as a .docx file.

    Args:
    transcription (str): Transcribed text.
    audio_file_path (str): Path to the original audio file for naming purposes.

    Returns:
    str: Path to the saved .docx file.
    """
    # Extract the base name of the audio file (without extension)
    base_name = os.path.splitext(os.path.basename(audio_file_path))[0]
    
    # Create a new file name by appending "_full_transcription" with .docx extension
    output_file_name = f"{base_name}_full_transcription.docx"
    
    # Create a new Document object
    doc = Document()
    
    # Add the transcription text to the document
    doc.add_paragraph(transcription)
    
    # Save the document in .docx format
    doc.save(output_file_name)
    
    return output_file_name

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
        chunk_length_ms = get_chunk_length_ms(temp_audio_file, target_size_mb=2)
        audio_chunks = split_audio(temp_audio_file, chunk_length_ms)
        transcription = process_audio_chunks(audio_chunks)
        if transcription:
            st.session_state.transcription = transcription
            st.success('Transcription complete!')

            # Save transcription to a Word (.docx) file
            output_docx_file = save_transcription_to_docx(transcription, uploaded_file.name)
            st.session_state.output_docx_file = output_docx_file
            
    # Clean up temporary file
    if os.path.exists(temp_audio_file):
        os.remove(temp_audio_file)

if st.session_state.transcription:
    st.text_area("Transcription", st.session_state.transcription, key="transcription_area_final")
    
    # Download the transcription as a .docx file
    with open(st.session_state.output_docx_file, "rb") as docx_file:
        st.download_button(
            label="Download Transcription (.docx)",
            data=docx_file,
            file_name=st.session_state.output_docx_file,
            mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )

