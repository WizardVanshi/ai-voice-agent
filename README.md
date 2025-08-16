# 🎙️ AI Voice Agent
> Conversational bot with memory, powered by FastAPI + AssemblyAI + Murf AI

An interactive voice-based AI assistant that listens, thinks, and responds — all in real time.  
Built with **FastAPI**, **Gemini AI**, **Murf AI**, and **AssemblyAI**, it remembers past conversations and delivers smooth, natural interactions.

---

## ✨ What It Does
- 🎤 **Voice Input** — Speak directly into your browser  
- 🧠 **AI Memory** — Maintains chat history per session  
- 💬 **Smart Responses** — Powered by Google's Gemini AI  
- 🔊 **Voice Output** — AI replies in natural-sounding speech using Murf AI  
- ⚡ **Auto Record** — Option to automatically listen after AI replies  
- 🎨 **Modern UI** — Clean, responsive design with a single dynamic record button  

---

## 🛠 Tech Stack

| Layer      | Technologies |
|------------|--------------|
| Frontend   | HTML5, CSS3 (`style.css`), Vanilla JavaScript (`script.js`, MediaRecorder API) |
| Backend    | FastAPI (Python) |
| APIs       | AssemblyAI (speech-to-text), Gemini AI (text generation), Murf AI (text-to-speech) |
| Storage    | In-memory session storage for conversation history |

---

## 🏗 How It Works

1. You press the record button and speak  
2. Audio is recorded in the browser and sent to the backend  
3. AssemblyAI transcribes your voice to text  
4. The transcription, along with your session's history, is sent to Gemini AI  
5. Gemini AI generates a contextual response  
6. Response is converted to speech via Murf AI  
7. The audio plays back automatically in your browser  
8. (Optional) Auto-record starts again for seamless back-and-forth  

---

## 📂 Project Structure
```
.
├── static/
│   ├── style.css       # Styling
│   └── script.js       # Frontend logic & recording
├── templates/
│   └── index.html      # UI template
├── services/           # STT, TTS, LLM service logic
│   ├── stt_service.py
│   ├── tts_service.py
│   └── llm_service.py
├── models/
│   └── schemas.py      # Pydantic models (request/response)
├── utils/
│   └── logger.py       # Logging utility
├── uploads/            # Temp audio storage (gitignored)
├── main.py             # FastAPI backend entrypoint
├── requirements.txt    # Python dependencies
└── README.md
```

---

## ✅ Requirements
- Python 3.10+  
- pip (Python package manager)  
- FastAPI  
- Uvicorn  

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the repository
```bash
git clone https://github.com/yourusername/ai-voice-agent.git
cd ai-voice-agent
```

### 2️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 3️⃣ Add environment variables  
Create a `.env` file in the root directory:
```env
MURF_API_KEY=your_murf_api_key
ASSEMBLY_API_KEY=your_assemblyai_api_key
```

### 4️⃣ Run the server
```bash
uvicorn main:app --reload
```

### 5️⃣ Open in browser
Go to:
```
http://127.0.0.1:8000
```

---

## 📡 API Usage

### 🔹 Transcribe Audio
```bash
curl -X POST "http://127.0.0.1:8000/transcribe/file"      -F "file=@sample.wav"
```

### 🔹 TTS Echo (STT → TTS)
```bash
curl -X POST "http://127.0.0.1:8000/tts/echo"      -F "file=@sample.wav"
```

### 🔹 Start New Session
```bash
curl -X POST "http://127.0.0.1:8000/agent/session/new"
```

### 🔹 Chat with Agent
```bash
curl -X POST "http://127.0.0.1:8000/agent/chat/{session_id}"      -H "Content-Type: application/json"      -d '{"message": "Hello, how are you?"}'
```

---

## 📸 Screenshots

### Home Screen
![Home](/screenshots/home_page.png)

### Recording State
![Recording](/screenshots/recording.png)

### Transcription Output
![Response](/screenshots/response.png)

### API Docs (Swagger)
![API Docs](/screenshots/docs.png)

---

## 🔮 Possible Improvements
- Persistent database for chat history  
- User authentication  
- Multi-voice and language options  
- Offline transcription with local models  

---

## 📜 License
MIT — Free to use, modify, and share.
