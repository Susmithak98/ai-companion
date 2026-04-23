# core/transcriber.py
import speech_recognition as sr
import os

recognizer = sr.Recognizer()
print("Speech recognizer ready!")

def transcribe(audio_filepath):

    if not os.path.exists(audio_filepath):
        return ""

    print("Understanding what you said...")

    with sr.AudioFile(audio_filepath) as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.1)
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio, language="en-US")
        print(f"✅ You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Could not understand. Please speak clearly.")
        return ""
    except Exception as e:
        print(f"Error: {e}")
        return ""