import numpy as np
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# ── dimensions ────────────────────────────────────────────────
WIDGET_WIDTH  = 400
WIDGET_HEIGHT = 250
SCREEN_WIDTH  = 384
SCREEN_HEIGHT = 160

# ── couleurs (jaune/doré comme Vital pour le filtre) ──────────
COLOR_GOLD      = QColor(220, 180, 40)
COLOR_GOLD_GLOW = QColor(220, 180, 40, 80)
COLOR_GOLD_FILL = QColor(220, 180, 40, 55)

COLOR_BTN_ACTIVE   = QColor(220, 180, 40)
COLOR_BTN_INACTIVE = QColor(60, 60, 60)

# ── styles ────────────────────────────────────────────────────
STYLE_WIDGET     = "background: #070809; border: none;"
STYLE_SCREEN     = "background: black; border-radius: 8px; border: 1px solid #1a1a1a;"
STYLE_TYPE_LABEL = "color: #eee; font-size: 11px; font-weight: bold; background: transparent;"
STYLE_ARROW_BTN  = """
    QPushButton       { color: #555; background: transparent; font-size: 14px; border: none; }
    QPushButton:hover { color: white; }
"""
STYLE_KNOB_LABEL = "color: #555; font-size: 9px; font-weight: bold;"
STYLE_DIAL       = "background: #1a1a1a;"

FILTER_TYPES = ["LOW PASS", "HIGH PASS"]

# fréquences pour l'axe X de la réponse (20 Hz → 20 kHz)
FREQ_MIN  = 20.0
FREQ_MAX  = 20000.0
SAMPLE_RATE = 44100.0


def _lp_response(freqs, cutoff):
    """Réponse amplitude d'un filtre passe-bas 1er ordre (12 dB/oct = 2 pôles)."""
    ratio = freqs / cutoff
    return 1.0 / (1.0 + ratio ** 2) ** 1.0   # 12 dB/oct


def _hp_response(freqs, cutoff):
    """Réponse amplitude d'un filtre passe-haut 12 dB/oct."""
    ratio = freqs / cutoff
    return ratio ** 2 / (1.0 + ratio ** 2) ** 1.0


class FilterWidget(QFrame):
    """
    Composant filtre dans le même style que VitalOsc.
    Émet config_updated(dict) à chaque changement.
    """

    config_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.filter_idx = 0          # 0 = LP, 1 = HP
        self.cutoff_norm = 0.5       # 0..1 → sera mappé en fréquence log
        self._fft_buffer = None

        self.setFixedSize(WIDGET_WIDTH, WIDGET_HEIGHT)
        self.setStyleSheet(STYLE_WIDGET)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)

        self.screen = QLabel()
        self.screen.setFixedSize(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.screen.setStyleSheet(STYLE_SCREEN)

        self.lbl_type = QLabel(FILTER_TYPES[self.filter_idx], self.screen)
        self.lbl_type.setGeometry(0, 0, SCREEN_WIDTH, 20)
        self.lbl_type.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_type.setStyleSheet(STYLE_TYPE_LABEL)

        btn_prev = self._arrow("<", x=0)
        btn_next = self._arrow(">", x=SCREEN_WIDTH - 20)
        btn_prev.clicked.connect(lambda: self._change_type(-1))
        btn_next.clicked.connect(lambda: self._change_type(+1))

        # slider cutoff en bas de l'écran (par-dessus)
        self.slider = QSlider(Qt.Orientation.Horizontal, self.screen)
        self.slider.setGeometry(8, SCREEN_HEIGHT - 18, SCREEN_WIDTH - 16, 14)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setValue(500)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal { background: #1a1a1a; height: 4px; border-radius: 2px; }
            QSlider::handle:horizontal { background: #dCb428; width: 10px; height: 10px;
                                         margin: -3px 0; border-radius: 5px; }
            QSlider::sub-page:horizontal { background: #dCb428; height: 4px; border-radius: 2px; }
        """)
        self.slider.valueChanged.connect(self._sync)

        layout.addWidget(self.screen)

        self._timer = QTimer()
        self._timer.setInterval(50)  # 20 fps
        self._timer.timeout.connect(self._sync)
        self._timer.start()

        self._sync()

    def _arrow(self, txt, x):
        btn = QPushButton(txt, self.screen)
        btn.setGeometry(x, 0, 20, 20)
        btn.setStyleSheet(STYLE_ARROW_BTN)
        return btn

    # ── logique ───────────────────────────────────────────────

    def _change_type(self, delta):
        self.filter_idx = (self.filter_idx + delta) % len(FILTER_TYPES)
        self.lbl_type.setText(FILTER_TYPES[self.filter_idx])
        self._sync()

    def _on_dial(self, value):
        # dial et slider sont synchronisés
        self.slider.blockSignals(True)
        self.slider.setValue(value)
        self.slider.blockSignals(False)
        self._sync()

    def _sync(self):
        v = self.slider.value()
        self.cutoff_norm = v / 1000.0
        self._draw_response()
        self.config_updated.emit(self._config())

    def _config(self):
        return {
            "filter_type":   FILTER_TYPES[self.filter_idx].lower().replace(" ", "_"),
            "cutoff":        self._norm_to_freq(self.cutoff_norm),
            "active":        True
        }

    @staticmethod
    def _norm_to_freq(norm):
        """Mapping logarithmique 0..1 → 20..20000 Hz."""
        return FREQ_MIN * (FREQ_MAX / FREQ_MIN) ** norm

    def update_fft(self, buffer: np.ndarray):
        self._fft_buffer = buffer.copy()

    # ── dessin réponse fréquentielle ──────────────────────────
    def _draw_response(self):
        w = SCREEN_WIDTH
        h = SCREEN_HEIGHT - 20   # laisser place au slider en bas et titre en haut
        y_off = 20               # décalage vertical (sous le titre)

        cutoff = self._norm_to_freq(self.cutoff_norm)
        freqs  = np.logspace(np.log10(FREQ_MIN), np.log10(FREQ_MAX), w)

        if self.filter_idx == 0:   # LP
            mag = _lp_response(freqs, cutoff)
        else:                      # HP
            mag = _hp_response(freqs, cutoff)

        # normalise 0..1
        mag = np.clip(mag, 0, 1)

        pixmap = QPixmap(SCREEN_WIDTH, SCREEN_HEIGHT)
        pixmap.fill(Qt.GlobalColor.transparent)

        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # points de la courbe
        pts = [QPointF(i, y_off + (1.0 - mag[i]) * (h - 4)) for i in range(w)]

        curve = QPainterPath()
        curve.moveTo(pts[0])
        for pt in pts[1:]:
            curve.lineTo(pt)

        bottom = float(y_off + h - 4)

        # Passe 1 : fill dégradé
        fill = QPainterPath(curve)
        fill.lineTo(w, bottom)
        fill.lineTo(0, bottom)
        fill.closeSubpath()
        grad = QLinearGradient(0, y_off, 0, y_off + h)
        grad.setColorAt(0.0, COLOR_GOLD_FILL)
        grad.setColorAt(1.0, QColor(220, 180, 40, 5))
        p.fillPath(fill, grad)

        # Passe 2 : halo
        p.setPen(QPen(COLOR_GOLD_GLOW, 4))
        p.drawPath(curve)

        # Passe 3 : ligne principale
        p.setPen(QPen(COLOR_GOLD, 2))
        p.drawPath(curve)

        if self._fft_buffer is not None and len(self._fft_buffer) > 0:
            fft_mag = np.abs(np.fft.rfft(self._fft_buffer))
            fft_freqs = np.fft.rfftfreq(len(self._fft_buffer), 1.0 / SAMPLE_RATE)

            # on ignore DC et on clip aux fréquences utiles
            mask = (fft_freqs >= FREQ_MIN) & (fft_freqs <= FREQ_MAX)
            fft_freqs = fft_freqs[mask]
            fft_mag = fft_mag[mask]

            if len(fft_mag) > 0:
                # normalisation log
                fft_db = 20 * np.log10(fft_mag + 1e-9)
                fft_db = np.clip((fft_db + 80) / 80, 0, 1)  # -80 dB → 0, 0 dB → 1

                # resampling sur la largeur de l'écran
                x_log = np.logspace(np.log10(FREQ_MIN), np.log10(FREQ_MAX), w)
                fft_resampled = np.interp(x_log, fft_freqs, fft_db)

                fft_pts = [QPointF(i, y_off + (1.0 - fft_resampled[i]) * (h - 4)) for i in range(w)]

                fft_curve = QPainterPath()
                fft_curve.moveTo(fft_pts[0])
                for pt in fft_pts[1:]:
                    fft_curve.lineTo(pt)

                # ligne FFT semi-transparente par-dessus la réponse
                p.setPen(QPen(QColor(255, 255, 255, 60), 1))
                p.drawPath(fft_curve)

        p.end()
        self.screen.setPixmap(pixmap)