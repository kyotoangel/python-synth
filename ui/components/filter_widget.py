import numpy as np
from PyQt6.QtWidgets import QHBoxLayout, QSlider, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QPainterPath, QLinearGradient, QColor, QPixmap
from PyQt6.QtCore import QPointF
from components.base_component import SynthComponent, COLOR_CYAN, COLOR_CYAN_GLOW, COLOR_CYAN_FILL, STYLE_SLIDER
from utils import lp_response, hp_response

WIDGET_HEIGHT: int = 250
SCREEN_HEIGHT: int = 160

class FilterWidget(SynthComponent):

    def __init__(self, freq_min: float = 20.0, freq_max: float = 20000.0):
        super().__init__(widget_height=WIDGET_HEIGHT, screen_height=SCREEN_HEIGHT)

        # Type de filtre disponible dans le composant (ici Passe Haut et Passe bas)
        self.filter_types = ["LOW PASS", "HIGH PASS"]
        self.filter_index = 0

        # Fréquence minimale et maximale du filtre
        self.freq_min = freq_min
        self.freq_max = freq_max

        # Cutoff du filtre en pourcentage
        self.cutoff_norm = 0.5
        # Cutoff du filtre en Hz
        self.cutoff = self._norm_to_frequency(self.cutoff_norm)

        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        screen_layout = QHBoxLayout()

        screen_layout.addWidget(self._make_screen(self.filter_types[self.filter_index]))

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

        self.lbl_cutoff_val = QLabel(f"{self.cutoff} Hz")
        self.lbl_cutoff_val.setStyleSheet("color: #555; font-size: 9px; font-weight: bold;")
        self.lbl_cutoff_val.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addLayout(screen_layout)
        layout.addWidget(self.lbl_cutoff_val)

        self._sync()

    def _change_type(self, delta: int) -> None:
        # On change le label du type de filtre et on appelle _sync() pour redessiner le composant
        self.filter_index = (self.filter_index + delta) % len(self.filter_types)
        self.lbl_title.setText(self.filter_types[self.filter_index])
        self._sync()

    def _sync(self) -> None:
        # À chaque changement de configuration du slider, on calcule le nouveau cutoff en Hz puis on l'affiche sur le label et on appelle _sync()
        self.cutoff_norm = self.slider.value() / 1000.0
        self.cutoff = self._norm_to_frequency(self.cutoff_norm)
        self.lbl_cutoff_val.setText(f"{self.cutoff} Hz")
        super()._sync()

    def _config(self) -> dict:
        # On retourne un dictionnaire avec le type de filtre sélectionné ansi que le cutoff en Hz.
        return {
            "filter_type": self.filter_types[self.filter_index].lower().replace(" ", "_"),
            "cutoff": self.cutoff,
        }

    def _norm_to_frequency(self, norm: float) -> int:
        # Permet de convertir le cutoff normalisé en cutoff de fréquence.
        return int(self.freq_min * (self.freq_max / self.freq_min) ** norm)

    # FONCTION GÉNÉRÉE PAR IA (pas du tout touchée) !!!
    def _draw(self) -> None:
        w = self.screen_width
        h = self.screen_height - 20
        y_off = 20

        frequencies = np.logspace(np.log10(self.freq_min), np.log10(self.freq_max), w)

        mag = (lp_response if self.filter_index == 0 else hp_response)(frequencies, self.cutoff)
        mag = np.clip(mag, 0, 1)

        pixmap = QPixmap(self.screen_width, self.screen_height)
        pixmap.fill(Qt.GlobalColor.transparent)

        p = QPainter(pixmap)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        pts = [QPointF(i, y_off + (1.0 - mag[i]) * (h - 4)) for i in range(w)]
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