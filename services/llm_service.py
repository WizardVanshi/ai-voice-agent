from utils.logger import get_logger
from google import genai

logger = get_logger("LLMService")

def generate_llm_text(prompt: str, model: str = "gemini-2.5-flash") -> dict:
    """
    Returns dict:
      { "success": True, "text": "..."} or
      { "success": False, "error": "..." }
    """
    try:
        client = genai.Client()
        response = client.models.generate_content(model=model, contents=prompt)
        text = (response.text or "").strip()
        if not text:
            return {"success": False, "error": "Empty LLM response"}
        return {"success": True, "text": text}
    except Exception as e:
        logger.exception("LLM generation failed")
        return {"success": False, "error": str(e)}
