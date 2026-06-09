from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QPainterPath, QLinearGradient, QColor, QPixmap
from PyQt6.QtCore import QPointF
from components.base_component import SynthComponent, COLOR_CYAN, COLOR_CYAN_GLOW, COLOR_CYAN_FILL

class EnvelopeWidget(SynthComponent):

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(self._make_screen("ENV"))

        knobs = QHBoxLayout()
        knobs.setSpacing(10)
        knobs.addStretch()

        self.dial_a = self._make_knob(knobs, "ATTACK", default_value=20)
        self.dial_d = self._make_knob(knobs, "DECAY", default_value=30)
        self.dial_s = self._make_knob(knobs, "SUSTAIN", default_value=70)
        self.dial_r = self._make_knob(knobs, "RELEASE", default_value=40)

        # On connecte chaque dial à la fonction _sync() lorsque leur valeur change
        for dial in (self.dial_a, self.dial_d, self.dial_s, self.dial_r):
            dial.valueChanged.connect(self._sync)

        knobs.addStretch()
        layout.addLayout(knobs)

        self._sync()

    def _config(self) -> dict:
        # On return un dictionnaire avec les valeurs des dials
        return {
            "attack":  self.dial_a.value() / 100.0,
            "decay":   self.dial_d.value() / 100.0,
            "sustain": self.dial_s.value() / 100.0,
            "release": self.dial_r.value() / 100.0,
        }

    # FONCTION GÉNÉRÉE PAR IA (très peu touchée à part la position des points de la courbe) !!!
    def _draw(self):
        w, h = self.screen_width, self.screen_height
        cfg = self._config()

        SUSTAIN_HOLD_RATIO: float = 0.3 # durée visuelle fixe du plateau sustain

        total = cfg["attack"] + cfg["decay"] + SUSTAIN_HOLD_RATIO + cfg["release"] or 1

        def seg(v: float) -> int: return int(v / total * w)

        x_a = seg(cfg["attack"])
        x_d = x_a + seg(cfg["decay"])
        x_r = x_d + seg(cfg["release"])

        top = int(h * 0.25)
        bottom = int(h * 0.9)
        sus_y = int(bottom - cfg["sustain"] * (bottom - top))

        pts = [
            QPointF(0,   bottom),
            QPointF(x_a, top),
            QPointF(x_d, sus_y),
            QPointF(x_r, bottom),
        ]

        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.GlobalColor.transparent)

        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        curve = QPainterPath()
        curve.moveTo(pts[0])
        for pt in pts[1:]:
            curve.lineTo(pt)

        fill = QPainterPath(curve)
        fill.lineTo(w, bottom)
        fill.lineTo(0, bottom)
        fill.closeSubpath()
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.2, COLOR_CYAN_FILL)
        grad.setColorAt(0.8, QColor(0, 212, 255, 10))
        p.fillPath(fill, grad)

        p.setPen(QPen(COLOR_CYAN_GLOW, 4))
        p.drawPath(curve)

        p.setPen(QPen(COLOR_CYAN, 2))
        p.drawPath(curve)

        p.end()
        self.screen.setPixmap(pixmap)