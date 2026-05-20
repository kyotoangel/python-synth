import numpy as np
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QDial
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QPainterPath, QLinearGradient, QColor, QPixmap, QPolygonF
from PyQt6.QtCore import QPointF

# ── dimensions ────────────────────────────────────────────────
WIDGET_WIDTH  = 400
WIDGET_HEIGHT = 220
SCREEN_WIDTH  = 384
SCREEN_HEIGHT = 130

# ── couleurs (reprises de osc_widget) ─────────────────────────
COLOR_CYAN      = QColor(0, 212, 255)
COLOR_CYAN_GLOW = QColor(0, 212, 255, 80)
COLOR_CYAN_FILL = QColor(0, 212, 255, 60)

# ── styles ────────────────────────────────────────────────────
STYLE_WIDGET      = "background: #070809; border: none;"
STYLE_SCREEN      = "background: black; border-radius: 8px; border: 1px solid #1a1a1a;"
STYLE_TITLE_LABEL = "color: #eee; font-size: 11px; font-weight: bold; background: transparent;"
STYLE_KNOB_LABEL  = "color: #555; font-size: 9px; font-weight: bold;"
STYLE_DIAL        = "background: #1a1a1a;"


def _make_dial(parent_layout, name, default=0):
    """Crée un dial + label et les ajoute dans un QVBoxLayout vertical."""
    col = QVBoxLayout()
    col.setSpacing(2)

    dial = QDial()
    dial.setFixedSize(40, 40)
    dial.setValue(default)
    dial.setStyleSheet(STYLE_DIAL)

    lbl = QLabel(name)
    lbl.setStyleSheet(STYLE_KNOB_LABEL)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

    col.addStretch()
    col.addWidget(lbl)
    col.addWidget(dial)
    col.addStretch()

    parent_layout.addLayout(col)
    return dial


class EnvelopeWidget(QFrame):
    """
    Widget ADSR simple, dans le même style que VitalOsc.
    Émet config_updated(dict) à chaque changement.
    """

    config_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setFixedSize(WIDGET_WIDTH, WIDGET_HEIGHT)
        self.setStyleSheet(STYLE_WIDGET)
        self._setup_ui()

    # ── construction UI ───────────────────────────────────────

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Écran
        self.screen = QLabel()
        self.screen.setFixedSize(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.screen.setStyleSheet(STYLE_SCREEN)

        self.lbl_title = QLabel("ENV", self.screen)
        self.lbl_title.setGeometry(0, 0, SCREEN_WIDTH, 20)
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setStyleSheet(STYLE_TITLE_LABEL)

        layout.addWidget(self.screen)

        knobs_layout = QHBoxLayout()
        knobs_layout.setSpacing(4)
        knobs_layout.addStretch()

        self.dial_a = _make_dial(knobs_layout, "ATTACK",  default=20)
        self.dial_d = _make_dial(knobs_layout, "DECAY",   default=30)
        self.dial_s = _make_dial(knobs_layout, "SUSTAIN", default=70)
        self.dial_r = _make_dial(knobs_layout, "RELEASE", default=40)

        for dial in (self.dial_a, self.dial_d, self.dial_s, self.dial_r):
            dial.valueChanged.connect(self._sync)

        knobs_layout.addStretch()

        layout.addLayout(knobs_layout)

        self._sync()

    def _sync(self):
        self._draw_envelope()
        self.config_updated.emit(self._config())

    def _config(self):
        return {
            "attack":  self.dial_a.value() / 100.0,
            "decay":   self.dial_d.value() / 100.0,
            "sustain": self.dial_s.value() / 100.0,
            "release": self.dial_r.value() / 100.0,
        }

    def _draw_envelope(self):
        w, h = SCREEN_WIDTH, SCREEN_HEIGHT
        cfg = self._config()

        # On répartit la largeur en segments proportionnels
        # [attack | decay | sustain_hold | release]
        total = cfg["attack"] + cfg["decay"] + 0.3 + cfg["release"]
        if total == 0:
            total = 1

        def seg(v): return int(v / total * w)

        x_a = seg(cfg["attack"])           # fin attack
        x_d = x_a + seg(cfg["decay"])      # fin decay
        x_r = x_d + seg(cfg["release"])    # fin release

        top    = int(h * 0.25)             # niveau max (attack peak)
        bottom = int(h * 0.9)             # niveau zéro
        sus_y  = int(bottom - cfg["sustain"] * (bottom - top))

        # Points de l'enveloppe
        pts = [
            QPointF(0,   bottom),   # départ
            QPointF(x_a, top),      # peak attack
            QPointF(x_d, sus_y),    # fin decay → sustain level
            QPointF(x_r, bottom),   # release → zéro
        ]

        fill_end = QPointF(w, bottom)

        # ── rendu ──
        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.GlobalColor.transparent)

        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        curve = QPainterPath()
        curve.moveTo(pts[0])
        for pt in pts[1:]:
            curve.lineTo(pt)

        # Passe 1 : remplissage dégradé
        fill = QPainterPath(curve)
        fill.lineTo(w, bottom)
        fill.lineTo(0, bottom)
        fill.closeSubpath()
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.2, COLOR_CYAN_FILL)
        grad.setColorAt(0.8, QColor(0, 212, 255, 10))
        p.fillPath(fill, grad)

        # Passe 2 : halo
        p.setPen(QPen(COLOR_CYAN_GLOW, 4))
        p.drawPath(curve)

        # Passe 3 : ligne principale
        p.setPen(QPen(COLOR_CYAN, 2))
        p.drawPath(curve)

        p.end()
        self.screen.setPixmap(pixmap)