# ============================================================
# ir_sensor.py — IR Sensor: Detect if Medicine Was Taken
# ============================================================

import lgpio
import time
import logging
from config import IR_SENSOR_PIN, MEDICINE_TAKEN_WAIT, MISSED_DOSE_ALERT_SEC

logger = logging.getLogger(__name__)

_chip = None   # Shared chip handle injected from main.py


def set_chip(chip_handle):
    """Inject the shared lgpio chip handle from main/motor module."""
    global _chip
    _chip = chip_handle
    lgpio.gpio_claim_input(_chip, IR_SENSOR_PIN, lgpio.SET_PULL_UP)
    logger.info(f"IR sensor initialised on GPIO {IR_SENSOR_PIN}")


def is_medicine_present() -> bool:
    """
    Read IR sensor.
    Most IR modules: LOW = object detected (medicine present).
    Returns True if medicine is present in the tray.
    """
    if _chip is None:
        logger.error("IR chip handle not set. Call set_chip() first.")
        return False
    try:
        value = lgpio.gpio_read(_chip, IR_SENSOR_PIN)
        # LOW (0) = medicine blocking IR beam → present
        return value == 0
    except Exception as e:
        logger.error(f"IR sensor read error: {e}")
        return False


def wait_for_medicine_taken(speak_fn, box_number: int) -> bool:
    """
    After opening a compartment:
      1. Wait MEDICINE_TAKEN_WAIT seconds.
      2. Check IR sensor.
      3. If medicine still present → remind again.
      4. After MISSED_DOSE_ALERT_SEC total → escalated alert.

    `speak_fn` — callable that speaks a message (from voice.py).
    Returns True if medicine was taken, False if missed.
    """
    logger.info(f"Monitoring IR sensor for box {box_number}...")
    start = time.time()

    # First check after initial wait
    time.sleep(MEDICINE_TAKEN_WAIT)

    if not is_medicine_present():
        speak_fn("Medicine taken. Well done! Stay healthy.")
        logger.info(f"Box {box_number}: medicine taken on first check.")
        return True

    # Medicine still in tray — remind
    speak_fn(
        f"Medicine not taken. Please take your {_ordinal(box_number)} medicine now."
    )
    logger.warning(f"Box {box_number}: medicine not taken after {MEDICINE_TAKEN_WAIT}s.")

    # Keep checking until MISSED_DOSE_ALERT_SEC elapses
    while time.time() - start < MISSED_DOSE_ALERT_SEC:
        time.sleep(15)
        if not is_medicine_present():
            speak_fn("Thank you for taking your medicine.")
            logger.info(f"Box {box_number}: medicine taken during monitoring.")
            return True
        speak_fn("Reminder: please take your medicine.")

    # Escalated alert
    speak_fn(
        "Alert! You have missed your medicine dose. "
        "Please consult your caregiver or family member."
    )
    logger.error(f"Box {box_number}: MISSED DOSE — escalated alert sent.")
    return False


def _ordinal(n):
    suffixes = {1: "first", 2: "second", 3: "third", 4: "fourth"}
    return suffixes.get(n, str(n))
