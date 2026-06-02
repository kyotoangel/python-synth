"""
base_component.py
─────────────────
Classe mère partagée par tous les widgets du synthé.
Centralise : dimensions, palette de couleurs, styles,
la structure écran/titre, les boutons fléchés et les dials.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QDial, QPushButton
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

# ── Dimensions par défaut ─────────────────────────────────────
WIDGET_WIDTH = 400
WIDGET_HEIGHT = 220
SCREEN_WIDTH = 384
SCREEN_HEIGHT = 130

# ── Palette commune ───────────────────────────────────────────
COLOR_CYAN = QColor(0, 212, 255)
COLOR_CYAN_GLOW = QColor(0, 212, 255, 80)
COLOR_CYAN_FILL = QColor(0, 212, 255, 60)

# ── Styles communs ────────────────────────────────────────────
STYLE_WIDGET = "background: #070809; border: none;"
STYLE_SCREEN = "background: black; border-radius: 8px; border: 1px solid #1a1a1a;"
STYLE_TITLE_LABEL = "color: #eee; font-size: 11px; font-weight: bold; background: transparent;"
STYLE_KNOB_LABEL = "color: #555; font-size: 9px; font-weight: bold;"
STYLE_DIAL = "background: #1a1a1a;"
STYLE_ARROW_BTN = """
    QPushButton       { color: #555; background: transparent; font-size: 14px; border: none; }
    QPushButton:hover { color: white; }
"""


class SynthComponent(QFrame):
    """
    Classe de base pour tous les composants du synthétiseur.

    Fournit :
      - taille fixe et style de fond standardisés
      - un QLabel `self.screen` avec titre centré (`self.lbl_title`)
      - `_make_screen(title)` pour construire l'écran
      - `_make_arrow(txt, x)` pour les boutons < / >
      - `_make_dial(layout, name, default)` (méthode d'instance)
      - signal `config_updated(dict)`
      - méthode `_sync()` à surcharger : appelle `_draw()` puis émet le signal
    """

    config_updated = pyqtSignal(dict)

    def __init__(
        self,
        widget_width: int = WIDGET_WIDTH,
        widget_height: int = WIDGET_HEIGHT,
        screen_width: int = SCREEN_WIDTH,
        screen_height: int = SCREEN_HEIGHT,
    ):
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
        Crée self.screen (QLabel noir arrondi) + self.lbl_title,
        et retourne le QLabel pour pouvoir l'ajouter au layout.
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
        Crée un bouton fléché (< ou >) positionné en absolu
        sur self.screen. Doit être appelé après _make_screen().
        """
        assert self.screen is not None, "_make_screen() must be called first"
        btn = QPushButton(txt, self.screen)
        btn.setGeometry(x, 0, 20, 17)
        btn.setStyleSheet(STYLE_ARROW_BTN)
        return btn

    def _make_dial(self, parent_layout, name: str, default: int = 0, w_size= 40, l_size= 40) -> QDial:
        """
        Crée un QDial de taille renseignée (default 40x40) avec son label au dessus,
        les insère dans un QVBoxLayout et l'ajoute à parent_layout.
        Retourne le QDial.
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

    def _sync(self):
        """
        À appeler à chaque changement d'un contrôle.
        Sous-classes : surcharger _draw() et _config(), pas _sync().
        """
        self._draw()
        self.config_updated.emit(self._config())

    def _draw(self):
        """Redessiner le contenu de self.screen."""
        raise NotImplementedError(f"{type(self).__name__} must implement _draw()")

    def _config(self) -> dict:
        """Retourner le dict de configuration courant."""
        raise NotImplementedError(f"{type(self).__name__} must implement _config()")