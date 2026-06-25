# ============================================================
# voice.py — Voice Assistant (STT + TTS + Conversation AI)
# Uses SpeechRecognition (Google API) + pyttsx3 (offline TTS)
# ============================================================

import speech_recognition as sr
import pyttsx3
import datetime
import logging
import threading

logger = logging.getLogger(__name__)

# ── TTS Engine (pyttsx3 — fully offline) ─────────────────────
_engine = None
_tts_lock = threading.Lock()   # pyttsx3 is not thread-safe


def init_voice():
    """Initialise the TTS engine. Call once at startup."""
    global _engine
    try:
        _engine = pyttsx3.init()

        # Slightly slower rate is clearer for elderly users
        _engine.setProperty("rate", 145)
        _engine.setProperty("volume", 1.0)

        # Prefer a female voice if available (friendlier for elderly)
        voices = _engine.getProperty("voices")
        for v in voices:
            if "female" in v.name.lower() or "zira" in v.id.lower():
                _engine.setProperty("voice", v.id)
                break

        logger.info("TTS engine initialised.")
    except Exception as e:
        logger.error(f"TTS init failed: {e}")
        _engine = None


def speak(text: str):
    """
    Speak `text` aloud via USB speaker.
    Thread-safe: uses a lock so overlapping calls queue up.
    """
    logger.info(f"[SPEAK] {text}")
    print(f"🔊 {text}")

    if _engine is None:
        logger.warning("TTS engine not ready — printing only.")
        return

    with _tts_lock:
        try:
            _engine.say(text)
            _engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS speak error: {e}")


# ── STT (SpeechRecognition via Google) ───────────────────────

def listen_for_command(timeout=5, phrase_limit=6) -> str:
    """
    Listen from USB mic and return recognised text (lowercase).
    Returns empty string on failure.
    """
    recogniser = sr.Recognizer()
    recogniser.energy_threshold = 300   # Adjust for room noise
    recogniser.pause_threshold  = 0.8

    try:
        with sr.Microphone() as source:
            recogniser.adjust_for_ambient_noise(source, duration=0.5)
            logger.debug("Listening...")
            audio = recogniser.listen(source, timeout=timeout,
                                      phrase_time_limit=phrase_limit)

        text = recogniser.recognize_google(audio).lower()
        logger.info(f"[HEARD] {text}")
        return text

    except sr.WaitTimeoutError:
        return ""
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        logger.error(f"Google STT request error: {e}")
        return ""
    except Exception as e:
        logger.error(f"Microphone error: {e}")
        return ""


# ── Command Parser ────────────────────────────────────────────

def parse_command(text: str) -> dict:
    """
    Parse voice command text.
    Returns dict: {"action": str, "box": int | None}

    Supported actions:
        open_box   → box = 1-4
        hello
        time
        remind
        status
        help
        unknown
    """
    if not text:
        return {"action": "unknown", "box": None}

    # Open box commands
    for i in range(1, 5):
        phrases = [
            f"open medicine {i}",
            f"open compartment {i}",
            f"open box {i}",
            f"medicine {i}",
            f"compartment {i}",
        ]
        for phrase in phrases:
            if phrase in text:
                return {"action": "open_box", "box": i}

    # Conversational commands
    if any(w in text for w in ["hello", "hi", "hey"]):
        return {"action": "hello", "box": None}

    if any(w in text for w in ["time", "what time", "clock"]):
        return {"action": "time", "box": None}

    if any(w in text for w in ["remind", "reminder", "schedule"]):
        return {"action": "remind", "box": None}

    if any(w in text for w in ["status", "how are you", "working"]):
        return {"action": "status", "box": None}

    if any(w in text for w in ["help", "what can you do", "commands"]):
        return {"action": "help", "box": None}

    return {"action": "unknown", "box": None}


def handle_conversation(action: str, schedule: dict) -> str:
    """
    Return an appropriate spoken response for non-motor commands.
    `schedule` is the dict from config.SCHEDULE.
    """
    now = datetime.datetime.now()

    if action == "hello":
        hour = now.hour
        if hour < 12:
            greeting = "Good morning"
        elif hour < 17:
            greeting = "Good afternoon"
        else:
            greeting = "Good evening"
        return (f"{greeting}! I am your smart medicine assistant. "
                "I am here to help you take your medicine on time.")

    if action == "time":
        t = now.strftime("%I:%M %p")
        return f"The current time is {t}."

    if action == "remind":
        parts = []
        for box, t in schedule.items():
            parts.append(f"Compartment {box} at {_to_12hr(t)}")
        return "Your medicine schedule is: " + ", ".join(parts) + "."

    if action == "status":
        return ("I am working perfectly. All compartments are ready. "
                "I will remind you when it is time for your medicine.")

    if action == "help":
        return ("You can say: open medicine 1, open medicine 2, "
                "open medicine 3, open medicine 4. "
                "You can also ask: what time is it, or remind me.")

    return "I am sorry, I did not understand that. Please try again."


def _to_12hr(time_str: str) -> str:
    """Convert '14:00' → '2:00 PM'."""
    try:
        t = datetime.datetime.strptime(time_str, "%H:%M")
        return t.strftime("%I:%M %p").lstrip("0")
    except Exception:
        return time_str


# ── Voice Assistant Loop ─────────────────────────────────────

def voice_assistant_loop(open_box_fn, schedule: dict, stop_event: threading.Event):
    """
    Continuous loop: listen → parse → respond / act.

    open_box_fn  : callable(box_number) that opens the motor.
    schedule     : config.SCHEDULE dict for reminder responses.
    stop_event   : threading.Event — set it to stop the loop.
    """
    speak("Smart medicine assistant is ready. How can I help you?")

    while not stop_event.is_set():
        try:
            text = listen_for_command()
            if not text:
                continue

            command = parse_command(text)
            action  = command["action"]
            box     = command["box"]

            if action == "open_box" and box:
                speak(f"Opening compartment {box}. Please get ready.")
                open_box_fn(box)

            elif action in ("hello", "time", "remind", "status", "help"):
                response = handle_conversation(action, schedule)
                speak(response)

            else:
                speak("Sorry, I did not understand. Please say: open medicine 1, 2, 3, or 4.")

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Voice loop error: {e}")
            # Don't crash — continue listening
