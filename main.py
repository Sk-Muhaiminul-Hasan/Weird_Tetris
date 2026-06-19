import math
import os

import pygame

from engine import GameEngine
from grid import Playfield
from shapes import next_piece

try:
    import psycopg
except ImportError:
    psycopg = None


WINDOW_W, WINDOW_H = 600, 680
GRID_OFFSET_X, GRID_OFFSET_Y = 40, 80
CELL_SIZE = 32
FPS = 60
BG_COLOR = (15, 15, 25)
GRID_BG_COLOR = (25, 25, 40)
WALL_COLOR = (220, 60, 60)
TEXT_COLOR = (235, 235, 245)
DB_URL = (
    os.environ.get("CONTINENTAL_DRIFT_DB_URL")
    or os.environ.get("DATABASE_URL")
    or "postgresql://localhost/continental_drift"
)

pygame.init()
screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
pygame.display.set_caption("Continental Drift")
clock = pygame.time.Clock()
font_large = pygame.font.SysFont("monospace", 28, bold=True)
font_small = pygame.font.SysFont("monospace", 16)

playfield = None
engine = None
current_piece = None
next_p = None
piece_x = 8
piece_y = 8
player_name = ""
entering_name = True
score_saved = False
db_ready = False
db_status = "DB: not checked"
float_time = 0.0


def reset_game():
    global playfield, engine, current_piece, next_p, piece_x, piece_y, score_saved
    playfield = Playfield()
    engine = GameEngine()
    current_piece = next_piece()
    next_p = next_piece()
    score_saved = False
    move_piece_to_spawn()


def init_database():
    global db_ready, db_status
    if psycopg is None:
        db_ready = False
        db_status = "DB: install psycopg"
        return

    try:
        with psycopg.connect(DB_URL, connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS scores (
                        id BIGSERIAL PRIMARY KEY,
                        username TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                )
        db_ready = True
        db_status = "DB: ready"
    except Exception as exc:
        db_ready = False
        db_status = f"DB: offline ({exc.__class__.__name__})"


def save_score_once():
    global score_saved, db_status
    if score_saved or entering_name:
        return

    score_saved = True
    if not db_ready:
        init_database()
    if not db_ready:
        return

    username = (player_name.strip() or "Player")[:32]
    try:
        with psycopg.connect(DB_URL, connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO scores (username, score) VALUES (%s, %s)",
                    (username, engine.score),
                )
        db_status = "DB: score saved"
    except Exception as exc:
        db_status = f"DB: save failed ({exc.__class__.__name__})"


def grid_to_screen(gx, gy):
    return (GRID_OFFSET_X + gx * CELL_SIZE, GRID_OFFSET_Y + gy * CELL_SIZE)


def darken(color, amount=45):
    return tuple(max(0, channel - amount) for channel in color)


def draw_cell(surface, gx, gy, color, alpha=None, scale=CELL_SIZE):
    sx, sy = grid_to_screen(gx, gy)
    rect = pygame.Rect(sx + 1, sy + 1, scale - 2, scale - 2)
    draw_color = color if alpha is None else (*color, alpha)
    border_color = darken(color) if alpha is None else (*darken(color), alpha)
    pygame.draw.rect(surface, draw_color, rect)
    pygame.draw.rect(surface, border_color, rect, 1)


def draw_hud():
    score_text = font_small.render(f"SCORE: {engine.score}", True, TEXT_COLOR)
    level_text = font_small.render(f"LEVEL: {engine.level}", True, TEXT_COLOR)
    next_text = font_small.render("NEXT:", True, TEXT_COLOR)
    db_text = font_small.render(db_status, True, (165, 185, 205))
    screen.blit(score_text, (40, 26))
    screen.blit(level_text, (215, 26))
    screen.blit(next_text, (405, 26))
    screen.blit(db_text, (40, 52))
    draw_preview_piece(next_p)


def draw_preview_piece(piece):
    preview_size = 14
    preview_origin_x = 506
    preview_origin_y = 20
    min_x = min(x for x, _ in piece.coords)
    max_x = max(x for x, _ in piece.coords)
    min_y = min(y for _, y in piece.coords)
    max_y = max(y for _, y in piece.coords)
    width = (max_x - min_x + 1) * preview_size
    height = (max_y - min_y + 1) * preview_size
    start_x = preview_origin_x - width // 2
    start_y = preview_origin_y + (44 - height) // 2

    for px, py in piece.coords:
        rect = pygame.Rect(
            start_x + (px - min_x) * preview_size,
            start_y + (py - min_y) * preview_size,
            preview_size - 1,
            preview_size - 1,
        )
        pygame.draw.rect(screen, piece.color, rect)
        pygame.draw.rect(screen, darken(piece.color), rect, 1)


def draw_grid_background():
    x = GRID_OFFSET_X + playfield.w_left * CELL_SIZE
    y = GRID_OFFSET_Y + playfield.w_top * CELL_SIZE
    width = (playfield.w_right - playfield.w_left) * CELL_SIZE
    height = (playfield.w_bottom - playfield.w_top) * CELL_SIZE
    pygame.draw.rect(screen, GRID_BG_COLOR, pygame.Rect(x, y, width, height))

    for index in range(playfield.size + 1):
        line_x = GRID_OFFSET_X + index * CELL_SIZE
        line_y = GRID_OFFSET_Y + index * CELL_SIZE
        pygame.draw.line(
            screen,
            (35, 35, 52),
            (line_x, GRID_OFFSET_Y),
            (line_x, GRID_OFFSET_Y + playfield.size * CELL_SIZE),
        )
        pygame.draw.line(
            screen,
            (35, 35, 52),
            (GRID_OFFSET_X, line_y),
            (GRID_OFFSET_X + playfield.size * CELL_SIZE, line_y),
        )


def draw_placed_cells():
    for y in range(playfield.size):
        for x in range(playfield.size):
            if playfield.matrix[y][x] == 1:
                draw_cell(screen, x, y, playfield.colors[y][x])


def draw_piece(piece, x, y):
    for px, py in piece.coords:
        draw_cell(screen, x + px, y + py, piece.color)


def draw_piece_floating(piece, x, y):
    """Draw the active piece with a floating bob, drop shadow, and glow.
    Shows a red tint when the current position is invalid (can't place there)."""
    bob = int(math.sin(float_time * 2.8) * 5)  # ±5 px vertical bob
    placeable = not playfield.is_colliding(x, y, piece.coords)

    # Colour switches to red when hovering over an occupied / out-of-bounds cell
    display_color = piece.color if placeable else (220, 60, 70)
    cell_alpha = 255 if placeable else 150

    for px, py in piece.coords:
        sx, sy = grid_to_screen(x + px, y + py)
        float_y = sy - bob

        # --- Drop shadow (stays at grid position, doesn't bob) ---
        shadow_alpha = 65 if placeable else 25
        shadow_surf = pygame.Surface((CELL_SIZE - 2, CELL_SIZE - 2), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, shadow_alpha))
        screen.blit(shadow_surf, (sx + 4, sy + 6))

        # --- Soft glow outline ---
        glow_color = tuple(min(255, c + 55) for c in display_color)
        glow_alpha = 45 if placeable else 90
        glow_surf = pygame.Surface((CELL_SIZE + 6, CELL_SIZE + 6), pygame.SRCALPHA)
        glow_surf.fill((*glow_color, glow_alpha))
        screen.blit(glow_surf, (sx - 3, float_y - 3))

        # --- Main cell body (bobbing, alpha-blended) ---
        cell_surf = pygame.Surface((CELL_SIZE - 2, CELL_SIZE - 2), pygame.SRCALPHA)
        cell_surf.fill((*display_color, cell_alpha))
        screen.blit(cell_surf, (sx + 1, float_y + 1))

        border_color = darken(display_color)
        border_surf = pygame.Surface((CELL_SIZE - 2, CELL_SIZE - 2), pygame.SRCALPHA)
        pygame.draw.rect(
            border_surf,
            (*border_color, cell_alpha),
            pygame.Rect(0, 0, CELL_SIZE - 2, CELL_SIZE - 2),
            1,
        )
        screen.blit(border_surf, (sx + 1, float_y + 1))

        if placeable:
            # Bright top-edge highlight for 3-D lifted look
            highlight_color = tuple(min(255, c + 90) for c in piece.color)
            highlight_rect = pygame.Rect(sx + 2, float_y + 2, CELL_SIZE - 4, 3)
            pygame.draw.rect(screen, highlight_color, highlight_rect)


def draw_walls():
    left = GRID_OFFSET_X + playfield.w_left * CELL_SIZE
    right = GRID_OFFSET_X + playfield.w_right * CELL_SIZE
    top = GRID_OFFSET_Y + playfield.w_top * CELL_SIZE
    bottom = GRID_OFFSET_Y + playfield.w_bottom * CELL_SIZE

    pygame.draw.line(screen, WALL_COLOR, (left, top), (left, bottom), 4)
    pygame.draw.line(screen, WALL_COLOR, (right, top), (right, bottom), 4)
    pygame.draw.line(screen, WALL_COLOR, (left, top), (right, top), 4)
    pygame.draw.line(screen, WALL_COLOR, (left, bottom), (right, bottom), 4)


def draw_game_over():
    overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 165))
    screen.blit(overlay, (0, 0))

    title = font_large.render("GAME OVER", True, (255, 255, 255))
    final_score = font_small.render(f"Final score: {engine.score}", True, TEXT_COLOR)
    player = font_small.render(f"Player: {player_name or 'Player'}", True, TEXT_COLOR)
    db_text = font_small.render(db_status, True, (190, 210, 225))
    restart = font_small.render("Press R to restart", True, TEXT_COLOR)
    screen.blit(title, title.get_rect(center=(WINDOW_W // 2, 300)))
    screen.blit(player, player.get_rect(center=(WINDOW_W // 2, 336)))
    screen.blit(final_score, final_score.get_rect(center=(WINDOW_W // 2, 364)))
    screen.blit(db_text, db_text.get_rect(center=(WINDOW_W // 2, 392)))
    screen.blit(restart, restart.get_rect(center=(WINDOW_W // 2, 424)))


def draw_name_prompt():
    screen.fill(BG_COLOR)
    title = font_large.render("CONTINENTAL DRIFT", True, (255, 255, 255))
    label = font_small.render("Enter player name", True, TEXT_COLOR)
    name = player_name if player_name else "Player"
    name_text = font_large.render(name, True, (255, 213, 79))
    start = font_small.render("Press Enter to start", True, TEXT_COLOR)
    db_text = font_small.render(db_status, True, (165, 185, 205))
    input_rect = pygame.Rect(150, 292, 300, 52)

    screen.blit(title, title.get_rect(center=(WINDOW_W // 2, 220)))
    screen.blit(label, label.get_rect(center=(WINDOW_W // 2, 270)))
    pygame.draw.rect(screen, GRID_BG_COLOR, input_rect)
    pygame.draw.rect(screen, WALL_COLOR, input_rect, 2)
    screen.blit(name_text, name_text.get_rect(center=input_rect.center))
    screen.blit(start, start.get_rect(center=(WINDOW_W // 2, 378)))
    screen.blit(db_text, db_text.get_rect(center=(WINDOW_W // 2, 408)))


def draw_everything():
    if entering_name:
        draw_name_prompt()
        return

    screen.fill(BG_COLOR)
    draw_grid_background()
    draw_placed_cells()
    if engine.game_active:
        draw_piece_floating(current_piece, piece_x, piece_y)
    draw_walls()
    draw_hud()
    if not engine.game_active:
        draw_game_over()


def candidate_positions(piece):
    left = int(playfield.w_left)
    right = int(playfield.w_right)
    top = int(playfield.w_top)
    bottom = int(playfield.w_bottom)
    center_x = (left + right) // 2
    center_y = (top + bottom) // 2
    positions = []

    for y in range(top, bottom):
        for x in range(left, right):
            if not playfield.is_colliding(x, y, piece.coords):
                distance = abs(x - center_x) + abs(y - center_y)
                positions.append((distance, x, y))

    positions.sort()
    return positions


def move_piece_to_spawn():
    """Spawn the piece at the visual centre of the active playfield.
    The player must deliberately navigate it to an empty slot to place it."""
    global piece_x, piece_y
    left = int(playfield.w_left)
    right = int(playfield.w_right)
    top = int(playfield.w_top)
    bottom = int(playfield.w_bottom)
    piece_x = (left + right) // 2
    piece_y = (top + bottom) // 2


def keep_piece_valid():
    """Floating over occupied/wall cells is intentionally allowed.
    Only placed cells touching shrinking walls end the game."""
    pass  # game-over is handled exclusively by check_wall_touch_game_over


def check_wall_touch_game_over():
    """Game over only when already-placed cells are crushed by the shrinking walls.
    The floating piece can hover anywhere without ending the game."""
    if playfield.occupied_touches_walls():
        engine.game_active = False


def try_move_piece(dx, dy):
    """Move freely — no collision block so the piece is never stranded on top of
    another block. Placement collision is checked separately in lock_piece."""
    global piece_x, piece_y
    next_x = piece_x + dx
    next_y = piece_y + dy
    # Only clamp to outer grid bounds so the piece stays on-screen
    if 0 <= next_x < playfield.size and 0 <= next_y < playfield.size:
        piece_x = next_x
        piece_y = next_y


def try_move_piece_to_grid(gx, gy):
    """Always follow the cursor — collision is only checked at placement (lock_piece).
    This prevents the piece from freezing at a 'last valid' spot that the player
    can exploit by spamming Enter."""
    global piece_x, piece_y
    piece_x = gx
    piece_y = gy
    return True


def cycle_current_piece():
    current_piece.cycle_shape()
    if playfield.is_colliding(piece_x, piece_y, current_piece.coords):
        move_piece_to_spawn()


def screen_to_grid(pos):
    mx, my = pos
    gx = (mx - GRID_OFFSET_X) // CELL_SIZE
    gy = (my - GRID_OFFSET_Y) // CELL_SIZE
    if gx < 0 or gx >= playfield.size or gy < 0 or gy >= playfield.size:
        return None
    return int(gx), int(gy)


def lock_piece():
    global current_piece, next_p
    if playfield.is_colliding(piece_x, piece_y, current_piece.coords):
        return

    playfield.place_piece(piece_x, piece_y, current_piece.coords, current_piece.color)
    boxes = playfield.clear_boxes()
    engine.add_score(boxes)
    engine.check_level_up()
    if playfield.occupied_touches_walls():
        engine.game_active = False
        return
    current_piece = next_p
    next_p = next_piece()
    move_piece_to_spawn()


def handle_input(event):
    global entering_name, player_name

    if event.type == pygame.QUIT:
        return False

    if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
        return False

    if entering_name:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                player_name = (player_name.strip() or "Player")[:32]
                entering_name = False
                reset_game()
            elif event.key == pygame.K_BACKSPACE:
                player_name = player_name[:-1]
            elif event.unicode and event.unicode.isprintable() and len(player_name) < 32:
                player_name += event.unicode
        return True

    if event.type == pygame.MOUSEMOTION and engine.game_active:
        grid_pos = screen_to_grid(event.pos)
        if grid_pos is not None:
            try_move_piece_to_grid(*grid_pos)
        return True

    if event.type == pygame.MOUSEBUTTONDOWN and engine.game_active:
        grid_pos = screen_to_grid(event.pos)
        if grid_pos is not None and try_move_piece_to_grid(*grid_pos):
            lock_piece()
        return True

    if event.type != pygame.KEYDOWN:
        return True

    if not engine.game_active:
        if event.key == pygame.K_r:
            reset_game()
        return True

    if event.key == pygame.K_LEFT:
        try_move_piece(-1, 0)
    elif event.key == pygame.K_RIGHT:
        try_move_piece(1, 0)
    elif event.key == pygame.K_UP:
        try_move_piece(0, -1)
    elif event.key == pygame.K_DOWN:
        try_move_piece(0, 1)
    elif event.key == pygame.K_f:
        current_piece.rotate()
        if playfield.is_colliding(piece_x, piece_y, current_piece.coords):
            current_piece.rotate()
            current_piece.rotate()
            current_piece.rotate()
    elif event.key == pygame.K_e:
        cycle_current_piece()
    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
        lock_piece()

    return True


def main():
    global float_time
    init_database()
    reset_game()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if not handle_input(event):
                running = False

        if engine.game_active and not entering_name:
            float_time += dt
            engine.process_level_behavior(playfield, dt)
            keep_piece_valid()
            check_wall_touch_game_over()

        if not engine.game_active:
            save_score_once()

        draw_everything()
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
