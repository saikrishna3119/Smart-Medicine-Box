# ============================================================
# main.py — Smart Medicine Box — System Entry Point
# Raspberry Pi 5 | lgpio | Flask | pyttsx3 | schedule
# ============================================================

import threading
import logging
import signal
import sys

from config   import SCHEDULE, FLASK_HOST, FLASK_PORT
import motor
import ir_sensor
import voice
import scheduler
import webapp

# ── Logging Setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("system.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)

# ── Shared Stop Event (signals all threads to exit) ───────────
stop_event = threading.Event()


def shutdown(signum=None, frame=None):
    """Graceful shutdown on Ctrl+C or SIGTERM."""
    logger.info("Shutdown signal received...")
    stop_event.set()
    motor.emergency_stop()
    motor.cleanup_gpio()
    voice.speak("Shutting down. Goodbye!")
    logger.info("System shut down cleanly.")
    sys.exit(0)


# Register OS signals
signal.signal(signal.SIGINT,  shutdown)
signal.signal(signal.SIGTERM, shutdown)


# ── Wrapper: open box + voice feedback ───────────────────────

def open_box_with_voice(box_number: int):
    """Open a compartment and confirm verbally."""
    success = motor.open_box(box_number)
    if not success:
        voice.speak(f"Sorry, compartment {box_number} is not available.")


# ── Wrapper: IR monitoring (passed to scheduler) ─────────────

def monitor_medicine(speak_fn, box_number: int) -> bool:
    return ir_sensor.wait_for_medicine_taken(speak_fn, box_number)


# ── Main ─────────────────────────────────────────────────────

def main():
    logger.info("=" * 50)
    logger.info("  Smart Medicine Box — Starting Up")
    logger.info("=" * 50)

    # 1. Initialise GPIO (motors + IR sensor)
    try:
        motor.init_gpio()
        ir_sensor.set_chip(motor._chip)   # Share the same chip handle
    except Exception as e:
        logger.critical(f"GPIO init failed: {e}")
        print("❌ GPIO init failed. Check wiring and lgpio installation.")
        sys.exit(1)

    # 2. Initialise TTS engine
    voice.init_voice()

    # 3. Register scheduled reminders
    scheduler.setup_schedule(
        speak_fn      = voice.speak,
        open_box_fn   = open_box_with_voice,
        check_taken_fn= monitor_medicine,
    )

    # 4. Inject dependencies into web app
    webapp.init_webapp(
        open_box_fn = open_box_with_voice,
        speak_fn    = voice.speak,
    )

    # ── Start background threads ──────────────────────────────

    # Thread 1: Flask web server
    web_thread = threading.Thread(
        target=webapp.run_webapp,
        args=(FLASK_HOST, FLASK_PORT),
        daemon=True,
        name="WebServer",
    )

    # Thread 2: Medicine scheduler
    scheduler_thread = threading.Thread(
        target=scheduler.scheduler_loop,
        args=(stop_event,),
        daemon=True,
        name="Scheduler",
    )

    # Thread 3: Voice assistant (runs in main loop below,
    #            but we use a thread so it doesn't block)
    voice_thread = threading.Thread(
        target=voice.voice_assistant_loop,
        args=(open_box_with_voice, SCHEDULE, stop_event),
        daemon=True,
        name="VoiceAssistant",
    )

    web_thread.start()
    scheduler_thread.start()
    voice_thread.start()

    logger.info(f"Flask server  : http://{FLASK_HOST}:{FLASK_PORT}")
    logger.info("Voice assistant: listening...")
    logger.info("Scheduler      : running...")
    logger.info("Press Ctrl+C to stop.")

    voice.speak(
        "Smart medicine box is ready. "
        f"Open the web panel on port {FLASK_PORT} or speak a command."
    )

    # Keep main thread alive — wait for stop event
    try:
        stop_event.wait()
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
