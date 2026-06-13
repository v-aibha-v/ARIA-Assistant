"""
Spirit Voice Assistant - Assistant Thread
Handles wake-word detection, speech recognition (Sarvam AI), and TTS (Sarvam AI).
Runs in a QThread to keep the UI responsive.
"""

import io
import os
import base64
import time
import traceback
import tempfile
import wave

import speech_recognition as sr
import sounddevice as sd
import soundfile as sf
import sys
from dotenv import load_dotenv
from sarvamai import SarvamAI
from PyQt6.QtCore import QThread, pyqtSignal
from core.skills import parse_and_execute

# Robustly find .env file
if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(__file__))
    base_path = os.path.dirname(base_path)  # Go up one level from core/

# Load .env from install dir first, then from writable APPDATA fallback
_appdata_dir = os.path.join(os.environ.get('APPDATA', base_path), 'Spirit')
load_dotenv(os.path.join(base_path, '.env'))        # install dir (may be read-only)
load_dotenv(os.path.join(_appdata_dir, '.env'))      # user-writable override

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
if not SARVAM_API_KEY:
    # Create a template .env in the writable APPDATA location
    os.makedirs(_appdata_dir, exist_ok=True)
    env_path = os.path.join(_appdata_dir, '.env')
    if not os.path.exists(env_path):
        try:
            with open(env_path, 'w') as f:
                f.write("SARVAM_API_KEY=your_key_here\n")
        except Exception:
            pass
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0,
            f"Sarvam AI API key not found.\n\n"
            f"Please edit the .env file at:\n{env_path}\n\n"
            f"Replace 'your_key_here' with your API key from sarvam.ai",
            "Spirit \u2013 Configuration Required",
            0x00000010 | 0x00001000,  # MB_ICONERROR | MB_SYSTEMMODAL
        )
    except Exception:
        pass
    print(f"[Spirit] SARVAM_API_KEY not set. Edit: {env_path}")
    sys.exit(1)


class AssistantThread(QThread):
    """
    Background thread that continuously listens for the wake word "Spirit",
    then listens for a command and executes it.
    """
    # UI state updates (only updates sphere visuals, does NOT show/hide overlay)
    state_changed  = pyqtSignal(str)
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    # Explicit overlay control — only these should show/hide the overlay
    overlay_show   = pyqtSignal()
    overlay_hide   = pyqtSignal()
    overlay_pause  = pyqtSignal()   # temporarily lower overlay (for UI automation)
    overlay_resume = pyqtSignal()   # restore overlay on top

    # Push-to-talk trigger
    push_to_talk   = pyqtSignal()

    WAKE_WORD = "spirit"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = True
        self._ptt_requested = False

        # Sarvam AI client
        self._sarvam = SarvamAI(api_subscription_key=SARVAM_API_KEY)

        # SpeechRecognition is still used for microphone capture only
        try:
            self.recognizer = sr.Recognizer()
            self.recognizer.energy_threshold = 300
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.pause_threshold = 0.8
        except Exception as e:
            print(f"[Spirit] Recognizer init error: {e}")
            self.recognizer = None

        self.push_to_talk.connect(self._on_ptt)

    def _on_ptt(self):
        self._ptt_requested = True

    # ── TTS (Sarvam AI bulbul:v3) ─────────────────────────────────────────
    def _speak(self, text: str):
        print(f"[Spirit] Speaking: {text}")
        self.state_changed.emit("speaking")
        self.response_ready.emit(text)
        try:
            response = self._sarvam.text_to_speech.convert(
                target_language_code="en-IN",
                text=text,
                model="bulbul:v3",
                speaker="aayan",
            )
            # response.audios[0] is a base64-encoded WAV
            audio_bytes = base64.b64decode(response.audios[0])
            # Play via sounddevice
            buf = io.BytesIO(audio_bytes)
            data, samplerate = sf.read(buf, dtype="float32")
            sd.play(data, samplerate)
            sd.wait()
        except Exception as e:
            print(f"[Spirit] TTS error: {e}")
            traceback.print_exc()

    # ── STT (Sarvam AI saaras:v3) ─────────────────────────────────────────
    def _listen(self, timeout=5, phrase_limit=8):
        """Capture audio from mic, transcribe via Sarvam saaras:v3, return text or None."""
        if self.recognizer is None:
            self.error_occurred.emit("Speech recognizer not available")
            return None
        try:
            with sr.Microphone(sample_rate=16000) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                try:
                    audio = self.recognizer.listen(
                        source, timeout=timeout, phrase_time_limit=phrase_limit
                    )
                except sr.WaitTimeoutError:
                    return None
        except OSError as e:
            self.error_occurred.emit(f"Microphone error: {e}")
            print(f"[Spirit] Microphone error: {e}")
            return None
        except Exception as e:
            self.error_occurred.emit(f"Audio error: {e}")
            print(f"[Spirit] Audio error: {e}")
            traceback.print_exc()
            return None

        # Write captured audio to a temp WAV file and send to Sarvam STT
        try:
            wav_bytes = audio.get_wav_data(convert_rate=16000)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(wav_bytes)
                tmp_path = tmp.name

            with open(tmp_path, "rb") as f:
                result = self._sarvam.speech_to_text.transcribe(
                    file=f,
                    model="saaras:v3",
                    mode="transcribe",
                    language_code="en-IN",
                )
            os.unlink(tmp_path)

            text = result.transcript.strip()
            print(f"[Spirit] Heard: {text}")
            return text.lower() if text else None

        except Exception as e:
            print(f"[Spirit] STT error: {e}")
            traceback.print_exc()
            return None

    # ── Main Loop ────────────────────────────────────────────────────────
    def run(self):
        print("[Spirit] Assistant thread started.")
        self._speak("Spirit is ready.")

        while self._running:
            try:
                # ── Check push-to-talk ────────────────────
                if self._ptt_requested:
                    self._ptt_requested = False
                    print("[Spirit] Push-to-talk activated.")
                    self.overlay_show.emit()
                    self.state_changed.emit("listening")
                    self._handle_command()
                    self._dismiss_after_done()
                    continue

                # ── Passive wake-word listening (NO overlay) ──
                text = self._listen(timeout=3, phrase_limit=6)
                if text is None:
                    continue
                if self.WAKE_WORD not in text:
                    continue

                # ── Wake word detected! ───────────────────
                print(f"[Spirit] Wake word detected in: '{text}'")
                self.overlay_show.emit()
                self.state_changed.emit("listening")

                after_wake = text.split(self.WAKE_WORD, 1)[1].strip()
                if after_wake:
                    print(f"[Spirit] Inline command: '{after_wake}'")
                    self._execute_command(after_wake)
                else:
                    self._handle_command()

                self._dismiss_after_done()

            except Exception as e:
                print(f"[Spirit] Loop error: {e}")
                traceback.print_exc()
                self.error_occurred.emit(str(e))
                time.sleep(1)

    def _handle_command(self):
        self._speak("Yes?")
        self.state_changed.emit("listening")
        command = self._listen(timeout=6, phrase_limit=10)
        if command is None:
            self._speak("I didn't catch that.")
            return
        print(f"[Spirit] Command received: '{command}'")
        self._execute_command(command)

    def _execute_command(self, command: str):
        self.state_changed.emit("processing")
        print(f"[Spirit] Executing command: '{command}'")
        try:
            response = parse_and_execute(
                command,
                speak_callback=lambda msg: self._speak(msg),
                pause_fn=lambda: self.overlay_pause.emit(),
                resume_fn=lambda: self.overlay_resume.emit(),
            )
            print(f"[Spirit] Command result: '{response}'")
        except Exception as e:
            response = f"Something went wrong: {e}"
            traceback.print_exc()
        self._speak(response)

    def _dismiss_after_done(self):
        """Signal to hide the overlay after a brief pause."""
        self.state_changed.emit("idle")
        time.sleep(2)
        self.overlay_hide.emit()

    def stop(self):
        self._running = False
        self.quit()
        self.wait(3000)
