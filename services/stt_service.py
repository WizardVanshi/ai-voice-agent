import assemblyai as aai
from utils.logger import get_logger

logger = get_logger("STTService")

def transcribe_file(file_path: str, api_key: str) -> dict:
    """
    Returns dict:
      { "success": True, "text": "..."} or
      { "success": False, "error": "..." }
    """
    try:
        aai.settings.api_key = api_key
        config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
        transcript = aai.Transcriber(config=config).transcribe(file_path)

        if transcript.status == "error":
            logger.error(f"AssemblyAI error: {transcript.error}")
            return {"success": False, "error": transcript.error}

        text = (transcript.text or "").strip()
        if not text:
            return {"success": False, "error": "Empty transcription"}
        return {"success": True, "text": text}

    except Exception as e:
        logger.exception("Transcription failed")
        return {"success": False, "error": str(e)}
