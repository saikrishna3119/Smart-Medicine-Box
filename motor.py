# ============================================================
# motor.py — DC Motor Control using lgpio (Raspberry Pi 5)
# Controls 4 × N20 motors via 2 × TB6612FNG drivers
# ============================================================

import lgpio
import time
import logging
from config import (
    MOTOR1_AIN1, MOTOR1_AIN2, MOTOR1_PWM,
    MOTOR2_BIN1, MOTOR2_BIN2, MOTOR2_PWM,
    MOTOR3_AIN1, MOTOR3_AIN2, MOTOR3_PWM,
    MOTOR4_BIN1, MOTOR4_BIN2, MOTOR4_PWM,
    DRIVER1_STBY, DRIVER2_STBY,
    MOTOR_RUN_SECONDS, MOTOR_PWM_FREQ, MOTOR_DUTY_CYCLE,
)

logger = logging.getLogger(__name__)

# GPIO chip handle (shared across module)
_chip = None


def init_gpio():
    """Open GPIO chip and configure all motor pins as outputs."""
    global _chip
    try:
        _chip = lgpio.gpiochip_open(0)  # /dev/gpiochip0 on RPi 5

        output_pins = [
            MOTOR1_AIN1, MOTOR1_AIN2, MOTOR1_PWM,
            MOTOR2_BIN1, MOTOR2_BIN2, MOTOR2_PWM,
            MOTOR3_AIN1, MOTOR3_AIN2, MOTOR3_PWM,
            MOTOR4_BIN1, MOTOR4_BIN2, MOTOR4_PWM,
            DRIVER1_STBY, DRIVER2_STBY,
        ]
        for pin in output_pins:
            lgpio.gpio_claim_output(_chip, pin, 0)

        # Keep STBY pins HIGH to enable both drivers at all times
        lgpio.gpio_write(_chip, DRIVER1_STBY, 1)
        lgpio.gpio_write(_chip, DRIVER2_STBY, 1)

        logger.info("GPIO initialised successfully.")
    except Exception as e:
        logger.error(f"GPIO init failed: {e}")
        raise


def cleanup_gpio():
    """Release GPIO resources safely."""
    global _chip
    if _chip is not None:
        try:
            # Stop all motors before releasing
            _all_motors_stop()
            lgpio.gpiochip_close(_chip)
            logger.info("GPIO cleaned up.")
        except Exception as e:
            logger.warning(f"GPIO cleanup warning: {e}")
        finally:
            _chip = None


# ── Internal helpers ─────────────────────────────────────────

def _pwm_on(pin):
    """Simulate PWM using lgpio tx_pwm (hardware PWM on supported pins)."""
    try:
        lgpio.tx_pwm(_chip, pin, MOTOR_PWM_FREQ, MOTOR_DUTY_CYCLE)
    except Exception:
        # Fallback: just drive pin HIGH if PWM not supported on that pin
        lgpio.gpio_write(_chip, pin, 1)


def _pwm_off(pin):
    """Stop PWM on pin."""
    try:
        lgpio.tx_pwm(_chip, pin, MOTOR_PWM_FREQ, 0)
    except Exception:
        lgpio.gpio_write(_chip, pin, 0)


def _run_motor(ain1, ain2, pwm_pin, duration=MOTOR_RUN_SECONDS):
    """
    Spin a motor forward for `duration` seconds, then stop.
    Forward: AIN1=HIGH, AIN2=LOW, PWM=HIGH
    """
    try:
        lgpio.gpio_write(_chip, ain1, 1)
        lgpio.gpio_write(_chip, ain2, 0)
        _pwm_on(pwm_pin)
        logger.debug(f"Motor on (AIN1={ain1}, AIN2={ain2}, PWM={pwm_pin})")

        time.sleep(duration)

        # Safety stop
        lgpio.gpio_write(_chip, ain1, 0)
        lgpio.gpio_write(_chip, ain2, 0)
        _pwm_off(pwm_pin)
        logger.debug("Motor stopped.")
    except Exception as e:
        logger.error(f"Motor run error: {e}")
        # Ensure motor is stopped even on error
        try:
            lgpio.gpio_write(_chip, ain1, 0)
            lgpio.gpio_write(_chip, ain2, 0)
            _pwm_off(pwm_pin)
        except Exception:
            pass


def _all_motors_stop():
    """Emergency stop — cut all motor signals."""
    for ain1, ain2, pwm in [
        (MOTOR1_AIN1, MOTOR1_AIN2, MOTOR1_PWM),
        (MOTOR2_BIN1, MOTOR2_BIN2, MOTOR2_PWM),
        (MOTOR3_AIN1, MOTOR3_AIN2, MOTOR3_PWM),
        (MOTOR4_BIN1, MOTOR4_BIN2, MOTOR4_PWM),
    ]:
        try:
            lgpio.gpio_write(_chip, ain1, 0)
            lgpio.gpio_write(_chip, ain2, 0)
            _pwm_off(pwm)
        except Exception:
            pass


# ── Public API ───────────────────────────────────────────────

def open_box_1():
    """Open compartment 1 (Motor 1, Driver 1)."""
    logger.info("Opening Box 1")
    _run_motor(MOTOR1_AIN1, MOTOR1_AIN2, MOTOR1_PWM)


def open_box_2():
    """Open compartment 2 (Motor 2, Driver 1)."""
    logger.info("Opening Box 2")
    _run_motor(MOTOR2_BIN1, MOTOR2_BIN2, MOTOR2_PWM)


def open_box_3():
    """Open compartment 3 (Motor 3, Driver 2)."""
    logger.info("Opening Box 3")
    _run_motor(MOTOR3_AIN1, MOTOR3_AIN2, MOTOR3_PWM)


def open_box_4():
    """Open compartment 4 (Motor 4, Driver 2)."""
    logger.info("Opening Box 4")
    _run_motor(MOTOR4_BIN1, MOTOR4_BIN2, MOTOR4_PWM)


def open_box(number: int):
    """Dispatcher: open any box by number (1–4)."""
    actions = {1: open_box_1, 2: open_box_2, 3: open_box_3, 4: open_box_4}
    if number in actions:
        actions[number]()
        return True
    logger.warning(f"Invalid box number: {number}")
    return False


def emergency_stop():
    """Safety stop — call this on any unhandled exception."""
    _all_motors_stop()
    logger.warning("Emergency stop triggered.")
