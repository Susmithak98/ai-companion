# main.py
import requests
from aira import record_audio, transcribe, detect_emotion, get_response, speak
from agents import (
    load_memory, update_last_seen,
    log_mood, check_consecutive_sad,
    check_crisis, get_crisis_response,
    should_suggest_exercise, get_exercise, get_exercise_intro
)

def check_ollama():
    try:
        requests.get("http://localhost:11434", timeout=3)
        print("✅ Ollama is running!")
        return True
    except:
        print("❌ Ollama is not running!")
        print("Open a NEW terminal and run: ollama serve")
        return False

def run_exercise(exercise):
    for step in exercise["steps"]:
        speak(step)

def main():
    print("\n" + "="*45)
    print("   AIRA - Your AI Voice Companion")
    print("="*45)
    print("\n   Just SPEAK — Aira listens automatically!")
    print("   Say bye to exit\n")

    if not check_ollama():
        return

    update_last_seen()

    memory = load_memory()
    if memory["user_name"]:
        greeting = f"Welcome back {memory['user_name']}. I am Aira. How are you feeling today?"
    else:
        greeting = "Hi there. I am Aira. I am here for you. Just start talking."

    speak(greeting)

    history = []
    turn = 0
    failed = 0

    while True:
        turn += 1
        print("\n" + "-"*45)

        audio = record_audio(f"input_{turn}.wav")

        if audio is None:
            failed += 1
            if failed >= 3:
                speak("I cannot hear you. Please check your microphone.")
                failed = 0
            continue

        text = transcribe(audio)

        if not text:
            failed += 1
            if failed >= 3:
                speak("Please speak a little louder and clearly.")
                failed = 0
            continue

        failed = 0
        print(f"\n👤 You: {text}")

        if any(w in text.lower() for w in ["goodbye", "bye", "exit", "quit", "stop"]):
            speak("Take care of yourself. I am always here for you. Goodbye.")
            break

        # Crisis check first
        crisis_level = check_crisis(text)
        if crisis_level in ["crisis", "concern"]:
            crisis_reply = get_crisis_response(crisis_level)
            speak(crisis_reply)
            history.append({"role": "user", "content": text})
            history.append({"role": "assistant", "content": crisis_reply})
            continue

        emotion = detect_emotion(text)
        log_mood(emotion, text)

        # Warn if sad too many times
        sad_count = check_consecutive_sad()
        if sad_count >= 5:
            speak("I noticed you have been feeling down a lot lately. I care about you deeply. Please consider talking to someone you trust.")

        history.append({"role": "user", "content": text})

        # Suggest exercise occasionally
        if should_suggest_exercise(emotion, turn):
            exercise = get_exercise(emotion)
            if exercise:
                intro = get_exercise_intro(emotion)
                speak(intro)
                audio2 = record_audio(f"exercise_{turn}.wav")
                if audio2:
                    response = transcribe(audio2)
                    if response and "yes" in response.lower():
                        run_exercise(exercise)
                        history.append({"role": "assistant", "content": intro})
                        continue

        reply = get_response(text, emotion, history)
        history.append({"role": "assistant", "content": reply})
        pass

        if len(history) > 20:
            history = history[-20:]

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nClosing Aira. Take care!")