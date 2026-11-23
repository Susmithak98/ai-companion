"""Aira, your AI voice companion.

    python main.py            # voice mode: speak naturally, say "bye" to exit
    python main.py --text     # text mode: type instead of speaking (no microphone needed)
    python main.py --mute     # don't speak replies out loud
"""
import argparse
import re

import agents
from aira import get_response
from core import speaker
from core.brain import is_ollama_running
from core.emotion import detect_emotion
from config import OLLAMA_MODEL, OLLAMA_URL

EXIT_WORDS = re.compile(r"\b(goodbye|bye|exit|quit)\b", re.I)


def listen(text_mode: bool, turn: int) -> str:
    if text_mode:
        try:
            return input("\n👤 You: ").strip()
        except EOFError:
            return "bye"
    from core.listener import record_audio
    from core.transcriber import transcribe
    text = transcribe(record_audio(f"input_{turn}.wav"))
    if text:
        print(f"\n👤 You: {text}")
    return text


def main():
    parser = argparse.ArgumentParser(description="Aira, your AI voice companion")
    parser.add_argument("--text", action="store_true", help="type instead of speaking")
    parser.add_argument("--mute", action="store_true", help="do not speak replies out loud")
    args = parser.parse_args()
    speaker.enabled = not args.mute

    print("\n" + "=" * 45 + "\n   AIRA - Your AI Voice Companion\n" + "=" * 45)
    print("   Type your message and press Enter." if args.text else "   Just SPEAK. Aira listens automatically!")
    print('   Say "bye" to exit\n')

    if not is_ollama_running():
        print(f"❌ Ollama is not reachable at {OLLAMA_URL}.")
        print(f"   Start it with: ollama serve   (and once: ollama pull {OLLAMA_MODEL})")
        return

    agents.update_last_seen()
    memory = agents.load_memory()
    name = memory["user_name"]
    speaker.speak(f"Welcome back {name}. I am Aira. How are you feeling today?" if name
                  else "Hi there. I am Aira. I am here for you. Just start talking.")

    history, turn, failed = [], 0, 0
    exercise_offered = warned_low_mood = False

    while True:
        turn += 1
        text = listen(args.text, turn)
        if not text:
            failed += 1
            if failed >= 3:
                speaker.speak("I cannot hear you. Please check your microphone, or try python main.py --text.")
                failed = 0
            continue
        failed = 0

        if EXIT_WORDS.search(text):
            speaker.speak("Take care of yourself. I am always here for you. Goodbye.")
            break

        # 1. Safety first: crisis language gets a safe, human-resource response.
        level = agents.check_crisis(text)
        if level != "normal":
            reply = agents.get_crisis_response(level)
            agents.log_mood("crisis" if level == "crisis" else "sad", text)
            speaker.speak(reply)
            history += [{"role": "user", "content": text}, {"role": "assistant", "content": reply}]
            continue

        # 2. Emotion + mood tracking
        emotion = detect_emotion(text)
        agents.log_mood(emotion, text)
        streak = agents.check_consecutive_sad()
        if streak >= 5 and not warned_low_mood:
            speaker.speak("I noticed you have been feeling down a lot lately. I care about you. "
                          "Please consider talking to someone you trust.")
            warned_low_mood = True

        history.append({"role": "user", "content": text})

        # 3. Wellness agent: offer an exercise once when things are hard
        if agents.should_suggest_exercise(emotion, streak, exercise_offered):
            exercise_offered = True
            intro = agents.get_exercise_intro(emotion)
            speaker.speak(intro)
            answer = listen(args.text, turn)
            if answer and re.search(r"\b(yes|sure|ok|okay)\b", answer, re.I):
                for step in agents.get_exercise(emotion)["steps"]:
                    speaker.speak(step)
                history.append({"role": "assistant", "content": intro})
                continue

        # 4. Brain: memory + mood + culture + emotion -> streamed, spoken reply
        reply = get_response(text, emotion, history)
        history.append({"role": "assistant", "content": reply})
        history = history[-20:]


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nClosing Aira. Take care!")
