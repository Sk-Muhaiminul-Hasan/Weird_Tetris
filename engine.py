class GameEngine:
    def __init__(self):
        self.score = 0
        self.level = 1
        self.game_active = True
        self._time_acc = 0.0

    def process_level_behavior(self, playfield, dt):
        base = 0.12 + (self.level * 0.03)

        if self.level == 1:
            playfield.w_left += base * dt
            playfield.w_right -= base * dt
            playfield.w_top += base * dt
            playfield.w_bottom -= base * dt
        elif self.level == 2:
            self._time_acc += dt
            if self._time_acc >= 3.0:
                self._time_acc -= 3.0
                playfield.w_left = min(playfield.w_left + 1, playfield.w_right - 2)
                playfield.w_right = max(playfield.w_right - 1, playfield.w_left + 2)
                playfield.w_top = min(playfield.w_top + 1, playfield.w_bottom - 2)
                playfield.w_bottom = max(playfield.w_bottom - 1, playfield.w_top + 2)
        elif self.level == 3:
            playfield.w_left += base * dt
            playfield.w_right -= base * dt

        if (playfield.w_right - playfield.w_left <= 2) or (
            playfield.w_bottom - playfield.w_top <= 2
        ):
            self.game_active = False

    def add_score(self, lines_cleared):
        points = [0, 100, 300, 500, 800]
        self.score += points[min(lines_cleared, 4)] * self.level

    def check_level_up(self):
        new_level = min(3, 1 + self.score // 500)
        self.level = new_level
