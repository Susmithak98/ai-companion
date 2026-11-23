"""Transcriber: offline speech-to-text with OpenAI Whisper (loaded once, on first use)."""
import os

from config import FFMPEG_DIR, WHISPER_MODEL

_model = None


def _load():
    global _model
    if _model is None:
        if FFMPEG_DIR:
            os.environ["PATH"] += os.pathsep + FFMPEG_DIR
        import whisper
        print(f"Loading Whisper '{WHISPER_MODEL}' model...")
        _model = whisper.load_model(WHISPER_MODEL)
        print("✅ Whisper ready!")
    return _model


def transcribe(audio_path) -> str:
    if not audio_path or not os.path.exists(audio_path):
        return ""
    try:
        result = _load().transcribe(audio_path, fp16=False, language="en")
        return result["text"].strip()
    except Exception as exc:  # keep the conversation going even if one clip fails
        print(f"Transcription error: {exc}")
        return ""
