import agents
import storage


def test_crisis_detection_and_resources():
    assert agents.check_crisis("I want to die") == "crisis"
    assert "988" in agents.get_crisis_response("crisis") and "14416" in agents.get_crisis_response("crisis")
    assert agents.check_crisis("I feel hopeless and worthless") == "concern"
    assert agents.check_crisis("I had a long day") == "normal"


def test_memory_remembers_name_and_facts_per_user():
    agents.extract_facts("Hi, my name is priya. My sister lives in Hyderabad.", "u1")
    agents.extract_facts("call me Arjun", "u2")
    assert agents.load_memory("u1")["user_name"] == "Priya"
    assert any("sister" in f for f in agents.load_memory("u1")["facts"])
    assert agents.load_memory("u2")["user_name"] == "Arjun"
    assert "Priya" not in agents.get_memory_context("u2")


def test_mood_tracker_summary_and_streak():
    for emotion in ["happy", "sad", "stressed", "sad"]:
        agents.log_mood(emotion, "secret text", "u1")
    assert agents.check_consecutive_sad("u1") == 3
    assert "mostly sad" in agents.get_mood_summary("u1")


def test_privacy_no_message_text_stored_by_default():
    agents.log_mood("sad", "something very personal", "u1")
    with storage.connect() as db:
        assert db.execute("SELECT excerpt FROM moods").fetchone()["excerpt"] == ""


def test_delete_user_erases_everything():
    agents.extract_facts("my name is Priya", "u1")
    agents.log_mood("happy", "", "u1")
    assert storage.delete_user("u1") == 2
    assert agents.load_memory("u1")["user_name"] == ""


def test_wellness_offered_once_after_streak():
    assert agents.should_suggest_exercise("stressed", 2, already_offered=False)
    assert not agents.should_suggest_exercise("stressed", 2, already_offered=True)
    assert agents.get_exercise("stressed")["name"] == "Box Breathing"


def test_indian_culture_scenarios():
    assert agents.detect_indian_scenario("I really miss amma's cooking, so homesick")[0] == "homesickness"
    assert agents.detect_indian_scenario("Log kya kahenge if I say no")[0] == "family_pressure"
    assert agents.detect_indian_scenario("My H1B is stressing me")[0] == "career_pressure"
    assert agents.detect_indian_scenario("The weather is nice")[0] is None
