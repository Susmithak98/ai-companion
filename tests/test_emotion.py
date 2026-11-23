from core.emotion import detect_emotion


def test_keyword_emotions():
    assert detect_emotion("I am so stressed about this deadline") == "stressed"
    assert detect_emotion("I feel lonely and sad today") == "sad"
    assert detect_emotion("I got the job, I'm so happy!") == "happy"
    assert detect_emotion("This is so unfair, I'm fed up") == "angry"


def test_whole_word_matching():
    # "made" must not be read as "mad", "goodbye" must not be read as "good"
    assert detect_emotion("I made dinner") != "angry"
    assert detect_emotion("") == "neutral"
