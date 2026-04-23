# agents.py
# All agents in one file: Memory, Mood Tracker, Crisis, Wellness, Indian Culture

import json
import os
import csv
import random
from datetime import datetime

# ============================================================
# MEMORY AGENT
# ============================================================

MEMORY_FILE = "aira_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {
        "user_name": "",
        "facts": [],
        "last_seen": "",
        "total_conversations": 0
    }

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def remember_fact(fact):
    memory = load_memory()
    if fact not in memory["facts"]:
        memory["facts"].append(fact)
        memory["facts"] = memory["facts"][-20:]
        save_memory(memory)
        print(f"🧠 Remembered: {fact}")

def update_last_seen():
    memory = load_memory()
    memory["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    memory["total_conversations"] += 1
    save_memory(memory)

def set_user_name(name):
    memory = load_memory()
    memory["user_name"] = name
    save_memory(memory)
    print(f"🧠 Remembered name: {name}")

def get_memory_context():
    memory = load_memory()
    context = ""
    if memory["user_name"]:
        context += f"User's name is {memory['user_name']}. "
    if memory["last_seen"]:
        context += f"Last seen: {memory['last_seen']}. "
    if memory["facts"]:
        context += f"Facts: {' '.join(memory['facts'][-5:])}"
    return context

def extract_facts(text):
    text_lower = text.lower()
    name_triggers = ["my name is", "i am called", "call me"]
    for trigger in name_triggers:
        if trigger in text_lower:
            parts = text_lower.split(trigger)
            if len(parts) > 1:
                name = parts[1].strip().split()[0].capitalize()
                set_user_name(name)
    fact_triggers = [
        "my sister", "my brother", "my mom", "my dad",
        "my wife", "my husband", "my friend", "my boss",
        "i work", "i study", "i live", "my job"
    ]
    for trigger in fact_triggers:
        if trigger in text_lower:
            sentences = text.split(".")
            for sentence in sentences:
                if trigger in sentence.lower() and len(sentence) > 10:
                    remember_fact(sentence.strip())


# ============================================================
# MOOD TRACKER AGENT
# ============================================================

MOOD_FILE = "aira_moods.csv"

def log_mood(emotion, user_text=""):
    file_exists = os.path.exists(MOOD_FILE)
    with open(MOOD_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["date", "time", "emotion", "what_user_said"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d"),
            datetime.now().strftime("%H:%M"),
            emotion,
            user_text[:100]
        ])

def get_mood_summary():
    if not os.path.exists(MOOD_FILE):
        return ""
    moods = []
    with open(MOOD_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            moods.append(row)
    if not moods:
        return ""
    emotion_counts = {}
    for entry in moods[-10:]:
        emotion = entry["emotion"]
        emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
    if emotion_counts:
        dominant = max(emotion_counts, key=emotion_counts.get)
        total = sum(emotion_counts.values())
        return f"Recent mood: mostly {dominant} ({emotion_counts[dominant]}/{total} times)."
    return ""

def check_consecutive_sad():
    if not os.path.exists(MOOD_FILE):
        return 0
    moods = []
    with open(MOOD_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            moods.append(row)
    count = 0
    for entry in reversed(moods):
        if entry["emotion"] in ["sad", "stressed"]:
            count += 1
        else:
            break
    return count


# ============================================================
# CRISIS DETECTION AGENT
# ============================================================

CRISIS_WORDS = [
    "kill myself", "end my life", "want to die",
    "cant go on", "can't go on", "no reason to live",
    "better off dead", "hurt myself", "suicide",
    "end it all", "disappear forever"
]

CONCERN_WORDS = [
    "hopeless", "worthless", "nobody cares",
    "all alone", "no one loves me", "hate myself",
    "cant take it", "can't take it", "tired of everything"
]

CRISIS_RESPONSE = """I hear you and I am really glad you are talking to me.
You are not alone in this moment.
Please reach out to someone who can help right now.
You can call or text 988 which is the Suicide and Crisis Lifeline available 24 hours a day.
You matter and things can get better."""

CONCERN_RESPONSE = """I can hear that you are going through something really hard.
Those feelings are real and valid.
You do not have to face this alone.
I am here with you. Can you tell me more about what is going on?"""

def check_crisis(text):
    text_lower = text.lower()
    for word in CRISIS_WORDS:
        if word in text_lower:
            print("🚨 Crisis detected")
            return "crisis"
    concern_count = sum(1 for word in CONCERN_WORDS if word in text_lower)
    if concern_count >= 2:
        print("⚠️  Concern detected")
        return "concern"
    return "normal"

def get_crisis_response(level):
    if level == "crisis":
        return CRISIS_RESPONSE
    elif level == "concern":
        return CONCERN_RESPONSE
    return None


# ============================================================
# WELLNESS AGENT
# ============================================================

EXERCISES = {
    "stressed": [
        {
            "name": "Box Breathing",
            "steps": [
                "Let us try a quick breathing exercise.",
                "Breathe in slowly for 4 counts. One. Two. Three. Four.",
                "Hold for 4 counts. One. Two. Three. Four.",
                "Breathe out slowly for 4 counts. One. Two. Three. Four.",
                "Hold again for 4 counts. One. Two. Three. Four.",
                "How do you feel now?"
            ]
        }
    ],
    "sad": [
        {
            "name": "Gratitude Exercise",
            "steps": [
                "Let us try something gentle together.",
                "Think of one person in your life you are grateful for.",
                "Now think of one small good thing that happened today.",
                "Finally think of one thing you like about yourself.",
                "Those things are real even on hard days. Well done."
            ]
        }
    ],
    "angry": [
        {
            "name": "Cool Down Breathing",
            "steps": [
                "Let us slow things down together.",
                "Take a deep breath in through your nose.",
                "Now breathe out slowly through your mouth.",
                "Again. Breathe in slowly. And out slowly.",
                "Good. How are you feeling now?"
            ]
        }
    ]
}

def should_suggest_exercise(emotion, turn):
    return emotion in ["stressed", "sad", "angry"] and turn % 4 == 0

def get_exercise(emotion):
    if emotion in EXERCISES:
        return random.choice(EXERCISES[emotion])
    return None

def get_exercise_intro(emotion):
    intros = {
        "stressed": "You seem stressed. Would you like to try a quick breathing exercise? Say yes or no.",
        "sad": "I notice you are feeling sad. Would you like to try something gentle together? Say yes or no.",
        "angry": "I can hear you are frustrated. Would a breathing exercise help? Say yes or no."
    }
    return intros.get(emotion, "")


# ============================================================
# INDIAN CULTURAL INTELLIGENCE
# ============================================================

INDIAN_SCENARIOS = {
    "homesickness": {
        "keywords": ["miss home", "miss amma", "miss india", "homesick",
                     "amma miss", "nanna miss", "ghar yaad"],
        "hint": "User misses home and family. Be deeply empathetic. Ask about a specific memory of home."
    },
    "family_pressure": {
        "keywords": ["parents want", "family pressure", "marriage pressure",
                     "arranged marriage", "log kya kahenge", "amma cheppindi",
                     "nanna cheppadu", "forced"],
        "hint": "User feels family pressure. Validate that Indian family pressure is real. Do not take sides."
    },
    "loneliness_abroad": {
        "keywords": ["no friends here", "alone in", "nobody here",
                     "no one to talk", "foreign country", "evaru ledu",
                     "akele hoon"],
        "hint": "User is lonely abroad. Be their home away from home. Warm and present."
    },
    "career_pressure": {
        "keywords": ["job pressure", "visa", "h1b", "green card",
                     "layoff", "fired", "job loss", "career"],
        "hint": "User faces career pressure. Acknowledge the pressure without adding to it."
    },
    "relationship": {
        "keywords": ["boyfriend", "girlfriend", "breakup", "love marriage",
                     "inter caste", "parents won't accept", "hiding relationship"],
        "hint": "User has relationship challenges. Be completely non-judgmental and supportive."
    }
}

def detect_indian_scenario(text):
    text_lower = text.lower()
    for scenario, data in INDIAN_SCENARIOS.items():
        if any(keyword in text_lower for keyword in data["keywords"]):
            print(f"🇮🇳 Indian scenario: {scenario}")
            return scenario, data["hint"]
    return None, None