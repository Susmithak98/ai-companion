# core/speaker.py
import pyttsx3

def speak(text, filename="response.mp3"):
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