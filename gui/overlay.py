"""
Spirit Voice Assistant – Siri-like Sphere Overlay
A frameless, fullscreen overlay with a blurred background and animated sphere.
"""

import sys
import math
import io
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import (
    Qt, QTimer, QPointF, QRectF, pyqtSignal,
)
from PyQt6.QtGui import (
    QColor, QPainter, QBrush, QRadialGradient, QPen,
    QPixmap, QGuiApplication, QImage, QFont, QLinearGradient,
    QConicalGradient,
)
from PIL import Image, ImageFilter, ImageEnhance


# ── Colour Palette ─────────────────────────────────────────────────────────────
SPHERE_COLORS = {
    "idle":       [QColor(40,  60,  200),  QColor(80,  120, 255), QColor(120, 160, 255)],
    "listening":  [QColor(0,   160, 120),  QColor(0,   220, 170), QColor(80,  255, 200)],
    "processing": [QColor(140, 40,  220),  QColor(200, 80,  255), QColor(255, 120, 220)],
    "speaking":   [QColor(200, 100, 20),   QColor(255, 160, 40),  QColor(255, 210, 100)],
}

STATE_LABELS = {
    "idle":       'Say "Spirit" or press Ctrl+Space…',
    "listening":  "Listening…",
    "processing": "Thinking…",
    "speaking":   "",
}


class SphereWidget(QWidget):
    """Animated glowing sphere widget — premium edition."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(320, 320)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._pulse       = 0.0
        self._ring_angle  = 0.0
        self._ring2_angle = 0.0
        self._wave_offset = 0.0
        self._speak_phase = 0.0
        self._state       = "idle"
        self._particle_offsets = [i * (2 * math.pi / 10) for i in range(10)]

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)

    def set_state(self, state: str):
        self._state = state
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        if not self._timer.isActive():
            self._timer.start(16)   # ~60 fps

    def hideEvent(self, event):
        super().hideEvent(event)
        self._timer.stop()

    def _tick(self):
        speed = {"idle": 0.018, "listening": 0.032, "processing": 0.045, "speaking": 0.038}
        s = speed.get(self._state, 0.02)
        self._pulse       = (self._pulse + s) % (2 * math.pi)
        self._ring_angle  = (self._ring_angle  + 1.8) % 360
        self._ring2_angle = (self._ring2_angle - 1.1) % 360
        self._wave_offset = (self._wave_offset + 0.07) % (2 * math.pi)
        self._speak_phase = (self._speak_phase + 0.12) % (2 * math.pi)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx, cy  = self.width() / 2, self.height() / 2
        base_r  = 100
        pulse_a = 8 * math.sin(self._pulse)
        r       = base_r + pulse_a

        colors = SPHERE_COLORS.get(self._state, SPHERE_COLORS["idle"])
        c1, c2, c3 = colors

        # ── Deep ambient glow (outermost) ──────────────────────────────────
        for i in range(6, 0, -1):
            glow_r = r + i * 12
            alpha  = max(0, int(18 - i * 2.5))
            gc     = QColor(c3.red(), c3.green(), c3.blue(), alpha)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gc))
            painter.drawEllipse(QPointF(cx, cy), glow_r, glow_r)

        # ── Mid glow ring ──────────────────────────────────────────────────
        for i in range(4, 0, -1):
            glow_r = r + i * 8
            alpha  = max(0, int(40 - i * 8))
            gc     = QColor(c2.red(), c2.green(), c2.blue(), alpha)
            painter.setBrush(QBrush(gc))
            painter.drawEllipse(QPointF(cx, cy), glow_r, glow_r)

        # ── Main sphere body ───────────────────────────────────────────────
        grad = QRadialGradient(cx - r * 0.28, cy - r * 0.28, r * 1.7)
        grad.setColorAt(0.00, QColor(255, 255, 255, 100))
        grad.setColorAt(0.15, c3)
        grad.setColorAt(0.45, c2)
        grad.setColorAt(0.75, c1)
        grad.setColorAt(1.00, QColor(c1.red() // 3, c1.green() // 3, c1.blue() // 3, 230))
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # ── Specular highlight (top-left) ──────────────────────────────────
        hl = QRadialGradient(cx - r * 0.22, cy - r * 0.30, r * 0.55)
        hl.setColorAt(0.0, QColor(255, 255, 255, 150))
        hl.setColorAt(0.6, QColor(255, 255, 255, 30))
        hl.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(hl))
        painter.drawEllipse(QPointF(cx - r * 0.12, cy - r * 0.18), r * 0.52, r * 0.38)

        # ── Bottom reflection ──────────────────────────────────────────────
        br = QRadialGradient(cx + r * 0.15, cy + r * 0.40, r * 0.35)
        br.setColorAt(0.0, QColor(255, 255, 255, 35))
        br.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(br))
        painter.drawEllipse(QPointF(cx + r * 0.1, cy + r * 0.35), r * 0.32, r * 0.22)

        # ── Animated rings ─────────────────────────────────────────────────
        if self._state in ("listening", "processing", "speaking"):
            # Ring 1 — solid arc
            ring_r = r + 20 + 5 * math.sin(self._pulse * 2)
            pen1 = QPen(QColor(c3.red(), c3.green(), c3.blue(), 90), 2.0)
            painter.setPen(pen1)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(self._ring_angle)
            painter.drawArc(QRectF(-ring_r, -ring_r, ring_r * 2, ring_r * 2), 0, 240 * 16)
            painter.restore()

            # Ring 2 — counter-rotating dashed arc
            ring_r2 = r + 34 + 3 * math.sin(self._pulse * 1.5 + 1)
            pen2 = QPen(QColor(c2.red(), c2.green(), c2.blue(), 55), 1.5)
            pen2.setStyle(Qt.PenStyle.DashLine)
            painter.setPen(pen2)
            painter.save()
            painter.translate(cx, cy)
            painter.rotate(self._ring2_angle)
            painter.drawArc(QRectF(-ring_r2, -ring_r2, ring_r2 * 2, ring_r2 * 2), 30 * 16, 200 * 16)
            painter.restore()

        # ── Sound-wave bars (listening) ────────────────────────────────────
        if self._state == "listening":
            bar_count = 32
            for i in range(bar_count):
                angle = (2 * math.pi / bar_count) * i + self._wave_offset
                bar_h = 6 + 18 * abs(math.sin(angle * 2.5 + self._wave_offset * 3))
                bx = cx + (r + 28) * math.cos(angle)
                by = cy + (r + 28) * math.sin(angle)
                alpha = 120 + int(80 * abs(math.sin(angle + self._wave_offset)))
                bar_color = QColor(c3.red(), c3.green(), c3.blue(), min(255, alpha))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(bar_color))
                painter.save()
                painter.translate(bx, by)
                painter.rotate(math.degrees(angle) + 90)
                painter.drawRoundedRect(QRectF(-2, 0, 4, bar_h), 2, 2)
                painter.restore()

        # ── Orbiting particles (processing) ───────────────────────────────
        if self._state == "processing":
            for i, offset in enumerate(self._particle_offsets):
                pa = offset + self._ring_angle * math.pi / 180
                pr = r + 32 + 10 * math.sin(self._pulse + i * 0.7)
                px = cx + pr * math.cos(pa)
                py = cy + pr * math.sin(pa)
                p_size = 3 + 3 * abs(math.sin(self._pulse + i * 0.5))
                alpha  = 160 + int(80 * abs(math.sin(self._pulse + i)))
                pc = QColor(c3.red(), c3.green(), c3.blue(), min(255, alpha))
                # Particle glow
                pg = QRadialGradient(px, py, p_size * 2)
                pg.setColorAt(0.0, pc)
                pg.setColorAt(1.0, QColor(pc.red(), pc.green(), pc.blue(), 0))
                painter.setBrush(QBrush(pg))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(px, py), p_size * 2, p_size * 2)
                painter.setBrush(QBrush(pc))
                painter.drawEllipse(QPointF(px, py), p_size, p_size)

        # ── Speaking waveform (vertical bars inside sphere) ────────────────
        if self._state == "speaking":
            bar_count = 12
            bar_w = 5
            spacing = 9
            total_w = bar_count * (bar_w + spacing) - spacing
            start_x = cx - total_w / 2
            for i in range(bar_count):
                phase = self._speak_phase + i * 0.55
                bh = 10 + 38 * abs(math.sin(phase))
                bx = start_x + i * (bar_w + spacing)
                by = cy - bh / 2
                alpha = 160 + int(80 * abs(math.sin(phase)))
                bc = QColor(255, 255, 255, min(255, alpha))
                painter.setBrush(QBrush(bc))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(QRectF(bx, by, bar_w, bh), 3, 3)

        painter.end()


class OverlayWindow(QWidget):
    """Full-screen overlay with blurred background and animated sphere."""

    dismiss_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._bg_pixmap   = None
        self._state       = "idle"
        self._is_active   = False

        # Sphere (hidden by default)
        self.sphere = SphereWidget(self)
        self.sphere.hide()

        self._status_text   = STATE_LABELS["idle"]
        self._response_text = ""

    # ── Public API ────────────────────────────────────────────────────────
    def set_state(self, state: str):
        self._state = state
        self.sphere.set_state(state)
        self._status_text = STATE_LABELS.get(state, "")
        self.update()

    def set_response(self, text: str):
        self._response_text = text
        self.update()

    def show_overlay(self):
        """Show the overlay. Only re-captures background if not already visible."""
        if self._is_active:
            self.raise_()
            self.activateWindow()
            return

        self._is_active = True
        print("[Spirit UI] Capturing background...")

        try:
            screen = QGuiApplication.primaryScreen()
            if screen:
                shot  = screen.grabWindow(0)
                qimg  = shot.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
                w, h  = qimg.width(), qimg.height()
                ptr   = qimg.bits()
                ptr.setsize(h * w * 4)
                pil_img = Image.frombytes("RGBA", (w, h), bytes(ptr))
                pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius=45))
                pil_img = ImageEnhance.Brightness(pil_img).enhance(0.32)

                buf = io.BytesIO()
                pil_img.save(buf, format="PNG")
                buf.seek(0)
                blurred_px = QPixmap()
                blurred_px.loadFromData(buf.getvalue(), "PNG")
                self._bg_pixmap = blurred_px
        except Exception as e:
            print(f"[Spirit UI] Blur capture failed: {e}")
            self._bg_pixmap = None

        self.showFullScreen()
        self.sphere.show()
        self._centre_sphere()
        self.raise_()
        self.activateWindow()
        print("[Spirit UI] Overlay shown.")

    def hide_overlay(self):
        if not self._is_active:
            return
        self._is_active = False
        self.sphere.hide()
        self.hide()
        self._response_text = ""
        print("[Spirit UI] Overlay hidden.")

    def pause_overlay(self):
        """Temporarily remove always-on-top so other windows can receive input."""
        if self.isVisible():
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
            self.show()
            print("[Spirit UI] Overlay paused (not on top).")

    def resume_overlay(self):
        """Restore always-on-top."""
        if self.isVisible():
            self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
            self.show()
            print("[Spirit UI] Overlay resumed (on top).")

    # ── Events ────────────────────────────────────────────────────────────
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._centre_sphere()

    def _centre_sphere(self):
        if self.sphere:
            sw, sh = self.sphere.width(), self.sphere.height()
            x = (self.width() - sw) // 2
            y = (self.height() - sh) // 2 - 60
            self.sphere.move(x, y)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # ── Blurred background ─────────────────────────────────────────────
        if self._bg_pixmap:
            painter.drawPixmap(0, 0, self._bg_pixmap.scaled(
                self.size(), Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))
        else:
            painter.fillRect(self.rect(), QColor(0, 0, 0, 200))

        # ── Subtle dark vignette ───────────────────────────────────────────
        vg = QRadialGradient(self.width() / 2, self.height() / 2,
                             max(self.width(), self.height()) * 0.8)
        vg.setColorAt(0.0, QColor(0, 0, 0, 0))
        vg.setColorAt(0.7, QColor(0, 0, 0, 0))
        vg.setColorAt(1.0, QColor(0, 0, 0, 60))
        painter.fillRect(self.rect(), QBrush(vg))

        # ── "Spirit" name label ────────────────────────────────────────────
        name_font = QFont("Segoe UI", 13, QFont.Weight.Light)
        painter.setFont(name_font)
        painter.setPen(QColor(255, 255, 255, 100))
        painter.drawText(
            QRectF(0, self.height() // 2 - 280, self.width(), 30),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "SPIRIT",
        )

        # ── Response / status text ─────────────────────────────────────────
        text = self._status_text
        if self._state == "speaking" and self._response_text:
            text = self._response_text

        if text:
            # Glassmorphism pill behind text
            colors = SPHERE_COLORS.get(self._state, SPHERE_COLORS["idle"])
            accent = colors[1]
            text_y = self.height() // 2 + 115

            # Measure text width for pill
            font = QFont("Segoe UI", 17)
            font.setWeight(QFont.Weight.Light)
            painter.setFont(font)
            fm = painter.fontMetrics()
            text_w = min(fm.horizontalAdvance(text) + 60, self.width() - 80)
            pill_x = (self.width() - text_w) / 2
            pill_rect = QRectF(pill_x, text_y - 10, text_w, 50)

            # Pill background
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 60))
            painter.drawRoundedRect(pill_rect, 25, 25)

            # Pill border with accent glow
            pill_pen = QPen(QColor(accent.red(), accent.green(), accent.blue(), 70), 1.0)
            painter.setPen(pill_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(pill_rect, 25, 25)

            # Text
            painter.setPen(QColor(255, 255, 255, 220))
            painter.drawText(
                pill_rect,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                text,
            )

        # ── Bottom hint ────────────────────────────────────────────────────
        hint_font = QFont("Segoe UI", 10)
        hint_font.setWeight(QFont.Weight.Light)
        painter.setFont(hint_font)
        painter.setPen(QColor(255, 255, 255, 55))
        painter.drawText(
            QRectF(0, self.height() - 45, self.width(), 35),
            Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
            "Esc to dismiss  ·  Ctrl+Space to talk",
        )

        painter.end()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.dismiss_requested.emit()
            self.hide_overlay()
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        sphere_rect = self.sphere.geometry()
        if not sphere_rect.contains(event.pos()):
            self.dismiss_requested.emit()
            self.hide_overlay()
        super().mousePressEvent(event)
