from typing import Optional, List
from pydantic import BaseModel

class TTSRequest(BaseModel):
    text: str
    voiceId: Optional[str] = "en-US-natalie"

class TTSResponse(BaseModel):
    success: bool
    audio_url: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None

class TranscriptionResponse(BaseModel):
    success: bool
    transcription: Optional[str] = None
    filename: Optional[str] = None
    error: Optional[str] = None

class LLMRequest(BaseModel):
    text: str

class LLMTextResponse(BaseModel):
    response: str

class ChatItem(BaseModel):
    role: str
    content: str
    timestamp: str

class ChatHistoryResponse(BaseModel):
    success: bool
    session_id: str
    message_count: int
    messages: List[ChatItem] = []
