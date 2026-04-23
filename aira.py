# aira.py
# ALL core logic in one file:
# Listener, Transcriber, Emotion Detection, Brain, Speaker
import os
import sys

# Tell Whisper exactly where ffmpeg is
os.environ["PATH"] += os.pathsep + r"C:\ffmpeg\bin"
import pyaudio
import wave
import os
import webrtcvad
import collections
import whisper
import requests
import pyttsx3
from textblob import TextBlob
from config import OLLAMA_URL, OLLAMA_MODEL, OUTPUT_DIR



# ============================================================
# LISTENER — records your voice
# ============================================================

def record_audio(filename="input.wav", seconds=30):
    CHUNK_DURATION = 0.03
    RATE = 16000
    CHUNK = int(RATE * CHUNK_DURATION)
    FORMAT = pyaudio.paInt16
    CHANNELS = 1

    vad = webrtcvad.Vad(2)
    recorder = pyaudio.PyAudio()
    stream = recorder.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    print("\n🎙️  Listening... speak whenever you are ready!")

    ring_buffer = collections.deque(maxlen=30)
    triggered = False
    voiced_frames = []
    silent_chunks = 0
    max_silent_chunks = 60
    max_chunks = int(seconds / CHUNK_DURATION)
    chunk_count = 0

    while chunk_count < max_chunks:
        chunk = stream.read(CHUNK, exception_on_overflow=False)
        chunk_count += 1
        is_speech = False
        try:
            is_speech = vad.is_speech(chunk, RATE)
        except:
            pass
        if not triggered:
            ring_buffer.append(chunk)
            if is_speech:
                triggered = True
                print("🔴 Recording...")
                voiced_frames.extend(ring_buffer)
                ring_buffer.clear()
                silent_chunks = 0
        else:
            voiced_frames.append(chunk)
            if not is_speech:
                silent_chunks += 1
                if silent_chunks > max_silent_chunks:
                    print("✅ Got it!")
                    break
            else:
                silent_chunks = 0

    stream.stop_stream()
    stream.close()
    recorder.terminate()

    if not voiced_frames:
        print("⚠️  No voice detected.")
        return None

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(b"".join(voiced_frames))

    return filepath


# ============================================================
# TRANSCRIBER — converts voice to text
# ============================================================

print("Loading Whisper model...")
WHISPER_MODEL = whisper.load_model("base")
print("✅ Whisper ready!")

def transcribe(audio_filepath):
    if not audio_filepath or not os.path.exists(audio_filepath):
        return ""
    print("Understanding what you said...")
    try:
        result = WHISPER_MODEL.transcribe(
            audio_filepath,
            fp16=False,
            language="en"
        )
        text = result["text"].strip()
        if text:
            print(f"✅ You said: {text}")
        return text
    except Exception as e:
        print(f"Transcription error: {e}")
        return ""


# ============================================================
# EMOTION DETECTOR — detects how you feel
# ============================================================

KEYWORDS = {
    "sad": ["sad", "unhappy", "depressed", "hopeless", "cry", "lonely",
            "empty", "worthless", "hurt", "grief", "miserable", "heartbroken"],
    "stressed": ["stressed", "overwhelmed", "anxious", "worried", "panic",
                 "too much", "pressure", "exhausted", "cant cope"],
    "angry": ["angry", "mad", "furious", "frustrated", "hate", "unfair",
              "sick of", "fed up", "annoyed"],
    "happy": ["happy", "great", "wonderful", "excited", "joyful", "good",
              "grateful", "love", "amazing", "thankful", "blessed"]
}

def detect_emotion(text):
    if not text:
        return "neutral"
    low = text.lower()
    scores = {}
    for emotion, words in KEYWORDS.items():
        count = sum(1 for w in words if w in low)
        if count > 0:
            scores[emotion] = count
    if scores:
        best = max(scores, key=scores.get)
        print(f"💡 Emotion: {best}")
        return best
    polarity = TextBlob(text).sentiment.polarity
    if polarity < -0.3: return "sad"
    if polarity < -0.1: return "stressed"
    if polarity > 0.3:  return "happy"
    return "neutral"


# ============================================================
# BRAIN — gets AI response from Ollama
# ============================================================
SYSTEM_PROMPT = """You are Aira, a warm and empathetic AI companion from India.
You naturally understand Indian culture, family dynamics, and the experiences of NRIs.
You speak like a caring friend — warm, supportive, and genuinely interested.
You understand when someone mentions Indian contexts but don't force it.
Keep responses to 2-3 natural sentences. Be present, not repetitive."""



def get_response(user_text, emotion="neutral", history=None):
    if history is None:
        history = []

    from agents import get_memory_context, extract_facts, get_mood_summary
    extract_facts(user_text)
    memory_context = get_memory_context()
    mood_summary = get_mood_summary()

    emotion_hints = {
        "sad":     "User is sad. Be very gentle and validating.",
        "stressed":"User is stressed. Be calm and reassuring.",
        "angry":   "User is frustrated. Acknowledge feelings calmly.",
        "happy":   "User is happy. Match their warm energy.",
        "neutral": "Be warm and curious."
    }
    hint = emotion_hints.get(emotion, emotion_hints["neutral"])

    history_text = ""
    for m in history[-6:]:
        role = "User" if m["role"] == "user" else "Aira"
        history_text += f"{role}: {m['content']}\n"

    prompt = f"""{SYSTEM_PROMPT}
[Memory: {memory_context}]
[{mood_summary}]
[{hint}]

{history_text}User: {user_text}
Aira:"""

    print("\nAira: ", end="", flush=True)

    full_reply = ""
    current_sentence = ""

    try:
        # Stream response word by word
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": True,     # KEY CHANGE — stream on
                "options": {
                    "temperature": 0.8,
                    "num_predict": 60
                }
            },
            stream=True,
            timeout=60
        )

        for line in r.iter_lines():
            if line:
                import json as json_lib
                chunk = json_lib.loads(line)
                word = chunk.get("response", "")
                print(word, end="", flush=True)
                current_sentence += word
                full_reply += word

                # Speak immediately when sentence is complete
                if any(current_sentence.strip().endswith(p) for p in [".", "!", "?", "..."]):
                    sentence = current_sentence.strip()
                    if sentence and len(sentence) > 5:
                        speak(sentence)
                        current_sentence = ""

                if chunk.get("done", False):
                    break

        # Speak any remaining text
        if current_sentence.strip():
            speak(current_sentence.strip())

        #print()  # New line after response
        return full_reply.strip()

    except Exception as e:
        print(f"\nError: {e}")
        fallback = "I am here for you. Can you tell me more?"
        speak(fallback)
        return fallback


# ============================================================
# SPEAKER — Aira speaks back to you
# ============================================================

def speak(text):
    if not text:
        return
    print(f"\nAira: {text}")
    engine = pyttsx3.init()
    engine.setProperty('rate', 165)
    engine.setProperty('volume', 1.0)
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'zira' in voice.name.lower() or 'female' in voice.name.lower():
            engine.setProperty('voice', voice.id)
            break
    engine.say(text)
    engine.runAndWait()
    engine.stop()