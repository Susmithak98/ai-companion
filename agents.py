"""Aira's helper agents: Memory, Mood Tracker, Crisis Detection, Wellness, Indian Culture.

Every agent is a small pure-Python module so it can be unit tested without a microphone or LLM.
"""
import csv
import json
import os
import random
import re
from datetime import datetime

from config import DATA_DIR, MAX_FACTS, MEMORY_FILE, MOOD_FILE


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


# ============================================================
# MEMORY AGENT
# ============================================================

def _empty_memory():
    return {"user_name": "", "facts": [], "last_seen": "", "total_conversations": 0}


def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, encoding="utf-8") as f:
                return {**_empty_memory(), **json.load(f)}
        except (json.JSONDecodeError, OSError):
            pass
    return _empty_memory()


def save_memory(memory):
    _ensure_data_dir()
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2)


def remember_fact(fact):
    memory = load_memory()
    if fact not in memory["facts"]:
        memory["facts"] = (memory["facts"] + [fact])[-MAX_FACTS:]
        save_memory(memory)


def set_user_name(name):
    memory = load_memory()
    memory["user_name"] = name
    save_memory(memory)


def update_last_seen():
    memory = load_memory()
    memory["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    memory["total_conversations"] += 1
    save_memory(memory)


def get_memory_context():
    memory = load_memory()
    parts = []
    if memory["user_name"]:
        parts.append(f"User's name is {memory['user_name']}.")
    if memory["last_seen"]:
        parts.append(f"Last seen: {memory['last_seen']}.")
    if memory["facts"]:
        parts.append("Facts: " + " ".join(memory["facts"][-5:]))
    return " ".join(parts)


NAME_PATTERN = re.compile(r"\b(?:my name is|i am called|call me)\s+([A-Za-z][A-Za-z'-]{1,30})", re.I)
FACT_TRIGGERS = ["my sister", "my brother", "my mom", "my dad", "my amma", "my nanna", "my wife",
                 "my husband", "my friend", "my boss", "i work", "i study", "i live", "my job"]


def extract_facts(text):
    """Remember the user's name and personal facts mentioned in the message."""
    match = NAME_PATTERN.search(text)
    if match:
        set_user_name(match.group(1).capitalize())
    for sentence in re.split(r"[.!?]", text):
        low = sentence.lower()
        if len(sentence.strip()) > 10 and any(t in low for t in FACT_TRIGGERS):
            remember_fact(sentence.strip())


# ============================================================
# MOOD TRACKER AGENT
# ============================================================

def log_mood(emotion, user_text=""):
    _ensure_data_dir()
    new_file = not os.path.exists(MOOD_FILE)
    with open(MOOD_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["date", "time", "emotion", "what_user_said"])
        now = datetime.now()
        writer.writerow([now.strftime("%Y-%m-%d"), now.strftime("%H:%M"), emotion, user_text[:100]])


def _read_moods():
    if not os.path.exists(MOOD_FILE):
        return []
    with open(MOOD_FILE, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def get_mood_summary():
    recent = _read_moods()[-10:]
    if not recent:
        return ""
    counts = {}
    for row in recent:
        counts[row["emotion"]] = counts.get(row["emotion"], 0) + 1
    dominant = max(counts, key=counts.get)
    return f"Recent mood: mostly {dominant} ({counts[dominant]}/{len(recent)} times)."


def check_consecutive_sad():
    count = 0
    for row in reversed(_read_moods()):
        if row["emotion"] in ("sad", "stressed", "crisis"):
            count += 1
        else:
            break
    return count


# ============================================================
# CRISIS DETECTION AGENT
# ============================================================

CRISIS_WORDS = ["kill myself", "end my life", "want to die", "cant go on", "can't go on",
                "no reason to live", "better off dead", "hurt myself", "suicide", "end it all",
                "disappear forever"]
CONCERN_WORDS = ["hopeless", "worthless", "nobody cares", "all alone", "no one loves me",
                 "hate myself", "cant take it", "can't take it", "tired of everything"]

CRISIS_RESPONSE = ("I hear you and I am really glad you are talking to me. You are not alone in this moment. "
                   "Please reach out to someone who can help right now. You can call or text 988, the Suicide "
                   "and Crisis Lifeline, available 24 hours a day. In India you can call Tele MANAS at 14416. "
                   "You matter and things can get better.")
CONCERN_RESPONSE = ("I can hear that you are going through something really hard. "
                    "Those feelings are real and valid. You do not have to face this alone. "
                    "I am here with you. Can you tell me more about what is going on?")


def check_crisis(text):
    low = text.lower()
    if any(w in low for w in CRISIS_WORDS):
        return "crisis"
    if sum(w in low for w in CONCERN_WORDS) >= 2:
        return "concern"
    return "normal"


def get_crisis_response(level):
    return {"crisis": CRISIS_RESPONSE, "concern": CONCERN_RESPONSE}.get(level)


# ============================================================
# WELLNESS AGENT
# ============================================================

EXERCISES = {
    "stressed": [{"name": "Box Breathing", "steps": [
        "Let us try a quick breathing exercise.",
        "Breathe in slowly for 4 counts. One. Two. Three. Four.",
        "Hold for 4 counts. One. Two. Three. Four.",
        "Breathe out slowly for 4 counts. One. Two. Three. Four.",
        "Hold again for 4 counts. One. Two. Three. Four.",
        "How do you feel now?"]}],
    "sad": [{"name": "Gratitude Exercise", "steps": [
        "Let us try something gentle together.",
        "Think of one person in your life you are grateful for.",
        "Now think of one small good thing that happened today.",
        "Finally think of one thing you like about yourself.",
        "Those things are real even on hard days. Well done."]}],
    "angry": [{"name": "Cool Down Breathing", "steps": [
        "Let us slow things down together.",
        "Take a deep breath in through your nose.",
        "Now breathe out slowly through your mouth.",
        "Again. Breathe in slowly. And out slowly.",
        "Good. How are you feeling now?"]}],
}
EXERCISE_INTROS = {
    "stressed": "You seem stressed. Would you like to try a quick breathing exercise? Say yes or no.",
    "sad": "I notice you are feeling sad. Would you like to try something gentle together? Say yes or no.",
    "angry": "I can hear you are frustrated. Would a breathing exercise help? Say yes or no.",
}


def should_suggest_exercise(emotion, negative_streak, already_offered):
    """Offer an exercise after two difficult messages in a row, at most once per session."""
    return emotion in EXERCISES and negative_streak >= 2 and not already_offered


def get_exercise(emotion):
    return random.choice(EXERCISES[emotion]) if emotion in EXERCISES else None


def get_exercise_intro(emotion):
    return EXERCISE_INTROS.get(emotion, "")


# ============================================================
# INDIAN CULTURAL INTELLIGENCE AGENT
# ============================================================

INDIAN_SCENARIOS = {
    "homesickness": {
        "keywords": ["miss home", "miss amma", "miss india", "homesick", "amma miss", "nanna miss",
                     "ghar yaad", "miss my family", "miss mom's food"],
        "hint": "User misses home and family. Be deeply empathetic. Ask about a specific memory of home."},
    "family_pressure": {
        "keywords": ["parents want", "family pressure", "marriage pressure", "arranged marriage",
                     "log kya kahenge", "amma cheppindi", "nanna cheppadu", "forced"],
        "hint": "User feels family pressure. Validate that Indian family pressure is real. Do not take sides."},
    "loneliness_abroad": {
        "keywords": ["no friends here", "alone in", "nobody here", "no one to talk", "foreign country",
                     "evaru ledu", "akele hoon"],
        "hint": "User is lonely abroad. Be their home away from home. Warm and present."},
    "career_pressure": {
        "keywords": ["job pressure", "visa", "h1b", "h-1b", "green card", "layoff", "fired", "job loss", "career"],
        "hint": "User faces career pressure. Acknowledge the pressure without adding to it."},
    "relationship": {
        "keywords": ["boyfriend", "girlfriend", "breakup", "love marriage", "inter caste",
                     "parents won't accept", "hiding relationship"],
        "hint": "User has relationship challenges. Be completely non-judgmental and supportive."},
    "festival": {
        "keywords": ["diwali", "holi", "pongal", "onam", "sankranti", "ugadi", "navratri", "festival"],
        "hint": "A festival is on the user's mind. Celebrate with them, or comfort them if they are away from family."},
}


def detect_indian_scenario(text):
    low = text.lower()
    for scenario, data in INDIAN_SCENARIOS.items():
        if any(k in low for k in data["keywords"]):
            return scenario, data["hint"]
    return None, None
