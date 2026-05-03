"""
voice/transcribe.py — Speech-to-text via Google Gemini Flash.

Uses the new google-genai SDK (v1.65+) for multimodal audio transcription.
Falls back to local faster-whisper if Gemini is unavailable.
"""
import os
import logging

logger = logging.getLogger("AutoOS.Voice")


def transcribe_audio(file_path: str) -> str:
    """
    Transcribe an audio file using Gemini Flash.
    Falls back to local faster-whisper if Gemini is unavailable.
    """
    api_key = os.getenv("GOOGLE_API_KEY", "")

    if api_key:
        try:
            return _transcribe_gemini(file_path, api_key)
        except Exception as e:
            logger.warning("Gemini transcription failed, falling back to local: %s", e)

    return _transcribe_local(file_path)


def _transcribe_gemini(file_path: str, api_key: str) -> str:
    """Transcribe using Gemini Flash via the google-genai SDK."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    with open(file_path, "rb") as f:
        audio_data = f.read()

    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {
        ".webm": "audio/webm",
        ".ogg": "audio/ogg",
        ".wav": "audio/wav",
        ".mp3": "audio/mp3",
        ".m4a": "audio/mp4",
    }
    mime = mime_map.get(ext, "audio/webm")

    audio_part = types.Part.from_bytes(data=audio_data, mime_type=mime)

    prompt = (
        "Transcribe the following audio exactly as spoken. "
        "Return ONLY the transcribed text, nothing else. "
        "No preamble, no quotes, no explanation. Just the raw words spoken."
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=[prompt, audio_part],
    )

    text = response.text.strip().strip('"').strip("'")
    logger.info("Gemini transcription: '%s'", text)
    return text


def _transcribe_local(file_path: str) -> str:
    """Fallback: transcribe using local faster-whisper."""
    from faster_whisper import WhisperModel

    model_size = os.getenv("WHISPER_MODEL", "base")
    logger.info("Using local faster-whisper model: %s", model_size)
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    segments, info = model.transcribe(
        file_path,
        beam_size=5,
        language="en",
        vad_filter=True,
    )

    text = " ".join(seg.text.strip() for seg in segments).strip()
    logger.info("Local transcription (%s, %.1fs): '%s'", info.language, info.duration, text)
    return text
