from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen

# CONFIGURATION DES TOUCHES DU CLAVIER (ne pas toucher, j'ai mis longtemps à trouver des valeurs qui rendent bien !!)
WHITE_W: int = 24
WHITE_H: int = 80
BLACK_W: int = 14
BLACK_H: int = 50
N_OCTAVES: int = 5 # Modulable en théorie, mais cela casserait un peu le design global du synthé
START_OCTAVE: int = 2 # À quelle octave commencer les touches (plus on augmente plus c'est aigu et inversement)

# CONFIGURATION DES COULEURS (si on veut un clavier un peu plus funky)
COLOR_WHITE = QColor("#e8e8e8")
COLOR_WHITE_HOVER = QColor("#b0eaff")
COLOR_WHITE_PRESS = QColor(0, 212, 255)
COLOR_BLACK = QColor("#111")
COLOR_BLACK_HOVER = QColor("#1a7a99")
COLOR_BLACK_PRESS = QColor(0, 180, 220)
COLOR_BORDER = QColor("#333")
COLOR_BG = QColor("#070809")

# CONFIGURATION DES NOTES (ne pas toucher !!)
BLACK_PATTERN = [0, 1, 3, 4, 5]
WHITE_NOTES = [0, 2, 4, 5, 7, 9, 11]

# FONCTION GÉNÉRÉE PAR IA (pas du tout touchée) !!!
def _build_keys(n_octaves, start_octave):
    whites, blacks = [], []
    base_midi = (start_octave + 1) * 12

    for octave in range(n_octaves):
        oct_x = octave * 7 * WHITE_W
        for i, semitone in enumerate(WHITE_NOTES):
            midi = base_midi + octave * 12 + semitone
            whites.append((oct_x + i * WHITE_W, midi))
        for bi in BLACK_PATTERN:
            midi = base_midi + octave * 12 + WHITE_NOTES[bi] + 1
            x = oct_x + bi * WHITE_W + WHITE_W - BLACK_W // 2
            blacks.append((x, midi))

    return whites, blacks


class PianoWidget(QWidget):

    # Les deux signaux qui vont nous permettre de nous connecter avec les entrées MIDI (clavier et fichier).
    note_on = pyqtSignal(int)
    note_off = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._whites, self._blacks = _build_keys(N_OCTAVES, START_OCTAVE)
        total_w = N_OCTAVES * 7 * WHITE_W
        self.setFixedSize(total_w, WHITE_H + 16)
        self.setStyleSheet("background: transparent;")

        self._pressed_mouse = None
        # De type set, car on ne peut pas appuyer sur une touche qui est déjà appuyée (limitation de notre système que l'on aimerait améliorer)
        self._pressed_midi : set = set()

        # On active le fait de pouvoir appuyer sur les notes avec la souris.
        self.setMouseTracking(True)

    def press_note(self, midi: int):
        self._pressed_midi.add(midi)
        self.update()

    def release_note(self, midi: int):
        self._pressed_midi.discard(midi)
        self.update()

    def pressed_notes(self) -> set:
        # Renvoie toutes les notes actuellement pressées.
        return set(self._pressed_midi)

    def release_all(self):
        # Supprime toutes les touches appuyées du set.
        self._pressed_midi.clear()
        self.update()

    def _note_at(self, x, y):
        # Permet de recupérer la valeur (midi) de la touche positionnée en (x,y).
        if y < BLACK_H:
            for bx, midi in self._blacks:
                if bx <= x <= bx + BLACK_W:
                    return midi
        for wx, midi in self._whites:
            if wx <= x <= wx + WHITE_W:
                return midi
        return None

    def mousePressEvent(self, e):
        # Lorsque l'on clique sur une touche, on active la note au travers du signal note_on.
        midi = self._note_at(int(e.position().x()), int(e.position().y()))
        if midi is not None:
            self._pressed_mouse = midi
            self.note_on.emit(midi)
            self.update()

    def mouseReleaseEvent(self, e) -> None:
        # Lorsque l'on relâche le click sur une touche, on désactive la note au travers du signal note_off.
        if self._pressed_mouse is not None:
            self.note_off.emit(self._pressed_mouse)
            self._pressed_mouse = None
            self.update()

    def _is_pressed(self, midi) -> bool:
        return midi == self._pressed_mouse or midi in self._pressed_midi

    def paintEvent(self, e):
        # Appellé automatiquement lors du self.update()
        # On dessine les touches du clavier, si elles sont pressées alors on change leur couleur pour le montrer.
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), COLOR_BG)

        for x, midi in self._whites:
            color = COLOR_WHITE_PRESS if self._is_pressed(midi) else COLOR_WHITE
            p.fillRect(x, 8, WHITE_W - 1, WHITE_H, color)
            p.setPen(QPen(COLOR_BORDER, 1))
            p.drawRect(x, 8, WHITE_W - 1, WHITE_H)

        for x, midi in self._blacks:
            color = COLOR_BLACK_PRESS if self._is_pressed(midi) else COLOR_BLACK
            p.fillRect(x, 8, BLACK_W, BLACK_H, color)
            p.setPen(QPen(COLOR_BORDER, 1))
            p.drawRect(x, 8, BLACK_W, BLACK_H)

        p.end()