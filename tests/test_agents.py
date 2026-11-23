import agents


def test_crisis_detection_and_resources():
    assert agents.check_crisis("I want to die") == "crisis"
    assert "988" in agents.get_crisis_response("crisis")
    assert agents.check_crisis("I feel hopeless and worthless") == "concern"
    assert agents.check_crisis("I had a long day") == "normal"


def test_memory_remembers_name_and_facts():
    agents.extract_facts("Hi, my name is priya. My sister lives in Hyderabad and I work at a bank.")
    memory = agents.load_memory()
    assert memory["user_name"] == "Priya"
    assert any("sister" in f for f in memory["facts"])
    assert "Priya" in agents.get_memory_context()


def test_mood_tracker_summary_and_streak():
    for emotion in ["happy", "sad", "stressed", "sad"]:
        agents.log_mood(emotion, "test")
    assert agents.check_consecutive_sad() == 3
    assert "mostly sad" in agents.get_mood_summary()


def test_wellness_offered_once_after_streak():
    assert agents.should_suggest_exercise("stressed", 2, already_offered=False)
    assert not agents.should_suggest_exercise("stressed", 2, already_offered=True)
    assert not agents.should_suggest_exercise("happy", 5, already_offered=False)
    assert agents.get_exercise("stressed")["name"] == "Box Breathing"


def test_indian_culture_scenarios():
    assert agents.detect_indian_scenario("I really miss amma's cooking, so homesick")[0] == "homesickness"
    assert agents.detect_indian_scenario("Log kya kahenge if I say no")[0] == "family_pressure"
    assert agents.detect_indian_scenario("My H1B is stressing me")[0] == "career_pressure"
    assert agents.detect_indian_scenario("The weather is nice")[0] is None
