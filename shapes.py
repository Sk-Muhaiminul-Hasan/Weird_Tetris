import random


SHAPES = {
    "SQUARE": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "T_SHAPE": [(0, 0), (-1, 0), (1, 0), (0, 1)],
    "L_SHAPE": [(0, 0), (0, -1), (0, 1), (1, 1)],
    "LINE": [(0, 0), (1, 0), (-1, 0), (2, 0)],
    "U_BEND": [(0, 0), (1, 0), (-1, 0), (-1, 1), (1, 1)],
}
SHAPE_ORDER = list(SHAPES.keys())

COLORS = {
    "SQUARE": (255, 213, 79),
    "T_SHAPE": (186, 85, 211),
    "L_SHAPE": (255, 140, 0),
    "LINE": (0, 191, 255),
    "U_BEND": (50, 205, 50),
}

GLITCH_COLOR = (255, 50, 50)


class Piece:
    def __init__(self):
        self.type = random.choice(SHAPE_ORDER)
        self.is_glitch = random.random() < 0.2
        self.set_type(self.type)

    def set_type(self, shape_type):
        self.type = shape_type
        self.coords = list(SHAPES[self.type])
        self.color = GLITCH_COLOR if self.is_glitch else COLORS[self.type]

    def cycle_shape(self):
        index = SHAPE_ORDER.index(self.type)
        self.set_type(SHAPE_ORDER[(index + 1) % len(SHAPE_ORDER)])

    def rotate(self):
        if not self.is_glitch:
            self.coords = [(-y, x) for (x, y) in self.coords]


def next_piece():
    return Piece()
