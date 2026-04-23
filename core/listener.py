# core/listener.py
import pyaudio
import wave
import os
import webrtcvad
import collections

OUTPUT_DIR = "outputs/"

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
                print("🔴 Recording... (will stop when you finish speaking)")
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
        print("⚠️  No voice detected. Please speak again.")
        return None

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(b"".join(voiced_frames))

    return filepath