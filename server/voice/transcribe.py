import os
import tempfile
import logging
from faster_whisper import WhisperModel

logger = logging.getLogger("AutoOS.voice")

# Initialize the model at module level so it loads only once at startup
# We use the 'base' model by default. It's fast and accurate enough for short commands.
MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")

logger.info(f"Loading faster-whisper model: {MODEL_SIZE}...")
# Use INT8 for CPU inference to save memory and speed up
try:
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    logger.info("faster-whisper model loaded successfully.")
except Exception as e:
    logger.error(f"Error loading faster-whisper model: {e}")
    model = None


def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribes audio bytes to text using faster-whisper.
    Saves bytes to a temp file, transcribes, and cleans up.
    """
    if not model:
        raise RuntimeError("Whisper model is not loaded.")

    # Create a temporary file to store the audio bytes
    # faster-whisper expects a file path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_bytes)
        temp_audio_path = temp_audio.name

    try:
        # Generate transcription
        # Using beam_size=1 (greedy search) for speed, since these are short commands
        segments, info = model.transcribe(temp_audio_path, beam_size=1)
        
        # Combine segments
        transcribed_text = " ".join([segment.text for segment in segments]).strip()
        
        logger.info(f"Transcription complete (Language: {info.language}, Probability: {info.language_probability:.2f})")
        return transcribed_text

    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise e
    
    finally:
        # Clean up temp file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)
