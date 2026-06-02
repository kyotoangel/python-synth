import numpy as np
from PyQt6.QtWidgets import QHBoxLayout, QSlider, QLabel
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QPainterPath, QLinearGradient, QColor, QPixmap
from PyQt6.QtCore import QPointF

from components.base_component import (
    SynthComponent,
    COLOR_CYAN, COLOR_CYAN_GLOW, COLOR_CYAN_FILL,
)

WIDGET_HEIGHT = 250
SCREEN_HEIGHT = 160

STYLE_SLIDER = """
    QSlider::groove:horizontal { background: #1a1a1a; height: 4px; border-radius: 2px; }
    QSlider::handle:horizontal { background: #00d4ff; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
    QSlider::sub-page:horizontal { background: #00d4ff; height: 4px; border-radius: 2px; }
"""

FREQ_MIN    = 20.0
FREQ_MAX    = 20000.0

FILTER_TYPES = ["LOW PASS", "HIGH PASS"]


def _lp_response(freqs, cutoff):
    ratio = freqs / cutoff
    return 1.0 / (1.0 + ratio ** 2)


def _hp_response(freqs, cutoff):
    ratio = freqs / cutoff
    return ratio ** 2 / (1.0 + ratio ** 2)


class FilterWidget(SynthComponent):

    config_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__(widget_height=WIDGET_HEIGHT, screen_height=SCREEN_HEIGHT)

        self.filter_idx  = 0
        self.cutoff_norm = 0.5
        self.cutoff = self._norm_to_freq(self.cutoff_norm)

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)

        layout.addWidget(self._make_screen(FILTER_TYPES[self.filter_idx]))

        btn_prev = self._make_arrow("<", x=0)
        btn_next = self._make_arrow(">", x=self.screen_width - 20)
        btn_prev.clicked.connect(lambda: self._change_type(-1))
        btn_next.clicked.connect(lambda: self._change_type(+1))

        self.slider = QSlider(Qt.Orientation.Horizontal, self.screen)
        self.slider.setGeometry(8, self.screen_height - 18, self.screen_width - 16, 14)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setValue(500)
        self.slider.setStyleSheet(STYLE_SLIDER)
        self.slider.valueChanged.connect(self._sync)

        self.lbl_tuning_val = QLabel(f"{self.cutoff} Hz")
        self.lbl_tuning_val.setStyleSheet("color: #555; font-size: 9px; font-weight: bold;")
        self.lbl_tuning_val.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.lbl_tuning_val)

        self._sync()

    def _change_type(self, delta):
        self.filter_idx = (self.filter_idx + delta) % len(FILTER_TYPES)
        self.lbl_title.setText(FILTER_TYPES[self.filter_idx])
        self._sync()

    def _sync(self):
        self.cutoff_norm = self.slider.value() / 1000.0
        self.cutoff = self._norm_to_freq(self.cutoff_norm)
        self.lbl_tuning_val.setText(f"{self.cutoff} Hz")
        super()._sync()

    def _config(self) -> dict:
        return {
            "filter_type": FILTER_TYPES[self.filter_idx].lower().replace(" ", "_"),
            "cutoff":      self.cutoff,
            "active":      True,
        }

    @staticmethod
    def _norm_to_freq(norm: float) -> float:
        return FREQ_MIN * (FREQ_MAX / FREQ_MIN) ** norm

    # ── Dessin ────────────────────────────────────────────────

    def _draw(self):
        w     = self.screen_width
        h     = self.screen_height - 20
        y_off = 20

        cutoff = self._norm_to_freq(self.cutoff_norm)
        freqs  = np.logspace(np.log10(FREQ_MIN), np.log10(FREQ_MAX), w)

        mag = (_lp_response if self.filter_idx == 0 else _hp_response)(freqs, cutoff)
        mag = np.clip(mag, 0, 1)

        pixmap = QPixmap(self.screen_width, self.screen_height)
        pixmap.fill(Qt.GlobalColor.transparent)

        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        pts    = [QPointF(i, y_off + (1.0 - mag[i]) * (h - 4)) for i in range(w)]
        bottom = float(y_off + h - 4)

        curve = QPainterPath()
        curve.moveTo(pts[0])
        for pt in pts[1:]:
            curve.lineTo(pt)

        fill = QPainterPath(curve)
        fill.lineTo(w, bottom)
        fill.lineTo(0, bottom)
        fill.closeSubpath()
        grad = QLinearGradient(0, y_off, 0, y_off + h)
        grad.setColorAt(0.0, COLOR_CYAN_FILL)
        grad.setColorAt(1.0, QColor(220, 180, 40, 5))
        p.fillPath(fill, grad)

        p.setPen(QPen(COLOR_CYAN_GLOW, 4))
        p.drawPath(curve)

        p.setPen(QPen(COLOR_CYAN, 2))
        p.drawPath(curve)

        p.end()
        self.screen.setPixmap(pixmap)