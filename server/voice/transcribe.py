import whisper
import os
import tempfile
import logging
import asyncio
from static_ffmpeg import add_paths

logger = logging.getLogger("AutoOS.voice")

# Global variables
_model = None
_ffmpeg_ready = False

def ensure_ffmpeg():
    """
    Ensures FFmpeg is available. This can be blocking on the first run.
    """
    global _ffmpeg_ready
    if not _ffmpeg_ready:
        try:
            logger.info("Initializing static-ffmpeg...")
            add_paths()
            _ffmpeg_ready = True
            logger.info("static-ffmpeg is ready.")
        except Exception as e:
            logger.error(f"Failed to add static-ffmpeg: {e}")

def get_model():
    global _model
    if _model is None:
        logger.info("Loading Whisper 'base' model...")
        _model = whisper.load_model("base")
    return _model

async def transcribe_audio(audio_bytes: bytes) -> str:
    """
    Transcribes raw audio bytes using the local Whisper model.
    """
    # Ensure dependencies are ready
    await asyncio.to_thread(ensure_ffmpeg)
    model = await asyncio.to_thread(get_model)
    
    # Save bytes to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(audio_bytes)
        temp_path = temp_audio.name
        
    try:
        logger.info(f"Transcribing audio from {temp_path}...")
        # Use asyncio.to_thread to run the CPU-intensive transcription without blocking
        # Explicitly set fp16=False for CPU compatibility
        result = await asyncio.to_thread(model.transcribe, temp_path, fp16=False)
        text = result.get("text", "").strip()
        return text
    except Exception as e:
        logger.error(f"Whisper transcription failed: {e}")
        return f"Error: {str(e)}"
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
