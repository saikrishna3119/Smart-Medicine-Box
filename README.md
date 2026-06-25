# Smart Medicine Box — Setup & Documentation
## For Blind and Elderly People | Raspberry Pi 5

---

## 📁 Project File Structure

```
smart_medicine_box/
├── main.py          ← Entry point — starts all threads
├── config.py        ← GPIO pins, timings, schedule
├── motor.py         ← DC motor control (lgpio)
├── ir_sensor.py     ← IR medicine detection
├── voice.py         ← Speech recognition + TTS
├── scheduler.py     ← Time-based reminders
├── webapp.py        ← Flask web control panel
├── requirements.txt ← Python dependencies
└── medicine_log.txt ← Auto-created: dose history log
```

---

## 🔧 Step 1: OS & System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Audio tools (for pyttsx3 + PyAudio)
sudo apt install -y espeak espeak-data libespeak-dev \
    portaudio19-dev python3-pyaudio \
    alsa-utils pulseaudio

# Verify USB speaker & mic
aplay -l      # List playback devices
arecord -l    # List recording devices

# Test speaker (you should hear a tone)
speaker-test -t wav -c 2

# Test mic recording (record 3 sec, play back)
arecord -d 3 test.wav && aplay test.wav
```

---

## 🐍 Step 2: Install Python Packages

```bash
# Navigate to project folder
cd ~/smart_medicine_box

# Install all dependencies
pip install -r requirements.txt --break-system-packages

# OR install individually:
pip install lgpio               --break-system-packages
pip install flask               --break-system-packages
pip install SpeechRecognition   --break-system-packages
pip install pyttsx3             --break-system-packages
pip install schedule            --break-system-packages
pip install PyAudio             --break-system-packages
```

---

## 🔌 Step 3: Circuit Wiring

### TB6612FNG Motor Driver Pinout

```
TB6612FNG Pin  | RPi GPIO  | Purpose
───────────────|───────────|─────────────────────────
Driver 1:
  AIN1         | GPIO 17   | Motor 1 direction A
  AIN2         | GPIO 27   | Motor 1 direction B
  PWMA         | GPIO 18   | Motor 1 speed
  BIN1         | GPIO 22   | Motor 2 direction A
  BIN2         | GPIO 24   | Motor 2 direction B
  PWMB         | GPIO 25   | Motor 2 speed
  STBY         | GPIO 23   | Driver enable (MUST be HIGH)
  VCC          | 3.3V      | Logic power
  VM           | 5V–12V    | Motor power supply
  GND          | GND       | Common ground

Driver 2:
  AIN1         | GPIO 5    | Motor 3 direction A
  AIN2         | GPIO 6    | Motor 3 direction B
  PWMA         | GPIO 12   | Motor 3 speed
  BIN1         | GPIO 13   | Motor 4 direction A
  BIN2         | GPIO 16   | Motor 4 direction B
  PWMB         | GPIO 19   | Motor 4 speed
  STBY         | GPIO 26   | Driver enable (MUST be HIGH)
  VCC          | 3.3V      | Logic power
  VM           | 5V–12V    | Motor power supply
  GND          | GND       | Common ground
```

### IR Sensor Wiring

```
IR Module Pin  | RPi GPIO  | Purpose
───────────────|───────────|─────────────────────────
  VCC          | 3.3V      | Power
  GND          | GND       | Ground
  OUT          | GPIO 21   | Digital output
                            (LOW = object detected)
```

### ⚠️ Important Wiring Notes
- Use a **separate 5V–12V power supply** for motor VM pins
- Connect all GND pins together (RPi GND + motor PSU GND)
- N20 motors typically run on 3V–6V; use appropriate VM voltage
- STBY pin MUST be connected to GPIO and driven HIGH in code

---

## ▶️ Step 4: Run the System

```bash
cd ~/smart_medicine_box
python main.py
```

You should see:
```
[INFO] GPIO initialised successfully.
[INFO] TTS engine initialised.
[INFO] Scheduled: Box 1 at 09:00
[INFO] Scheduled: Box 2 at 14:00
[INFO] Scheduled: Box 3 at 20:00
Flask server : http://0.0.0.0:5000
🔊 Smart medicine box is ready...
```

### Run on boot (systemd service):

```bash
# Create service file
sudo nano /etc/systemd/system/medicinebox.service
```

Paste:
```ini
[Unit]
Description=Smart Medicine Box
After=network.target sound.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/smart_medicine_box/main.py
WorkingDirectory=/home/pi/smart_medicine_box
Restart=on-failure
User=pi

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable medicinebox
sudo systemctl start medicinebox
sudo systemctl status medicinebox
```

---

## 🌐 Step 5: Access Web Panel

From any browser on the same Wi-Fi network:
```
http://<raspberry-pi-ip>:5000
```

Find your Pi's IP: `hostname -I`

---

## 🧪 Testing Procedure

### Test Motors Only (no other threads):
```python
# test_motors.py
from motor import init_gpio, open_box_1, open_box_2, open_box_3, open_box_4, cleanup_gpio
init_gpio()
open_box_1()   # Should spin motor 1 for 1.5 seconds
open_box_2()
open_box_3()
open_box_4()
cleanup_gpio()
```

### Test Voice Only:
```python
# test_voice.py
from voice import init_voice, speak, listen_for_command
init_voice()
speak("Testing voice output")
text = listen_for_command()
print(f"Heard: {text}")
```

### Test IR Sensor Only:
```python
# test_ir.py
import lgpio, time
from ir_sensor import set_chip, is_medicine_present
chip = lgpio.gpiochip_open(0)
set_chip(chip)
for _ in range(5):
    print("Medicine present:", is_medicine_present())
    time.sleep(1)
lgpio.gpiochip_close(chip)
```

### Test Web (from another device):
```bash
curl "http://<pi-ip>:5000/open_box?box=1"
# Expected: {"success": true, "message": "Compartment 1 opened."}

curl "http://<pi-ip>:5000/status"
# Expected: {"status": "ok", ...}
```

### Test Scheduler (advance a reminder by 1 min):
In `config.py`, temporarily change a time to 1 minute from now,
run the system, and verify the reminder fires.

---

## 🔍 Troubleshooting

| Problem | Solution |
|---|---|
| `lgpio.error: Can't open gpiochip` | Run with `sudo` or add user to `gpio` group: `sudo usermod -aG gpio $USER` |
| Motor not spinning | Check STBY pin is HIGH, check VM voltage, verify wiring |
| Motor spins wrong direction | Swap AIN1 / AIN2 connections |
| No audio output | Run `alsa-mixer`, check speaker selection: `sudo raspi-config → Audio` |
| `PyAudio` install fails | `sudo apt install portaudio19-dev` then retry |
| STT not working offline | Use `recognize_sphinx()` instead of `recognize_google()` (install `pocketsphinx`) |
| IR sensor always HIGH | Check object distance (typically 2–30 cm), adjust potentiometer on module |
| IR sensor always LOW | Check wiring, try inverting logic in `is_medicine_present()` |
| Flask port 5000 in use | Change `FLASK_PORT` in `config.py` |
| `pyttsx3` no sound | Install espeak: `sudo apt install espeak` |

---

## 📊 Medicine Log

The system auto-creates `medicine_log.txt`:
```
[2025-01-15 09:00:12] Box 1 | Morning medicine | TAKEN
[2025-01-15 14:00:08] Box 2 | Afternoon medicine | MISSED
[2025-01-15 20:00:05] Box 3 | Evening medicine | TAKEN
```

---

## 🎓 Viva / Presentation Explanation (5–6 lines)

> "This project is a smart medicine dispenser designed for blind and elderly
> people who struggle to remember or manage their medications independently.
> It uses a Raspberry Pi 5 to control four DC-motor-driven compartments,
> each holding a different dose. A built-in voice assistant lets users open
> compartments by speaking simple commands, while scheduled reminders
> automatically open the correct box at the right time each day. An IR sensor
> detects whether the medicine was actually removed, and the system escalates
> alerts if a dose is missed. A web control panel also allows caregivers to
> operate the device remotely from any phone or laptop on the same network."

---

## 🌍 Real-World Impact

- **Blind users**: voice commands and audio feedback eliminate the need to see labels
- **Elderly users**: automatic reminders prevent forgotten or doubled doses
- **Caregivers**: web panel allows remote monitoring and manual control
- **Independence**: the user does not need a caregiver physically present for every dose
- **Safety**: missed-dose escalation alerts prevent dangerous medication lapses
- **Logging**: medicine_log.txt gives doctors/family a clear compliance history

---

## 🏆 Bonus Features Included

- ✅ Logging system (`medicine_log.txt` with timestamps)
- ✅ Repeated alerts for missed doses (15-second interval checks)
- ✅ Emergency motor stop (`motor.emergency_stop()`)
- ✅ Safety: motors always stopped in `cleanup_gpio()` and `emergency_stop()`
- ✅ Graceful shutdown via Ctrl+C / SIGTERM
- ✅ Thread-safe TTS with a threading lock
- ✅ Offline TTS (pyttsx3) — works without internet
- ✅ IR sensor pull-up resistor configured in software
