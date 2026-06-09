"""
base_component.py
─────────────────
Classe mère SynthComponent dont héritent tous les widgets du synthétiseur.
Centralise les dimensions, couleurs, styles CSS et helpers UI communs.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QDial, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

# Dimension par défaut d'un composant
DEFAULT_WIDGET_WIDTH: int = 400
DEFAULT_WIDGET_HEIGHT: int = 220
DEFAULT_SCREEN_WIDTH: int = 384
DEFAULT_SCREEN_HEIGHT: int = 130

# Palette de couleur par défaut (nous avons choisi le cyan en l'occurence)
COLOR_CYAN: QColor = QColor(0, 212, 255)
COLOR_CYAN_GLOW: QColor = QColor(0, 212, 255, 80)
COLOR_CYAN_FILL: QColor = QColor(0, 212, 255, 60)

# CSS par défaut appliqué à chaque composant
STYLE_WIDGET: str = "background: #070809; border: none;"
STYLE_SCREEN: str = "background: black; border-radius: 8px; border: 1px solid #1a1a1a;"
STYLE_TITLE_LABEL: str = "color: #eee; font-size: 11px; font-weight: bold; background: transparent;"
STYLE_KNOB_LABEL: str = "color: #555; font-size: 9px; font-weight: bold;"
STYLE_DIAL: str = "background: #1a1a1a;"
STYLE_ARROW_BTN: str = """
    QPushButton       { color: #555; background: transparent; font-size: 14px; border: none; }
    QPushButton:hover { color: white; }
"""
STYLE_SLIDER: str = """
    QSlider::groove:horizontal { background: #1a1a1a; height: 4px; border-radius: 2px; }
    QSlider::handle:horizontal { background: #00d4ff; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }
    QSlider::sub-page:horizontal { background: #00d4ff; height: 4px; border-radius: 2px; }
"""

class SynthComponent(QFrame):
    """
    Classe mère pour chaque composants du synthétiseur, chaque composant va hériter de cette classe.

    Cette classe définit par défaut :
      - Une taille fixe (hauteur et largeur) et un style CSS (tout deux définis un peu plus haut)
      - Un QLabel `self.screen` avec titre centré `self.lbl_title` qui permet d'avoir un écran titré pour tracer les graphiques
      - Une fonction _make_screen qui permet de créer l'écran avec le titre
      - Une fonction make_arrow qui permet de générer automatiquement des flèches dans les coin du screen si besoin
      - Une fonction make_knob qui permet de créer automatiquement des dials qui sont utilisées dans les composants
      - Un signal PyQt pour notifier les changements de configuration du composant
      - Un fonction _sync qui permet de redessiner le composant et de notifier le signal à chaque modification du composant
            en appelant _draw() et _config() qui doivent être surchargé dans les sous-classes
    """

    config_updated = pyqtSignal(dict)

    def __init__(self, widget_width: int = DEFAULT_WIDGET_WIDTH, widget_height: int = DEFAULT_WIDGET_HEIGHT, screen_width: int = DEFAULT_SCREEN_WIDTH, screen_height: int = DEFAULT_SCREEN_HEIGHT):
        super().__init__()
        self.widget_width = widget_width
        self.widget_height = widget_height
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.setFixedSize(widget_width, widget_height)
        self.setStyleSheet(STYLE_WIDGET)

        self.screen: QLabel | None = None
        self.lbl_title: QLabel | None = None

    def _make_screen(self, title: str = "") -> QLabel:
        """
        Créer le screen du composant sur lequel on va dessiner les graphiques.

        :param str title: Le titre du screen (c'est à dire le nom du composant).
        :return: L'écran QLabel.
        """
        self.screen = QLabel()
        self.screen.setFixedSize(self.screen_width, self.screen_height)
        self.screen.setStyleSheet(STYLE_SCREEN)

        self.lbl_title = QLabel(title, self.screen)
        self.lbl_title.setGeometry(0, 0, self.screen_width, 20)
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setStyleSheet(STYLE_TITLE_LABEL)

        return self.screen

    def _make_arrow(self, txt: str, x: int) -> QPushButton:
        """
        Permet de créer des flèches cliquables dans les coins du screen. (codé en position absolue)
        Cette fonction doit être appelé après _make_screen() puisqu'il faut un écran sur lequel desinné.

        :param str txt: Le texte qui sera affiché sur le bouton en l'occurence soit "<" soit ">".
        :param int x: La position absolue du bouton sur l'axe x.

        :return: Le bouton cliquable QPushButton.
        """
        assert self.screen is not None, "_make_screen() doit être appelé avant _make_arrow()"
        btn = QPushButton(txt, self.screen)
        btn.setGeometry(x, 0, 20, 17)
        btn.setStyleSheet(STYLE_ARROW_BTN)
        return btn

    def _make_knob(self, parent_layout: QVBoxLayout | QHBoxLayout, name: str, default: int = 0, w_size: int= 40, l_size: int= 40) -> QDial:
        """

        Crée un QDial de taille renseignée (default 40x40) avec son label au-dessus puis les insère dans un QVBoxLayout et l'ajoute à parent_layout.

        :param parent_layout: Un layout PyQt qui va accueillir le knob et son label (QVBoxLayout ou QHBoxLayout).
        :param str name: Le nom du knob.
        :param int default: Valeur par défaut du knob lorsqu'il est créé.
        :param w_size: Valeur de la largeur du knob.
        :param l_size: Valeur de la hauteur du knob.
        :return: Le knob QDial.
        """
        col = QVBoxLayout()
        col.setSpacing(2)

        dial = QDial()
        dial.setFixedSize(w_size, l_size)
        dial.setValue(default)
        dial.setStyleSheet(STYLE_DIAL)

        lbl = QLabel(name)
        lbl.setStyleSheet(STYLE_KNOB_LABEL)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        col.addStretch()
        col.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addWidget(dial, alignment=Qt.AlignmentFlag.AlignHCenter)
        col.addStretch()

        parent_layout.addLayout(col)
        return dial

    def _sync(self) -> None:
        """
        Une fonction qui est appelée à chaque modification du composant pour redessiner le composant et notifier le signal.
        """
        self._draw()
        self.config_updated.emit(self._config())

    def _draw(self) -> None:
        """Redessiner le contenu de self.screen."""
        raise NotImplementedError(f"{type(self).__name__} doit avoir une fonction _draw() implémentée !")

    def _config(self) -> dict:
        """Retourner le dict de la configuration actuelle du composant."""
        raise NotImplementedError(f"{type(self).__name__} doit avoir une fonction _config() implémentée !")