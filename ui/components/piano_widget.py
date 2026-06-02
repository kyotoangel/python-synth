from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen

# ── config ────────────────────────────────────────────────────
WHITE_W = 24
WHITE_H = 80
BLACK_W = 14
BLACK_H = 50
N_OCTAVES = 5
START_OCTAVE = 2

COLOR_WHITE = QColor("#e8e8e8")
COLOR_WHITE_HOVER = QColor("#b0eaff")
COLOR_WHITE_PRESS = QColor(0, 212, 255)
COLOR_BLACK = QColor("#111")
COLOR_BLACK_HOVER = QColor("#1a7a99")
COLOR_BLACK_PRESS = QColor(0, 180, 220)
COLOR_BORDER = QColor("#333")
COLOR_BG = QColor("#070809")

BLACK_PATTERN = [0, 1, 3, 4, 5]
WHITE_NOTES = [0, 2, 4, 5, 7, 9, 11]


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

    note_on = pyqtSignal(int)
    note_off = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self._whites, self._blacks = _build_keys(N_OCTAVES, START_OCTAVE)
        total_w = N_OCTAVES * 7 * WHITE_W
        self.setFixedSize(total_w, WHITE_H + 16)
        self.setStyleSheet("background: transparent;")

        self._pressed_mouse = None
        self._pressed_midi : set = set()

        self.setMouseTracking(True)

    def press_note(self, midi: int):
        self._pressed_midi.add(midi)
        self.update()

    def release_note(self, midi: int):
        self._pressed_midi.discard(midi)
        self.update()

    def release_all(self):
        self._pressed_midi.clear()
        self.update()

    def _note_at(self, x, y):
        if y < BLACK_H:
            for bx, midi in self._blacks:
                if bx <= x <= bx + BLACK_W:
                    return midi
        for wx, midi in self._whites:
            if wx <= x <= wx + WHITE_W:
                return midi
        return None

    def mousePressEvent(self, e):
        midi = self._note_at(int(e.position().x()), int(e.position().y()))
        if midi is not None:
            self._pressed_mouse = midi
            self.note_on.emit(midi)
            self.update()

    def mouseReleaseEvent(self, e):
        if self._pressed_mouse is not None:
            self.note_off.emit(self._pressed_mouse)
            self._pressed_mouse = None
            self.update()

    def mouseMoveEvent(self, e):
        self.update()

    def leaveEvent(self, e):
        self.update()

    def _is_pressed(self, midi):
        return midi == self._pressed_mouse or midi in self._pressed_midi

    def paintEvent(self, e):
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