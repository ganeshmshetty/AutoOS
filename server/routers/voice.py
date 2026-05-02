from fastapi import APIRouter, UploadFile, File, HTTPException
import logging
from server.voice.transcribe import transcribe_audio

router = APIRouter(prefix="/voice", tags=["voice"])
logger = logging.getLogger("AutoOS.voice_router")

@router.post("/transcribe")
async def transcribe(file: UploadFile = File(...)):
    """
    Endpoint to receive an audio file and return transcribed text.
    """
    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Empty audio file")
            
        text = await transcribe_audio(content)
        logger.info(f"Transcribed text: {text}")
        
        return {"text": text}
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail="Transcription failed")
