"""Aira command-line companion.

    aira                # voice mode: speak naturally, say "bye" to exit
    aira --text         # type instead of speaking (no microphone needed)
    aira --mute         # don't speak replies out loud
"""
import argparse
import logging
import re

from config import OLLAMA_MODEL, OLLAMA_URL
from core import speaker
from core.brain import is_ollama_running
from core.pipeline import Session, greeting, respond
from logging_setup import setup_logging

YES = re.compile(r"\b(yes|sure|ok|okay|haan)\b", re.I)


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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="aira", description="Aira, your AI voice companion")
    parser.add_argument("--text", action="store_true", help="type instead of speaking")
    parser.add_argument("--mute", action="store_true", help="do not speak replies out loud")
    args = parser.parse_args(argv)
    setup_logging()
    logging.getLogger().setLevel(logging.ERROR)  # keep the console clean for conversation
    speaker.enabled = not args.mute

    print("\n" + "=" * 45 + "\n   AIRA - Your AI Voice Companion\n" + "=" * 45)
    print("   Type your message and press Enter." if args.text else "   Just SPEAK. Aira listens automatically!")
    print('   Say "bye" to exit\n')

    if not is_ollama_running():
        print(f"❌ Ollama is not reachable at {OLLAMA_URL}.")
        print(f"   Start it with: ollama serve   (and once: ollama pull {OLLAMA_MODEL})")
        return 1

    session = Session()
    speaker.speak(greeting(session.user_id))
    turn = failed = 0
    while True:
        turn += 1
        text = listen(args.text, turn)
        if not text:
            failed += 1
            if failed >= 3:
                speaker.speak("I cannot hear you. Please check your microphone, or try aira --text.")
                failed = 0
            continue
        failed = 0

        print("\nAira: ", end="", flush=True)
        result = respond(session, text, on_sentence=lambda s: (print(s, end=" ", flush=True),
                                                               speaker.speak(s, show=False)))
        if result.crisis_level != "normal" or result.ended:
            print(result.reply)                      # these replies are fixed text, not streamed
            speaker.speak(result.reply, show=False)
        else:
            print()
        if result.ended:
            return 0
        if result.low_mood_note:
            speaker.speak(result.low_mood_note)
        if result.exercise:
            speaker.speak(result.exercise["intro"])
            if YES.search(listen(args.text, turn) or ""):
                for step in result.exercise["steps"]:
                    speaker.speak(step)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n\nClosing Aira. Take care!")
