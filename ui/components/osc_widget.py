import numpy as np
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

WIDGET_WIDTH  = 400
WIDGET_HEIGHT = 180
SCREEN_WIDTH  = 300
SCREEN_HEIGHT = 120

WAVE_AMPLITUDE_RATIO = 1 / 3

COLOR_CYAN       = QColor(0, 212, 255)
COLOR_CYAN_GLOW  = QColor(0, 212, 255, 80)
COLOR_CYAN_FILL  = QColor(0, 212, 255, 60)

COLOR_BG_WIDGET = "#070809" # couleur du widget
COLOR_BG_SCREEN = "black" # couleur du graphique
COLOR_BG_DIAL   = "#1a1a1a"

STYLE_WIDGET = f"background: {COLOR_BG_WIDGET}; border: none;"
STYLE_SCREEN = f"background: {COLOR_BG_SCREEN}; border-radius: 8px; border: 1px solid #1a1a1a;"
STYLE_WAVE_LABEL  = "color: #eee; font-size: 11px; font-weight: bold; background: transparent;"
STYLE_ARROW_BTN   = """
    QPushButton       { color: #555; background: transparent; font-size: 14px; border: none; }
    QPushButton:hover { color: white; }
"""
STYLE_LEVEL_LABEL = "color: #555; font-size: 9px; font-weight: bold;"
STYLE_DIAL        = f"background: {COLOR_BG_DIAL};"

class VitalOsc(QFrame):
    """
    Composant oscillateur simple et réutilisable. (bon codé un peu avec le cul quand même :3)

    """

    config_updated = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.wf_types = ["SINE", "TRIANGLE", "SAWTOOTH", "SQUARE"]
        self.wf_idx = 2 # SAWTOOTH par défaut
        self.level = 0.5

        self.setFixedSize(WIDGET_WIDTH, WIDGET_HEIGHT)
        self.setStyleSheet(STYLE_WIDGET)

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)

        # Écran de visualisation
        self.screen = QLabel()
        self.screen.setFixedSize(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.screen.setStyleSheet(STYLE_SCREEN)

        self.lbl_name = QLabel(self.wf_types[self.wf_idx], self.screen)
        self.lbl_name.setGeometry(0, 0, SCREEN_WIDTH, 20)
        self.lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_name.setStyleSheet(STYLE_WAVE_LABEL)

        btn_prev = self._create_arrow_button("<", x=0)
        btn_next = self._create_arrow_button(">", x=SCREEN_WIDTH - 20)
        btn_prev.clicked.connect(lambda: self._change_waveform(-1))
        btn_next.clicked.connect(lambda: self._change_waveform(+1))

        layout.addWidget(self.screen)

        # Knob LEVEL
        ctrl = QVBoxLayout()

        self.dial = QDial()
        self.dial.setFixedSize(50, 50)
        self.dial.setValue(50)
        self.dial.setStyleSheet(STYLE_DIAL)
        self.dial.valueChanged.connect(self._sync)

        lbl_level = QLabel("LEVEL")
        lbl_level.setStyleSheet(STYLE_LEVEL_LABEL)
        lbl_level.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ctrl.addStretch()
        ctrl.addWidget(lbl_level)
        ctrl.addWidget(self.dial)
        ctrl.addStretch()
        layout.addLayout(ctrl)

        self._sync()
    
    def _create_arrow_button(self, txt, x):
        btn = QPushButton(txt, self.screen)
        btn.setGeometry(x, 0, 20, 20)
        btn.setStyleSheet(STYLE_ARROW_BTN)
        return btn

    def _change_waveform(self, delta):
        self.wf_idx = (self.wf_idx + delta) % len(self.wf_types)
        self.lbl_name.setText(self.wf_types[self.wf_idx])
        self._sync()

    def _sync(self):
        self.level = self.dial.value() / 100.0
        self._draw_wave()
        self.config_updated.emit({
            "waveform": self.wf_types[self.wf_idx].lower(),
            "level":    self.level
        })

    def _draw_wave(self):
        w, h = SCREEN_WIDTH, SCREEN_HEIGHT

        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.GlobalColor.transparent)

        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        x_vals = np.linspace(0, 2 * np.pi, w)
        wf = self.wf_types[self.wf_idx]

        if wf == "SINE":
            y_vals = np.sin(x_vals)
        elif wf == "TRIANGLE":
            y_vals = (2 / np.pi) * np.arcsin(np.sin(x_vals))
        elif wf == "SAWTOOTH":
            y_vals = (x_vals % (2 * np.pi)) / np.pi - 1
        else:  # SQUARE
            y_vals = np.sign(np.sin(x_vals))

        amplitude = self.level * h * WAVE_AMPLITUDE_RATIO
        points = [QPointF(i, h / 2 - y_vals[i] * amplitude) for i in range(w)]

        curve = QPainterPath()
        curve.addPolygon(QPolygonF(points))

        # Passe 1 : remplissage dégradé
        fill_path = QPainterPath()
        fill_path.addPolygon(QPolygonF(points))
        fill_path.lineTo(w, h / 2)
        fill_path.lineTo(0, h / 2)
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.3, COLOR_CYAN_FILL)
        grad.setColorAt(0.7, QColor(0, 212, 255, 10))
        p.fillPath(fill_path, grad)

        # Passe 2 : halo
        p.setPen(QPen(COLOR_CYAN_GLOW, 4))
        p.drawPath(curve)

        # Passe 3 : ligne principale
        p.setPen(QPen(COLOR_CYAN, 2))
        p.drawPath(curve)

        p.end()
        self.screen.setPixmap(pixmap)