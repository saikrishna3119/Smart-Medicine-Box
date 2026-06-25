# ============================================================
# config.py — GPIO Pin Mapping & Global Configuration
# Smart Medicine Box for Blind & Elderly People
# ============================================================

# ── Driver 1 ────────────────────────────────────────────────
MOTOR1_AIN1 = 17
MOTOR1_AIN2 = 27
MOTOR1_PWM  = 18

MOTOR2_BIN1 = 22
MOTOR2_BIN2 = 24
MOTOR2_PWM  = 25

DRIVER1_STBY = 23

# ── Driver 2 ────────────────────────────────────────────────
MOTOR3_AIN1 = 5
MOTOR3_AIN2 = 6
MOTOR3_PWM  = 12

MOTOR4_BIN1 = 13
MOTOR4_BIN2 = 16
MOTOR4_PWM  = 19

DRIVER2_STBY = 26

# ── IR Sensor ───────────────────────────────────────────────
IR_SENSOR_PIN = 21

# ── Motor Settings ───────────────────────────────────────────
MOTOR_RUN_SECONDS  = 1.5   # How long each motor spins to open box
MOTOR_PWM_FREQ     = 1000  # PWM frequency in Hz
MOTOR_DUTY_CYCLE   = 100   # Duty cycle 0–100 (full speed)

# ── Reminder Settings ────────────────────────────────────────
MEDICINE_TAKEN_WAIT   = 10   # Seconds to wait before checking IR
MISSED_DOSE_ALERT_SEC = 120  # Seconds before escalated alert

# ── Medicine Schedule (24-hr format HH:MM) ───────────────────
SCHEDULE = {
    1: "09:00",   # Morning dose  → Compartment 1
    2: "14:00",   # Afternoon dose → Compartment 2
    3: "20:00",   # Evening dose  → Compartment 3
}

# ── Medicine Names (customisable) ────────────────────────────
MEDICINE_NAMES = {
    1: "Morning medicine",
    2: "Afternoon medicine",
    3: "Evening medicine",
    4: "Extra medicine",
}

# ── Flask Web Server ─────────────────────────────────────────
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000

# ── Logging ──────────────────────────────────────────────────
LOG_FILE = "medicine_log.txt"
