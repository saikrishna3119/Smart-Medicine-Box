# ============================================================
# scheduler.py — Medicine Reminder Scheduler
# Uses the `schedule` library for time-based reminders
# ============================================================

import schedule
import time
import threading
import logging
import datetime
from config import SCHEDULE, MEDICINE_NAMES

logger = logging.getLogger(__name__)


def _make_reminder(box_number: int, speak_fn, open_box_fn, check_taken_fn):
    """
    Factory: returns a job function for a specific box.
    Reminder flow:
      1. Speak reminder.
      2. Open the compartment.
      3. Monitor if medicine is taken via IR sensor.
      4. Log outcome.
    """
    def reminder_job():
        name = MEDICINE_NAMES.get(box_number, f"medicine {box_number}")
        logger.info(f"Scheduled reminder triggered for box {box_number} ({name})")

        speak_fn(
            f"It is time for your {name}. "
            f"Opening compartment {box_number} now."
        )
        open_box_fn(box_number)

        # Run IR monitoring in a separate thread so scheduler stays on time
        def monitor():
            taken = check_taken_fn(speak_fn, box_number)
            _log_dose(box_number, name, taken)

        t = threading.Thread(target=monitor, daemon=True)
        t.start()

    return reminder_job


def setup_schedule(speak_fn, open_box_fn, check_taken_fn):
    """
    Register all scheduled jobs from config.SCHEDULE.
    Call once at startup before starting the scheduler loop.
    """
    schedule.clear()   # Remove any previously registered jobs

    for box_number, time_str in SCHEDULE.items():
        job_fn = _make_reminder(box_number, speak_fn, open_box_fn, check_taken_fn)
        schedule.every().day.at(time_str).do(job_fn)
        logger.info(f"Scheduled: Box {box_number} at {time_str}")
        print(f"📅 Box {box_number} reminder set for {time_str}")


def scheduler_loop(stop_event: threading.Event):
    """
    Blocking loop that runs pending jobs every second.
    Run in its own daemon thread.
    """
    logger.info("Scheduler loop started.")
    while not stop_event.is_set():
        try:
            schedule.run_pending()
            time.sleep(1)
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(5)


def _log_dose(box_number: int, medicine_name: str, taken: bool):
    """Append dose event to medicine_log.txt."""
    from config import LOG_FILE
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status    = "TAKEN" if taken else "MISSED"
    line      = f"[{timestamp}] Box {box_number} | {medicine_name} | {status}\n"

    try:
        with open(LOG_FILE, "a") as f:
            f.write(line)
        logger.info(f"Logged: {line.strip()}")
    except Exception as e:
        logger.error(f"Log write error: {e}")
