import numpy as np
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QSlider
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QPainterPath, QLinearGradient, QColor, QPixmap, QPolygonF
from PyQt6.QtCore import QPointF
from components.base_component import SynthComponent, COLOR_CYAN, COLOR_CYAN_GLOW, COLOR_CYAN_FILL, STYLE_SLIDER

WAVE_AMPLITUDE_RATIO: float = 1 / 3

class OscWidget(SynthComponent):

    def __init__(self):
        super().__init__()

        # Type de waveform disponible dans le composant (ici Sine, Triangle, Sawtooth et Square)
        self.wf_types = ["SINE", "TRIANGLE", "SAW", "SQUARE"]
        self.wf_index = 0

        self.level = 0.5
        self.tuning = 440

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(self._make_screen(self.wf_types[self.wf_index]))

        btn_prev = self._make_arrow("<", x=0)
        btn_next = self._make_arrow(">", x=self.screen_width - 20)
        btn_prev.clicked.connect(lambda: self._change_waveform(-1))
        btn_next.clicked.connect(lambda: self._change_waveform(+1))

        ctrl = QVBoxLayout()

        self.dial = self._make_knob(ctrl, "LEVEL", 50, 45, 45)
        self.dial.valueChanged.connect(self._sync)

        tuning_ctrl = QVBoxLayout()
        tuning_ctrl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.tuning_slider = QSlider(Qt.Orientation.Horizontal)
        self.tuning_slider.setFixedWidth(120)
        self.tuning_slider.setRange(200, 600)
        self.tuning_slider.setValue(440)
        self.tuning_slider.setSingleStep(5)
        self.tuning_slider.setStyleSheet(STYLE_SLIDER)
        self.tuning_slider.valueChanged.connect(self._sync)

        self.lbl_tuning_val = QLabel(f"{self.tuning} Hz")
        self.lbl_tuning_val.setStyleSheet("color: #555; font-size: 9px; font-weight: bold;")
        self.lbl_tuning_val.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_tuning = QLabel("TUNING")
        lbl_tuning.setStyleSheet("color: #555; font-size: 9px; font-weight: bold;")
        lbl_tuning.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tuning_ctrl.addStretch()
        tuning_ctrl.addWidget(lbl_tuning)
        tuning_ctrl.addWidget(self.tuning_slider, alignment=Qt.AlignmentFlag.AlignCenter)
        tuning_ctrl.addWidget(self.lbl_tuning_val)
        tuning_ctrl.addStretch()

        h_ctrl = QHBoxLayout()
        h_ctrl.addLayout(ctrl)
        h_ctrl.addLayout(tuning_ctrl)
        layout.addLayout(h_ctrl)

        self._sync()

    def _change_waveform(self, delta):
        # On change le label du type de waveform et on appelle _sync() pour redessiner le composant
        self.wf_index = (self.wf_index + delta) % len(self.wf_types)
        self.lbl_title.setText(self.wf_types[self.wf_index])
        self._sync()

    def _sync(self):
        # À chaque changement de configuration, on calcule le level en pourcentage et on affiche sur le label la valeur du tuning et on appelle _sync()
        self.level = self.dial.value() / 100.0
        self.tuning = self.tuning_slider.value()
        self.lbl_tuning_val.setText(f"{self.tuning} Hz")
        super()._sync()

    def _config(self) -> dict:
        # On retourne un dictionnaire avec le type de waveform sélectionné, le level en pourcentage et le tuning en Hz.
        return {
            "waveform": self.wf_types[self.wf_index].lower(),
            "level": self.level,
            "tuning": self.tuning,
        }

    # FONCTION GÉNÉRÉE PAR IA (très peu touchée) !!!
    def _draw(self):
        w, h = self.screen_width, self.screen_height

        pixmap = QPixmap(w, h)
        pixmap.fill(Qt.GlobalColor.transparent)

        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        x_vals = np.linspace(0, 2 * np.pi, w)
        wf = self.wf_types[self.wf_index]

        if wf == "SINE":
            y_vals = np.sin(x_vals)
        elif wf == "TRIANGLE":
            y_vals = (2 / np.pi) * np.arcsin(np.sin(x_vals))
        elif wf == "SAW":
            y_vals = (x_vals % (2 * np.pi)) / np.pi - 1
        else:  # SQUARE
            y_vals = np.sign(np.sin(x_vals))

        amplitude = self.level * h * WAVE_AMPLITUDE_RATIO
        points = [QPointF(i, h / 2 - y_vals[i] * amplitude) for i in range(w)]

        curve = QPainterPath()
        curve.addPolygon(QPolygonF(points))

        fill_path = QPainterPath()
        fill_path.addPolygon(QPolygonF(points))
        fill_path.lineTo(w, h / 2)
        fill_path.lineTo(0, h / 2)
        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.3, COLOR_CYAN_FILL)
        grad.setColorAt(0.7, QColor(0, 212, 255, 10))
        p.fillPath(fill_path, grad)

        p.setPen(QPen(COLOR_CYAN_GLOW, 4))
        p.drawPath(curve)

        p.setPen(QPen(COLOR_CYAN, 2))
        p.drawPath(curve)

        p.end()
        self.screen.setPixmap(pixmap)