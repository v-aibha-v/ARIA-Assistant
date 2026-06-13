"""
Spirit Voice Assistant - Skills / Command Execution
Handles opening apps, system control, timers and alarms.
"""

import os
import re
import shutil
import subprocess
import ctypes
import threading
import time
import winsound


# ── App Launcher ───────────────────────────────────────────────────────────────
APP_MAP = {
    "vscode":       "code",
    "vs code":      "code",
    "visual studio code": "code",
    "opera":        "opera",
    "opera browser": "opera",
    "chrome":       "chrome",
    "google chrome": "chrome",
    "notepad":      "notepad",
    "calculator":   "calc",
    "file explorer": "explorer",
    "explorer":     "explorer",
    "task manager":  "taskmgr",
    "command prompt": "cmd",
    "terminal":      "wt",
    "spotify":       "spotify",
    "discord":       "discord",
}


def open_app(app_name: str) -> str:
    key = app_name.lower().strip()
    cmd = APP_MAP.get(key, key)

    # Try resolving via PATH first (works for most apps)
    resolved = shutil.which(cmd)
    if resolved:
        try:
            subprocess.Popen([resolved])
            return f"Opening {app_name}"
        except Exception:
            pass

    # Try shell launch (handles built-in commands like 'calc')
    try:
        subprocess.Popen(cmd, shell=True)
        return f"Opening {app_name}"
    except Exception:
        pass

    # Last resort — os.startfile (handles registered protocols & Start Menu apps)
    try:
        os.startfile(cmd)
        return f"Opening {app_name}"
    except OSError:
        return f"Sorry, I don't know how to open {app_name}"


# ── System Control ─────────────────────────────────────────────────────────────

def lock_screen() -> str:
    ctypes.windll.user32.LockWorkStation()
    return "Locking the screen"


def shutdown_pc(delay: int = 5) -> str:
    os.system(f"shutdown /s /t {delay}")
    return f"Shutting down in {delay} seconds"


def restart_pc(delay: int = 5) -> str:
    os.system(f"shutdown /r /t {delay}")
    return f"Restarting in {delay} seconds"


def cancel_shutdown() -> str:
    os.system("shutdown /a")
    return "Shutdown cancelled"


def sleep_pc() -> str:
    os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    return "Going to sleep"


# ── Timer ──────────────────────────────────────────────────────────────────────


def _timer_alert(label: str):
    """
    Alert the user when a timer fires.
    Uses Windows MessageBox (always visible) + a beep.
    The speak_callback approach was unreliable from a foreign thread,
    so we use a blocking OS dialog instead.
    """
    try:
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        pass
    # Non-blocking Windows balloon / message box
    try:
        ctypes.windll.user32.MessageBoxW(
            0,
            f"⏰  {label}",
            "Spirit – Timer",
            0x00000040 | 0x00001000,  # MB_ICONINFORMATION | MB_SYSTEMMODAL
        )
    except Exception:
        print(f"[Spirit Timer] {label}")


def set_timer(seconds: int, callback=None, pause_fn=None, resume_fn=None) -> str:
    """
    Open Windows Clock, create a timer with the given duration, and start it.
    Runs in a background thread so Spirit responds immediately.
    pause_fn/resume_fn: called before/after automation to lower the overlay.
    """
    hours, remainder = divmod(seconds, 3600)
    mins, secs_rem = divmod(remainder, 60)
    label = _fmt_duration(seconds)

    def _automate():
        try:
            from pywinauto import Application, mouse
            from pywinauto.keyboard import send_keys

            # Step aside so Clock can receive clicks
            if pause_fn:
                pause_fn()
            time.sleep(0.3)

            # Kill any stale Clock instance so we start fresh on Timer tab
            subprocess.run(
                "taskkill /f /im Microsoft.WindowsAlarms.exe",
                shell=True, capture_output=True
            )
            time.sleep(1)

            # Launch Clock
            subprocess.Popen("explorer.exe ms-clock:", shell=True)
            time.sleep(4)

            app = Application(backend="uia").connect(title_re=".*Clock.*", timeout=10)
            win = app.top_window()
            win.set_focus()
            time.sleep(0.5)

            # Navigate to Timer tab explicitly
            try:
                timer_tab = win.child_window(auto_id="TimerButton", control_type="ListItem")
                r = timer_tab.rectangle()
                mouse.click(coords=((r.left + r.right) // 2, (r.top + r.bottom) // 2))
                time.sleep(1)
            except Exception as e:
                print(f"[Spirit Timer] Timer tab click failed (may already be on it): {e}")

            # Click "Add new timer"
            add_btn = win.child_window(auto_id="AddTimerButton", control_type="Button")
            r = add_btn.rectangle()
            mouse.click(coords=((r.left + r.right) // 2, (r.top + r.bottom) // 2))
            time.sleep(2)
            win.set_focus()

            # Set hours / minutes / seconds via spinner arrow keys
            picker = win.child_window(auto_id="DurationPicker")
            spinners = picker.children()   # [hours, minutes, seconds]

            def _set_spinner(spinner, value):
                if value == 0:
                    return
                r2 = spinner.rectangle()
                mouse.click(coords=((r2.left + r2.right) // 2, (r2.top + r2.bottom) // 2))
                time.sleep(0.2)
                for _ in range(value):
                    send_keys("{UP}")
                    time.sleep(0.05)

            _set_spinner(spinners[0], hours)
            _set_spinner(spinners[1], mins)
            _set_spinner(spinners[2], secs_rem)

            # Click Save
            save_btn = win.child_window(auto_id="PrimaryButton", control_type="Button")
            r = save_btn.rectangle()
            mouse.click(coords=((r.left + r.right) // 2, (r.top + r.bottom) // 2))
            time.sleep(2)
            win.set_focus()

            # Click Start — use found_index=0 (newest timer is always first in list)
            start_btn = win.child_window(
                auto_id="TimerPlayPauseButton", control_type="Button", found_index=0
            )
            r = start_btn.rectangle()
            mouse.click(coords=((r.left + r.right) // 2, (r.top + r.bottom) // 2))
            print(f"[Spirit Timer] Started {label} timer in Windows Clock.")

        except ImportError:
            print("[Spirit Timer] pywinauto not installed.")
        except Exception as e:
            print(f"[Spirit Timer] Automation error: {e}")
            import traceback; traceback.print_exc()
        finally:
            # Always restore overlay on top
            if resume_fn:
                resume_fn()

    threading.Thread(target=_automate, daemon=True).start()
    return f"Timer set for {label}"






def _fmt_duration(seconds: int) -> str:
    mins, secs = divmod(seconds, 60)
    parts = []
    if mins:
        parts.append(f"{mins} minute{'s' if mins > 1 else ''}")
    if secs:
        parts.append(f"{secs} second{'s' if secs != 1 else ''}")
    return " and ".join(parts) if parts else "0 seconds"


# ── Alarm ──────────────────────────────────────────────────────────────────────

def set_alarm(hour: int, minute: int, callback=None) -> str:
    def _alarm_loop():
        while True:
            now = time.localtime()
            if now.tm_hour == hour and now.tm_min == minute:
                label = f"Alarm! It's {hour:02d}:{minute:02d}!"
                print(f"[Spirit Alarm] {label}")
                _timer_alert(label)
                if callback:
                    try:
                        callback(label)
                    except Exception:
                        pass
                break
            time.sleep(10)

    t = threading.Thread(target=_alarm_loop, daemon=True)
    t.start()
    return f"Alarm set for {hour:02d}:{minute:02d}"


# ── Volume ─────────────────────────────────────────────────────────────────────

def mute_volume() -> str:
    os.system('powershell -c "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"')
    return "Volume muted"


# ── Command Parser ─────────────────────────────────────────────────────────────

def parse_and_execute(command: str, speak_callback=None, pause_fn=None, resume_fn=None) -> str:
    cmd = command.lower().strip()
    print(f"[Spirit Skills] Parsing command: '{cmd}'")

    # ── Open App ───────────────────────────────────────────
    if cmd.startswith("open "):
        return open_app(cmd[5:].strip())

    # ── Lock Screen ────────────────────────────────────────
    # Matches: "lock", "lock screen", "lock the screen", "lock pc", "lock the", etc.
    if re.search(r'\block\b', cmd):
        return lock_screen()

    # ── Cancel Shutdown (must be checked BEFORE shutdown/restart) ───
    if "cancel" in cmd and ("shutdown" in cmd or "shut down" in cmd or "restart" in cmd):
        return cancel_shutdown()

    # ── Shutdown ───────────────────────────────────────────
    if "shut down" in cmd or "shutdown" in cmd:
        return shutdown_pc()

    # ── Restart ────────────────────────────────────────────
    if "restart" in cmd or "reboot" in cmd:
        return restart_pc()

    # ── Sleep ──────────────────────────────────────────────
    if re.search(r'\b(go to sleep|sleep mode|put .* to sleep)\b', cmd) or cmd.strip() == "sleep":
        return sleep_pc()

    # ── Timer ──────────────────────────────────────────────
    if "timer" in cmd:
        mins_m = re.search(r'(\d+)\s*min', cmd)
        secs_m = re.search(r'(\d+)\s*sec', cmd)
        total = 0
        if mins_m:
            total += int(mins_m.group(1)) * 60
        if secs_m:
            total += int(secs_m.group(1))
        if total == 0:
            nums = re.findall(r'\d+', cmd)
            if nums:
                total = int(nums[0]) * 60
            else:
                return "How long should I set the timer for?"
        return set_timer(total, callback=speak_callback, pause_fn=pause_fn, resume_fn=resume_fn)

    # ── Alarm ──────────────────────────────────────────────
    if "alarm" in cmd:
        match = re.search(r'(\d{1,2})[:\s](\d{2})', cmd)
        if match:
            return set_alarm(int(match.group(1)), int(match.group(2)), callback=speak_callback)
        return "What time should I set the alarm for? Say something like 7 30."

    # ── Mute ───────────────────────────────────────────────
    if "mute" in cmd:
        return mute_volume()

    # ── Time ───────────────────────────────────────────────
    if "time" in cmd:
        now = time.localtime()
        hour = now.tm_hour
        minute = now.tm_min
        suffix = "AM" if hour < 12 else "PM"
        hour12 = hour % 12 or 12
        return f"It's {hour12}:{minute:02d} {suffix}"

    # ── Fallback ───────────────────────────────────────────
    return f"Sorry, I didn't understand: {command}"
