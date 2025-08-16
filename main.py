import os
import uuid
import shutil
import json
from datetime import datetime
from typing import Dict, List

from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from models.schemas import (
    TTSRequest, TTSResponse, TranscriptionResponse,
    LLMRequest, LLMTextResponse, ChatHistoryResponse
)
from services.stt_service import transcribe_file
from services.tts_service import generate_speech
from services.llm_service import generate_llm_text
from utils.logger import get_logger

# ── Env & App ──────────────────────────────────────────────────────────────────
load_dotenv()
MURF_API_KEY = os.getenv("MURF_API_KEY")
ASSEMBLY_API_KEY = os.getenv("ASSEMBLY_API_KEY")

app = FastAPI(title="AI Voice Agent", version="2.0.0")
logger = get_logger("MainApp")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static & Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory chat history: { session_id: [ {role, content, timestamp}, ... ] }
chat_sessions: Dict[str, List[dict]] = {}

# ── Routes: UI ─────────────────────────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# ── Health & Debug ─────────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "murf_api_key": bool(MURF_API_KEY),
        "assembly_api_key": bool(ASSEMBLY_API_KEY),
    }

@app.get("/debug/api-key")
def debug_api_key():
    return {
        "murf_configured": bool(MURF_API_KEY),
        "murf_preview": f"{MURF_API_KEY[:6]}..." if MURF_API_KEY else None,
        "assembly_configured": bool(ASSEMBLY_API_KEY),
        "assembly_preview": f"{ASSEMBLY_API_KEY[:6]}..." if ASSEMBLY_API_KEY else None,
    }

# ── Basic upload (optional helper) ─────────────────────────────────────────────
@app.post("/upload_audio")
async def upload_audio(file: UploadFile = File(...)):
    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": os.path.getsize(path),
    }

# ── Text → TTS (Murf) ─────────────────────────────────────────────────────────
@app.post("/generate_speech", response_model=TTSResponse)
def generate_speech_route(request: TTSRequest):
    if not MURF_API_KEY:
        return TTSResponse(success=False, error="Murf API key not configured")
    text = (request.text or "").strip()
    if not text:
        return TTSResponse(success=False, error="Text cannot be empty")

    # Mock path for quick testing
    if MURF_API_KEY in ("your_api_key_here", "test_key"):
        return TTSResponse(
            success=True,
            audio_url="https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
            message=f"Mock TTS for voice {request.voiceId}"
        )

    out = generate_speech(text, MURF_API_KEY, request.voiceId)
    if not out["success"]:
        return TTSResponse(success=False, error=out["error"])
    return TTSResponse(success=True, audio_url=out["audio_url"], message=f"Voice: {request.voiceId}")

# ── STT (AssemblyAI) ──────────────────────────────────────────────────────────
@app.post("/transcribe/file", response_model=TranscriptionResponse)
async def transcribe_file_route(file: UploadFile = File(...)):
    if not ASSEMBLY_API_KEY:
        return TranscriptionResponse(success=False, error="AssemblyAI API key not configured")

    path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        out = transcribe_file(path, ASSEMBLY_API_KEY)
        if not out["success"]:
            return TranscriptionResponse(success=False, error=out["error"], filename=file.filename)

        return TranscriptionResponse(success=True, transcription=out["text"], filename=file.filename)
    finally:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

# ── Echo Bot: Audio → STT → Murf TTS ──────────────────────────────────────────
@app.post("/tts/echo")
async def tts_echo(file: UploadFile = File(...), voice_id: str = "en-US-natalie"):
    if not ASSEMBLY_API_KEY:
        return {"success": False, "error": "AssemblyAI API key not configured"}
    if not MURF_API_KEY:
        return {"success": False, "error": "Murf API key not configured"}

    path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # 1) STT
        stt = transcribe_file(path, ASSEMBLY_API_KEY)
        if not stt["success"]:
            return {"success": False, "error": f"Transcription failed: {stt['error']}", "transcription": None, "audio_url": None}

        transcription = stt["text"]

        # Mock path (optional testing)
        if MURF_API_KEY in ("your_api_key_here", "test_key"):
            return {
                "success": True,
                "transcription": transcription,
                "audio_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
                "message": f"Mock echo with voice {voice_id}"
            }

        # 2) TTS
        tts = generate_speech(transcription, MURF_API_KEY, voice_id)
        if not tts["success"]:
            return {"success": False, "error": f"Murf TTS failed: {tts['error']}", "transcription": transcription, "audio_url": None}

        return {"success": True, "transcription": transcription, "audio_url": tts["audio_url"], "message": f"Echo complete with {voice_id}"}
    finally:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

# ── LLM (Text) ────────────────────────────────────────────────────────────────
@app.post("/llm/query", response_model=LLMTextResponse)
async def llm_query(request: LLMRequest):
    prompt = request.text
    out = generate_llm_text(prompt)
    if not out["success"]:
        raise HTTPException(status_code=500, detail=out["error"])
    return LLMTextResponse(response=out["text"])

# ── Voice LLM: Audio → STT → Gemini → Murf TTS ────────────────────────────────
@app.post("/llm/voice-query")
async def voice_llm_query(file: UploadFile = File(...), voice_id: str = "en-US-natalie"):
    if not ASSEMBLY_API_KEY:
        return {"success": False, "error": "AssemblyAI API key not configured"}
    if not MURF_API_KEY:
        return {"success": False, "error": "Murf API key not configured"}

    path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # STT
        stt = transcribe_file(path, ASSEMBLY_API_KEY)
        if not stt["success"]:
            return {"success": False, "error": f"Transcription failed: {stt['error']}", "transcription": None, "llm_response": None, "audio_url": None}
        transcription = stt["text"]

        # LLM
        enhanced_prompt = (
            "Please provide a helpful and concise response (under 2500 chars) to this:\n\n"
            f"User: {transcription}\n\nResponse:"
        )
        llm = generate_llm_text(enhanced_prompt)
        if not llm["success"]:
            return {"success": False, "error": f"LLM failed: {llm['error']}", "transcription": transcription, "llm_response": None, "audio_url": None}
        llm_response = llm["text"][:2500]

        # Mock (optional)
        if MURF_API_KEY in ("your_api_key_here", "test_key"):
            return {
                "success": True,
                "transcription": transcription,
                "llm_response": llm_response,
                "audio_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
                "message": "Mock voice LLM"
            }

        # TTS
        tts = generate_speech(llm_response, MURF_API_KEY, voice_id)
        if not tts["success"]:
            return {"success": False, "error": f"Murf TTS failed: {tts['error']}", "transcription": transcription, "llm_response": llm_response, "audio_url": None}

        return {"success": True, "transcription": transcription, "llm_response": llm_response, "audio_url": tts["audio_url"], "message": f"Voice LLM complete with {voice_id}"}
    finally:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

# ── Agent Chat (with session history) ─────────────────────────────────────────
@app.post("/agent/session/new")
async def new_session():
    session_id = str(uuid.uuid4())
    chat_sessions[session_id] = []
    return {"success": True, "session_id": session_id, "message": "New chat session created"}

@app.get("/agent/chat/{session_id}/history", response_model=ChatHistoryResponse)
async def chat_history(session_id: str):
    messages = chat_sessions.get(session_id, [])
    return {
        "success": session_id in chat_sessions,
        "session_id": session_id,
        "message_count": len(messages),
        "messages": messages,
    }

@app.post("/agent/chat/{session_id}")
async def agent_chat(session_id: str, file: UploadFile = File(...), voice_id: str = "en-US-natalie"):
    if not ASSEMBLY_API_KEY:
        return {"success": False, "error": "AssemblyAI API key not configured"}
    if not MURF_API_KEY:
        return {"success": False, "error": "Murf API key not configured"}

    path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # STT
        stt = transcribe_file(path, ASSEMBLY_API_KEY)
        if not stt["success"]:
            return {"success": False, "error": f"Transcription failed: {stt['error']}", "session_id": session_id}

        transcription = stt["text"]

        # Ensure session
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []

        # Add user message
        chat_sessions[session_id].append({
            "role": "user", "content": transcription, "timestamp": datetime.now().isoformat()
        })

        # Build context (last ~10 exchanges)
        recent = chat_sessions[session_id][-19:]
        context = "You are a helpful AI assistant. Here's our conversation so far:\n\n"
        for msg in recent[:-1]:
            prefix = "User" if msg["role"] == "user" else "Assistant"
            context += f"{prefix}: {msg['content']}\n"
        context += f"User: {transcription}\n\nPlease provide a helpful response (under 2500 chars):"

        # LLM
        llm = generate_llm_text(context)
        if not llm["success"]:
            return {"success": False, "error": f"LLM failed: {llm['error']}", "session_id": session_id, "transcription": transcription}

        llm_response = llm["text"][:2500]

        # Save assistant message
        chat_sessions[session_id].append({
            "role": "assistant", "content": llm_response, "timestamp": datetime.now().isoformat()
        })

        # Mock (optional)
        if MURF_API_KEY in ("your_api_key_here", "test_key"):
            return {
                "success": True,
                "session_id": session_id,
                "transcription": transcription,
                "llm_response": llm_response,
                "audio_url": "https://www.soundjay.com/misc/sounds/bell-ringing-05.wav",
                "message": f"Mock chat agent for session {session_id}"
            }

        # TTS
        tts = generate_speech(llm_response, MURF_API_KEY, voice_id)
        if not tts["success"]:
            return {"success": False, "error": f"Murf TTS failed: {tts['error']}", "session_id": session_id, "transcription": transcription, "llm_response": llm_response}

        return {
            "success": True,
            "session_id": session_id,
            "transcription": transcription,
            "llm_response": llm_response,
            "audio_url": tts["audio_url"],
            "message": f"Chat response complete! Session: {session_id}, Voice: {voice_id}"
        }
    finally:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass
