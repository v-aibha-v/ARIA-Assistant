"""
Spirit – Windows Voice Assistant
Main entry point.  Launches UI, voice-processing thread, and global hotkey.
"""

import sys
import os
import traceback
import keyboard
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QAction, QFont
from PyQt6.QtCore import Qt, QObject, pyqtSignal

# Log output to file when running as a frozen exe (no console)
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    try:
        _log_dir = os.path.join(os.environ.get('APPDATA', os.path.dirname(sys.executable)), 'Spirit')
        os.makedirs(_log_dir, exist_ok=True)
        _log_path = os.path.join(_log_dir, 'spirit.log')
        sys.stdout = open(_log_path, 'w', encoding='utf-8')
        sys.stderr = open(_log_path, 'a', encoding='utf-8')
    except Exception:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')


class HotkeyBridge(QObject):
    """Thread-safe bridge between `keyboard` lib and Qt main thread."""
    triggered = pyqtSignal()


def _get_icon_path():
    """Resolve the icon path whether running from source or frozen exe."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'assets', 'spirit.ico')


def create_tray_icon(app, overlay):
    icon_path = _get_icon_path()
    if os.path.exists(icon_path):
        icon = QIcon(icon_path)
    else:
        # Fallback: draw a simple icon if file not found
        px = QPixmap(64, 64)
        px.fill(QColor(0, 0, 0, 0))
        p = QPainter(px)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QColor(80, 140, 255))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(4, 4, 56, 56)
        p.setPen(QColor(255, 255, 255))
        font = QFont("Segoe UI", 22, QFont.Weight.Bold)
        p.setFont(font)
        p.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "S")
        p.end()
        icon = QIcon(px)

    tray = QSystemTrayIcon(icon, app)
    menu = QMenu()
    show_action = QAction("Show Spirit", menu)
    show_action.triggered.connect(overlay.show_overlay)
    menu.addAction(show_action)
    quit_action = QAction("Quit", menu)
    quit_action.triggered.connect(app.quit)
    menu.addAction(quit_action)
    tray.setContextMenu(menu)
    tray.setToolTip("Spirit Voice Assistant")
    tray.activated.connect(
        lambda reason: overlay.show_overlay()
        if reason == QSystemTrayIcon.ActivationReason.Trigger
        else None
    )
    tray.show()
    return tray


def main():
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Spirit")
        app.setQuitOnLastWindowClosed(False)

        from gui.overlay import OverlayWindow
        from core.assistant import AssistantThread

        overlay = OverlayWindow()
        assistant = AssistantThread()

        # ── Signal Wiring ─────────────────────────────────────
        # State changes only update the sphere visuals (no show/hide)
        assistant.state_changed.connect(overlay.set_state)
        assistant.response_ready.connect(overlay.set_response)

        # Explicit overlay control from assistant
        assistant.overlay_show.connect(overlay.show_overlay)
        assistant.overlay_hide.connect(overlay.hide_overlay)
        assistant.overlay_pause.connect(overlay.pause_overlay)
        assistant.overlay_resume.connect(overlay.resume_overlay)

        assistant.error_occurred.connect(lambda err: print(f"[Spirit Error] {err}"))

        # ── Global Hotkey: Ctrl+Space ─────────────────────────
        hotkey_bridge = HotkeyBridge()

        def on_hotkey_activated():
            try:
                if not overlay.isVisible():
                    overlay.show_overlay()
                assistant.push_to_talk.emit()
            except Exception as e:
                print(f"[Spirit] Hotkey error: {e}")

        hotkey_bridge.triggered.connect(on_hotkey_activated)

        try:
            keyboard.add_hotkey("ctrl+space", lambda: hotkey_bridge.triggered.emit(), suppress=False)
            print("[Spirit] Hotkey 'Ctrl+Space' registered.")
        except Exception as e:
            print(f"[Spirit] Could not register hotkey (try running as admin): {e}")

        # ── Start ─────────────────────────────────────────────
        assistant.start()
        tray = create_tray_icon(app, overlay)

        def cleanup():
            try:
                keyboard.unhook_all()
            except Exception:
                pass
            assistant.stop()

        app.aboutToQuit.connect(cleanup)

        print("[Spirit] Running — say 'Spirit' or press Ctrl+Space to activate.")
        sys.exit(app.exec())

    except Exception as e:
        traceback.print_exc()
        # Show error via Windows dialog (no console available in frozen windowed mode)
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                f"Spirit failed to start:\n\n{e}\n\nCheck the log at:\n%APPDATA%\\Spirit\\spirit.log",
                "Spirit \u2013 Fatal Error",
                0x00000010 | 0x00001000,
            )
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
