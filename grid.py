class Playfield:
    def __init__(self, size=16):
        self.size = size
        self.matrix = [[0] * size for _ in range(size)]
        self.colors = [[None] * size for _ in range(size)]
        self.w_left = 0.0
        self.w_right = float(size)
        self.w_top = 0.0
        self.w_bottom = float(size)

    def is_colliding(self, cx, cy, piece_coords):
        for (px, py) in piece_coords:
            tx, ty = cx + px, cy + py
            if tx < 0 or tx >= self.size or ty < 0 or ty >= self.size:
                return True
            if tx < int(self.w_left) or tx >= int(self.w_right):
                return True
            if ty < int(self.w_top) or ty >= int(self.w_bottom):
                return True
            if self.matrix[ty][tx] == 1:
                return True
        return False

    def place_piece(self, cx, cy, piece_coords, color):
        for (px, py) in piece_coords:
            tx, ty = cx + px, cy + py
            self.matrix[ty][tx] = 1
            self.colors[ty][tx] = color

    def cell_touches_walls(self, x, y):
        return (
            x <= self.w_left <= x + 1
            or x <= self.w_right <= x + 1
            or y <= self.w_top <= y + 1
            or y <= self.w_bottom <= y + 1
        )

    def occupied_touches_walls(self):
        for y in range(self.size):
            for x in range(self.size):
                if self.matrix[y][x] == 1 and self.cell_touches_walls(x, y):
                    return True
        return False

    def piece_touches_walls(self, cx, cy, piece_coords):
        for (px, py) in piece_coords:
            tx, ty = cx + px, cy + py
            if tx < 0 or tx >= self.size or ty < 0 or ty >= self.size:
                return True
            if self.cell_touches_walls(tx, ty):
                return True
        return False

    def expand_walls(self, amount=1.0):
        self.w_left = max(0.0, self.w_left - amount)
        self.w_right = min(float(self.size), self.w_right + amount)
        self.w_top = max(0.0, self.w_top - amount)
        self.w_bottom = min(float(self.size), self.w_bottom + amount)

    def clear_boxes(self, box_size=3):
        boxes = []
        left = int(self.w_left)
        right = int(self.w_right)
        top = int(self.w_top)
        bottom = int(self.w_bottom)

        for y in range(top, bottom - box_size + 1):
            for x in range(left, right - box_size + 1):
                full_box = True
                for by in range(y, y + box_size):
                    for bx in range(x, x + box_size):
                        if self.matrix[by][bx] != 1:
                            full_box = False
                            break
                    if not full_box:
                        break
                if full_box:
                    boxes.append((x, y))

        selected_boxes = []
        cells_to_clear = set()
        for x, y in boxes:
            box_cells = {
                (bx, by)
                for by in range(y, y + box_size)
                for bx in range(x, x + box_size)
            }
            if not cells_to_clear.intersection(box_cells):
                selected_boxes.append((x, y))
                cells_to_clear.update(box_cells)

        for x, y in cells_to_clear:
            self.matrix[y][x] = 0
            self.colors[y][x] = None

        for _ in selected_boxes:
            self.expand_walls()

        return len(selected_boxes)

    def clear_lines(self):
        cleared = 0
        left = int(self.w_left)
        right = int(self.w_right)
        top = int(self.w_top)
        bottom = int(self.w_bottom)

        for row in range(top, bottom):
            if all(self.matrix[row][col] == 1 for col in range(left, right)):
                self.matrix[row] = [0] * self.size
                self.colors[row] = [None] * self.size
                self.w_left = max(0.0, self.w_left - 0.5)
                self.w_right = min(float(self.size), self.w_right + 0.5)
                cleared += 1

        return cleared
