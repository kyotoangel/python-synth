from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen

# ── config ────────────────────────────────────────────────────
WHITE_W = 24
WHITE_H = 80
BLACK_W = 14
BLACK_H = 50
N_OCTAVES = 5
START_OCTAVE = 2          # octave de départ (Do2 = midi 36)

COLOR_WHITE       = QColor("#e8e8e8")
COLOR_WHITE_HOVER = QColor("#b0eaff")
COLOR_WHITE_PRESS = QColor(0, 212, 255)
COLOR_BLACK       = QColor("#111")
COLOR_BLACK_HOVER = QColor("#1a7a99")
COLOR_BLACK_PRESS = QColor(0, 180, 220)
COLOR_BORDER      = QColor("#333")
COLOR_BG          = QColor("#070809")

# pattern des touches noires dans une octave (index relatif aux blanches)
# Do Ré Mi Fa Sol La Si  →  dièses entre 0-1, 1-2, 3-4, 4-5, 5-6
BLACK_PATTERN = [0, 1, 3, 4, 5]   # position de la blanche à gauche du dièse

# notes blanches dans une octave
WHITE_NOTES = [0, 2, 4, 5, 7, 9, 11]   # demi-tons depuis Do


def _build_keys(n_octaves, start_octave):
    """
    Retourne deux listes :
      whites : [(x, midi), ...]
      blacks  : [(x, midi), ...]
    """
    whites, blacks = [], []
    base_midi = (start_octave + 1) * 12   # Do du start_octave en MIDI

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
    """
    Clavier MIDI jouable à la souris.
    Émet note_on(midi) et note_off(midi).
    """

    note_on  = pyqtSignal(int)
    note_off = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._whites, self._blacks = _build_keys(N_OCTAVES, START_OCTAVE)
        total_w = N_OCTAVES * 7 * WHITE_W
        self.setFixedSize(total_w, WHITE_H + 16)
        self.setStyleSheet("background: transparent;")

        self._pressed  = None   # midi note actuellement enfoncée
        self._hovered  = None

        self.setMouseTracking(True)

    # ── hit-test ──────────────────────────────────────────────

    def _note_at(self, x, y):
        """Retourne le numéro MIDI sous le curseur, ou None."""
        # Les noires sont au-dessus → on les teste en premier
        if y < BLACK_H:
            for bx, midi in self._blacks:
                if bx <= x <= bx + BLACK_W:
                    return midi
        for wx, midi in self._whites:
            if wx <= x <= wx + WHITE_W:
                return midi
        return None

    # ── events souris ─────────────────────────────────────────

    def mousePressEvent(self, e):
        midi = self._note_at(int(e.position().x()), int(e.position().y()))
        if midi is not None:
            self._pressed = midi
            self.note_on.emit(midi)
            self.update()

    def mouseReleaseEvent(self, e):
        if self._pressed is not None:
            self.note_off.emit(self._pressed)
            self._pressed = None
            self.update()

    def mouseMoveEvent(self, e):
        midi = self._note_at(int(e.position().x()), int(e.position().y()))
        if midi != self._hovered:
            self._hovered = midi
            self.update()

    def leaveEvent(self, e):
        self._hovered = None
        self.update()

    # ── dessin ────────────────────────────────────────────────

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # fond
        p.fillRect(self.rect(), COLOR_BG)

        # touches blanches
        for x, midi in self._whites:
            if midi == self._pressed:
                color = COLOR_WHITE_PRESS
            elif midi == self._hovered:
                color = COLOR_WHITE_HOVER
            else:
                color = COLOR_WHITE
            p.fillRect(x, 8, WHITE_W - 1, WHITE_H, color)
            p.setPen(QPen(COLOR_BORDER, 1))
            p.drawRect(x, 8, WHITE_W - 1, WHITE_H)

        # touches noires (par-dessus)
        for x, midi in self._blacks:
            if midi == self._pressed:
                color = COLOR_BLACK_PRESS
            elif midi == self._hovered:
                color = COLOR_BLACK_HOVER
            else:
                color = COLOR_BLACK
            p.fillRect(x, 8, BLACK_W, BLACK_H, color)
            p.setPen(QPen(COLOR_BORDER, 1))
            p.drawRect(x, 8, BLACK_W, BLACK_H)

        p.end()