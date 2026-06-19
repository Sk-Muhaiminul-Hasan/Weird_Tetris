# AGENTS.md

## Project Overview
**Continental Drift** is a Pygame-based twist on Tetris. 
Instead of pieces falling vertically and filling rows, the playfield boundaries (walls) constantly collapse/shrink inward. Clearing rows has been replaced with completing **3x3 blocks** of placed cells. When a 3x3 block is filled, it is cleared, and the playfield expands back outward. 

---

## Technical Stack & Entry Point
- **Language**: Python 3
- **Graphics Library**: `pygame`
- **Database**: PostgreSQL (via `psycopg` to store user highscores optional/fallback to offline state)
- **Entry Point**: `python main.py`

---

## Key Files & Architecture

### 1. `main.py`
- Handles the core application loop, Pygame screen setup, frame rates, rendering, HUD, input handling, and database interaction.
- **Floating Mechanic**: Active piece rendering handles custom floating animations (bobbing using `math.sin` on `float_time`, drop shadow, and glow effects) until the piece is clicked or committed.

### 2. `grid.py` (`Playfield`)
- Implements the grid logic, matrix size (16x16 grid), and shrinking boundary offsets (`w_left`, `w_right`, `w_top`, `w_bottom`).
- Collision checks (`is_colliding`), wall collision checks, and 3x3 box detection & clearing logic (`clear_boxes`). When a 3x3 box clears, walls expand.

### 3. `engine.py` (`GameEngine`)
- Manages state machine tracking for game speed, scores, difficulty levels (1 to 3), and level-specific wall contraction behavior (`process_level_behavior`).
  - **Level 1**: Smooth continuous contraction inward on all sides.
  - **Level 2**: Stepped contraction every 3 seconds.
  - **Level 3**: Horizontal-only continuous contraction.

### 4. `shapes.py` (`Piece`)
- Defines standard shapes (Square, T, L, Line, U-Bend) and randomized properties.
- Contains the rotation implementation (`rotate`), cycling through shapes (`cycle_shape`), and "glitch" pieces (cannot be rotated).

---

## Game State Flow
1. **Name Prompt**: Player inputs username -> writes/checks database availability.
2. **Main Gameplay**: Active floating block follows the mouse or arrow keys.
3. **Placing Block**: Committing a block places static cells onto the grid.
4. **Game Over Condition**: Placed blocks touch shrinking walls, or playfield area shrinks to size $\le 2$. Saves score and prompts restart.
