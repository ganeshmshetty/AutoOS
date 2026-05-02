from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from voice.transcribe import transcribe_audio
import logging

logger = logging.getLogger("AutoOS.api.voice")
router = APIRouter(prefix="/voice", tags=["voice"])

class TranscriptionResponse(BaseModel):
    text: str

@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_endpoint(audio: UploadFile = File(...)):
    """
    Receives an audio file (e.g., .wav from the frontend),
    processes it through the local faster-whisper model,
    and returns the transcribed text.
    """
    if not audio:
        raise HTTPException(status_code=400, detail="No audio file provided.")
    
    try:
        # Read the file bytes
        audio_bytes = await audio.read()
        logger.info(f"Received audio file for transcription: {audio.filename} ({len(audio_bytes)} bytes)")
        
        # Pass to faster-whisper
        text = transcribe_audio(audio_bytes)
        
        if not text:
            logger.warning("Transcription resulted in empty text.")
            return TranscriptionResponse(text="")
            
        logger.info(f"Successfully transcribed text: {text}")
        return TranscriptionResponse(text=text)

    except Exception as e:
        logger.error(f"Error in transcription endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process audio.")
