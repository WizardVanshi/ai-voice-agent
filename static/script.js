// Chat Agent functionality with combined record button
let chatMediaRecorder;
let chatAudioChunks = [];
let currentSessionId = getSessionId();
let isAutoRecordingEnabled = false;
let autoRecordTimeout = null;
let recordingState = 'ready'; // 'ready', 'recording', 'processing'

const recordButton = document.getElementById('record-button');
const recordIcon = document.getElementById('record-icon');
const recordStatus = document.getElementById('record-status');
const chatAudio = document.getElementById('chat-audio');
const processingIndicator = document.getElementById('processing-indicator');
const processingText = document.getElementById('processing-text');
const conversationDisplay = document.getElementById('conversation-display');
const userQuestion = document.getElementById('user-question');
const aiResponse = document.getElementById('ai-response');
const sessionIdDisplay = document.getElementById('session-id-display');
const newSessionBtn = document.getElementById('new-session-btn');
const autoRecordToggle = document.getElementById('auto-record-toggle');

// Get or create session ID from URL params
function getSessionId() {
    const urlParams = new URLSearchParams(window.location.search);
    let sessionId = urlParams.get('session_id');

    if (!sessionId) {
        sessionId = 'chat-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        const newUrl = new URL(window.location);
        newUrl.searchParams.set('session_id', sessionId);
        window.history.replaceState({}, '', newUrl);
    }

    return sessionId;
}

// Update UI based on recording state
function updateRecordButton(state) {
    recordingState = state;
    recordButton.className = 'record-button';
    recordStatus.className = 'record-status';

    const micIcon = `<path d="M12 14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2s-2 .9-2 2v6c0 1.1.9 2 2 2zm5-2c0 2.8-2.2 5-5 5s-5-2.2-5-5H5c0 3.5 2.6 6.4 6 6.9V21h2v-2.1c3.4-.5 6-3.4 6-6.9h-2z"/>`;
    const stopIcon = `<rect x="6" y="6" width="12" height="12"/>`;

    switch (state) {
        case 'ready':
            recordButton.classList.add('ready');
            recordStatus.innerHTML = '<span class="status-ready">Ready to listen</span>';
            recordIcon.innerHTML = micIcon;
            recordButton.disabled = false;
            break;
        case 'recording':
            recordButton.classList.add('recording');
            recordStatus.innerHTML = '<div class="recording-dot"></div><span class="status-recording">Recording...</span>';
            recordIcon.innerHTML = stopIcon;
            recordButton.disabled = false;
            break;
        case 'processing':
            recordButton.classList.add('processing');
            recordStatus.innerHTML = '<span class="status-processing">Processing...</span>';
            recordIcon.innerHTML = micIcon;
            recordButton.disabled = true;
            break;
    }
}

// Initialize UI
if (sessionIdDisplay) {
    sessionIdDisplay.textContent = `Session: ${currentSessionId}`;
}

// Auto-record toggle
if (autoRecordToggle) {
    autoRecordToggle.addEventListener('change', function () {
        isAutoRecordingEnabled = this.checked;
        console.log('Auto-recording:', isAutoRecordingEnabled ? 'enabled' : 'disabled');
    });
}

// New session button
if (newSessionBtn) {
    newSessionBtn.addEventListener('click', async () => {
        try {
            const response = await fetch('/agent/session/new', { method: 'POST' });
            const data = await response.json();

            if (data.success) {
                currentSessionId = data.session_id;

                const newUrl = new URL(window.location);
                newUrl.searchParams.set('session_id', currentSessionId);
                window.history.replaceState({}, '', newUrl);

                if (sessionIdDisplay) {
                    sessionIdDisplay.textContent = `Session: ${currentSessionId}`;
                }

                if (conversationDisplay) {
                    conversationDisplay.style.display = 'none';
                }

                updateRecordButton('ready');
                console.log('New session created:', currentSessionId);
            }
        } catch (error) {
            console.error('Error creating new session:', error);
        }
    });
}

// Function to start auto-recording after audio ends
function scheduleAutoRecord() {
    if (!isAutoRecordingEnabled || !chatAudio) return;

    if (autoRecordTimeout) {
        clearTimeout(autoRecordTimeout);
    }

    autoRecordTimeout = setTimeout(() => {
        if (recordingState === 'ready' && isAutoRecordingEnabled) {
            console.log('Auto-starting recording...');
            startRecording();
        }
    }, 1500);
}

// Listen for audio end event
if (chatAudio) {
    chatAudio.addEventListener('ended', scheduleAutoRecord);
}

// Start recording function
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        chatMediaRecorder = new MediaRecorder(stream);
        chatAudioChunks = [];

        chatMediaRecorder.ondataavailable = event => {
            chatAudioChunks.push(event.data);
        };

        chatMediaRecorder.onstop = async () => {
            const audioBlob = new Blob(chatAudioChunks, { type: 'audio/webm' });
            stream.getTracks().forEach(track => track.stop());

            updateRecordButton('processing');
            processingIndicator.style.display = 'flex';
            processingText.textContent = 'Transcribing your message...';
            conversationDisplay.style.display = 'none';

            try {
                const formData = new FormData();
                formData.append('file', audioBlob, 'chat.webm');
                formData.append('voice_id', 'en-US-natalie');

                processingText.textContent = 'Thinking with Gemini AI...';

                const response = await fetch(`/agent/chat/${currentSessionId}`, {
                    method: 'POST',
                    body: formData
                });

                if (response.ok) {
                    const result = await response.json();

                    if (result.success) {
                        if (result.transcription && result.llm_response) {
                            if (userQuestion) {
                                userQuestion.textContent = result.transcription;
                            }
                            if (aiResponse) {
                                aiResponse.textContent = result.llm_response;
                            }
                            if (conversationDisplay) {
                                conversationDisplay.style.display = 'block';
                            }
                        }

                        processingText.textContent = 'Converting to speech...';

                        if (result.audio_url && chatAudio) {
                            chatAudio.src = result.audio_url;
                            processingIndicator.style.display = 'none';
                            updateRecordButton('ready');

                            try {
                                await chatAudio.play();
                            } catch (e) {
                                console.log('Auto-play blocked');
                            }
                        } else {
                            processingIndicator.style.display = 'none';
                            updateRecordButton('ready');
                        }
                    } else {
                        processingIndicator.style.display = 'none';
                        updateRecordButton('ready');
                        console.error('Chat processing failed:', result.error);

                        if (result.transcription && userQuestion) {
                            userQuestion.textContent = result.transcription;
                            conversationDisplay.style.display = 'block';
                        }
                    }
                } else {
                    processingIndicator.style.display = 'none';
                    updateRecordButton('ready');
                    console.error('Server error:', response.status);
                }

            } catch (err) {
                processingIndicator.style.display = 'none';
                updateRecordButton('ready');
                console.error('Network error:', err);
            }
        };

        chatMediaRecorder.start();
        updateRecordButton('recording');

    } catch (err) {
        alert('Microphone access denied or not available.');
        console.error('Error accessing microphone:', err);
    }
}

// Stop recording function
function stopRecording() {
    if (chatMediaRecorder && chatMediaRecorder.state !== 'inactive') {
        chatMediaRecorder.stop();
    }
}

// Combined record button click handler
if (recordButton) {
    recordButton.addEventListener('click', () => {
        if (recordingState === 'ready') {
            startRecording();
        } else if (recordingState === 'recording') {
            stopRecording();
        }
    });
}

// Initialize
updateRecordButton('ready');
console.log('Professional AI Voice Agent loaded!');
console.log('Current session ID:', currentSessionId);