import json
import requests
from utils.logger import get_logger

logger = get_logger("TTSService")

def _extract_audio_url(data: dict) -> str | None:
    return (
        data.get("audioFile")
        or data.get("audio_url")
        or data.get("url")
        or data.get("audioUrl")
        or data.get("file")
        or data.get("download_url")
    )

def generate_speech(text: str, api_key: str, voice_id: str = "en-US-natalie") -> dict:
    """
    Returns dict:
      { "success": True, "audio_url": "..."} or
      { "success": False, "error": "..." }
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "api-key": api_key
        }
        payload = {"text": text, "voiceId": voice_id}

        response = requests.post(
            "https://api.murf.ai/v1/speech/generate",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            logger.error(f"Murf API error {response.status_code}: {response.text[:300]}")
            # try best-effort to parse error
            try:
                err = response.json().get("message") or response.json().get("error") or response.text
            except json.JSONDecodeError:
                err = response.text
            return {"success": False, "error": f"Murf API error: {err}"}

        data = response.json()
        audio_url = _extract_audio_url(data)
        if not audio_url:
            logger.error(f"No audio URL in Murf response: {data}")
            return {"success": False, "error": "No audio URL returned by Murf"}
        return {"success": True, "audio_url": audio_url}

    except Exception as e:
        logger.exception("Murf TTS failed")
        return {"success": False, "error": str(e)}
