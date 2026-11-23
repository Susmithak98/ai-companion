"""Listener: records from the microphone only while you are speaking (WebRTC VAD)."""
import collections
import os
import wave

from config import MAX_RECORD_SECONDS, OUTPUT_DIR, SAMPLE_RATE

CHUNK_DURATION = 0.03                 # 30 ms frames, required by webrtcvad
CHUNK = int(SAMPLE_RATE * CHUNK_DURATION)
SILENCE_CHUNKS_TO_STOP = 60           # ~1.8 s of silence ends the recording


def record_audio(filename: str = "input.wav", seconds: int = MAX_RECORD_SECONDS):
    """Record one utterance and return the path to a WAV file, or None if nothing was heard."""
    import pyaudio
    import webrtcvad

    vad = webrtcvad.Vad(2)
    recorder = pyaudio.PyAudio()
    stream = recorder.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE,
                           input=True, frames_per_buffer=CHUNK)
    print("\n🎙️  Listening... speak whenever you are ready!")

    ring_buffer = collections.deque(maxlen=30)
    voiced, triggered, silent = [], False, 0
    try:
        for _ in range(int(seconds / CHUNK_DURATION)):
            chunk = stream.read(CHUNK, exception_on_overflow=False)
            try:
                is_speech = vad.is_speech(chunk, SAMPLE_RATE)
            except Exception:
                is_speech = False
            if not triggered:
                ring_buffer.append(chunk)
                if is_speech:
                    triggered = True
                    print("🔴 Recording...")
                    voiced.extend(ring_buffer)
                    ring_buffer.clear()
            else:
                voiced.append(chunk)
                silent = 0 if is_speech else silent + 1
                if silent > SILENCE_CHUNKS_TO_STOP:
                    print("✅ Got it!")
                    break
    finally:
        stream.stop_stream()
        stream.close()
        recorder.terminate()

    if not voiced:
        print("⚠️  No voice detected.")
        return None

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, filename)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"".join(voiced))
    return path
