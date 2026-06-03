# Continental Drift

Continental Drift is a single-player desktop puzzle game built with Python and
Pygame. The player places Tetris-like shapes inside a 16 by 16 board while four
red walls slowly close in from every side. The goal is to survive as long as
possible by building filled 3 by 3 block structures, which disappear and push the
walls back outward.

The game also supports optional PostgreSQL score saving. If a database is
available, the game stores each player's name and final score when the game ends.
If the database is unavailable, the game still runs normally and shows the
database status on screen.

## Features

- 16 by 16 grid-based puzzle board.
- Four red walls shrink inward over time.
- Red walls are lethal: if a wall touches the active piece or any placed block,
  the game ends.
- Player-controlled placement instead of falling blocks.
- Mouse and keyboard placement support.
- Shape rotation with `F`.
- Active shape cycling with `E`.
- Next-shape preview in the HUD.
- Filled 3 by 3 structures clear from the board.
- Clearing a 3 by 3 structure expands all four walls.
- Player name entry screen.
- Optional PostgreSQL score storage.

## Project Structure

```text
continental_drift/
├── main.py       # Pygame window, rendering, input, username flow, DB saving
├── engine.py     # Score, level, wall contraction, game-over timing
├── grid.py       # Board state, collision checks, wall-touch checks, 3x3 clears
├── shapes.py     # Shape definitions, colors, rotation, shape cycling
├── README.md     # Project documentation
└── databse.py    # Placeholder file, currently unused
```

## Requirements

- macOS, Linux, or Windows with Python 3 installed.
- Python 3.10 or newer recommended.
- `pygame` or `pygame-ce`.
- `psycopg` for PostgreSQL score saving.
- PostgreSQL is optional. The game runs without it.

This project was tested locally with:

```text
Python 3.14.5
pygame-ce 2.5.7
psycopg 3.3.4
```

## Installation

Open a terminal and move into the project folder:

```bash
cd /Users/muhaiminul/Documents/IUT_Codex/continental_drift
```

Install the Python packages:

```bash
python3 -m pip install pygame-ce psycopg[binary]
```

On some Homebrew-managed macOS Python installs, `pip` may block global package
installation. In that case, use a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install pygame-ce psycopg[binary]
```

If you already installed the packages globally or with `--user`, you can skip
the virtual environment.

## Running The Game

From the `continental_drift` folder, run:

```bash
python3 main.py
```

The game opens a 600 by 680 Pygame window.

## Running Without PostgreSQL

PostgreSQL is optional. If no database is configured or reachable, the game still
starts and plays normally. You will see a DB status message such as:

```text
DB: offline (OperationalError)
```

Scores will not be stored until a working PostgreSQL connection is configured.

## PostgreSQL Score Saving

The game reads the database URL from either of these environment variables:

1. `CONTINENTAL_DRIFT_DB_URL`
2. `DATABASE_URL`

If neither is set, it tries:

```text
postgresql://localhost/continental_drift
```

Example:

```bash
export CONTINENTAL_DRIFT_DB_URL="postgresql://user:password@localhost:5432/continental_drift"
python3 main.py
```

When the connection works, the game automatically creates this table:

```sql
CREATE TABLE IF NOT EXISTS scores (
    id BIGSERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    score INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

When a game ends, one row is inserted:

```sql
INSERT INTO scores (username, score) VALUES (...);
```

### Example Local PostgreSQL Setup

If PostgreSQL is installed and running locally, create a database:

```bash
createdb continental_drift
```

Then run:

```bash
export CONTINENTAL_DRIFT_DB_URL="postgresql://localhost/continental_drift"
python3 main.py
```

To view saved scores:

```bash
psql postgresql://localhost/continental_drift
```

Then inside `psql`:

```sql
SELECT username, score, created_at
FROM scores
ORDER BY score DESC, created_at ASC;
```

## How To Play

1. Start the game.
2. Enter your player name.
3. Press `Enter` to begin.
4. Move the active shape inside the shrinking red walls.
5. Place shapes to build filled 3 by 3 structures.
6. A filled 3 by 3 structure disappears and expands the walls.
7. Survive as long as possible.

## Controls

| Control | Action |
|---|---|
| `Arrow Left` | Move active shape left |
| `Arrow Right` | Move active shape right |
| `Arrow Up` | Move active shape up |
| `Arrow Down` | Move active shape down |
| `F` | Rotate active shape |
| `E` | Cycle active shape to the next design |
| `Space` | Place active shape |
| `Enter` | Place active shape, or start after entering name |
| Mouse move | Move active shape to a valid grid position |
| Mouse click | Place active shape at a valid grid position |
| `R` | Restart after game over |
| `Escape` | Quit |

## Shape Cycling

Pressing `E` changes the current piece to the next shape in this order:

```text
SQUARE -> T_SHAPE -> L_SHAPE -> LINE -> U_BEND -> SQUARE
```

The cycle loops forever, so pressing `E` enough times returns to the original
shape.

## Rotation

Press `F` to rotate the active shape clockwise. If the rotated shape would
collide with a wall or another block, the rotation is reverted.

Glitch pieces are red. They can be placed normally, but they do not rotate.

## Clearing Rule

A filled 3 by 3 block structure clears anywhere inside the active area.

Example:

```text
****
***
***
```

The filled 3 by 3 part disappears, but the extra block remains:

```text
*
```

Every cleared 3 by 3 structure expands all four walls by one grid unit, up to
the outer 16 by 16 board boundary.

## Scoring And Levels

Scores are awarded when 3 by 3 structures clear:

| Structures cleared at once | Base points |
|---:|---:|
| 0 | 0 |
| 1 | 100 |
| 2 | 300 |
| 3 | 500 |
| 4 or more | 800 |

The base points are multiplied by the current level.

Levels increase every 500 points, up to level 3.

Wall behavior by level:

| Level | Wall behavior |
|---:|---|
| 1 | All four walls shrink continuously |
| 2 | All four walls snap inward every 3 seconds |
| 3 | Left and right walls shrink continuously |

## Game Over Conditions

The game ends when:

- Any red wall touches a placed block.
- Any red wall touches the active piece.
- The active piece cannot be placed in a valid position.
- The playable area becomes too small.

After game over, press `R` to restart.

## Troubleshooting

### `ModuleNotFoundError: No module named 'pygame'`

Install Pygame:

```bash
python3 -m pip install pygame-ce
```

### `ModuleNotFoundError: No module named 'psycopg'`

Install the PostgreSQL driver:

```bash
python3 -m pip install psycopg[binary]
```

The game can still run without `psycopg`, but score saving will be disabled.

### `DB: offline (OperationalError)`

This usually means PostgreSQL is not running, the database does not exist, or the
connection URL is wrong.

Check that your URL is set:

```bash
echo "$CONTINENTAL_DRIFT_DB_URL"
```

Try connecting manually:

```bash
psql "$CONTINENTAL_DRIFT_DB_URL"
```

### Pygame Window Does Not Open

Make sure you are running the command in a desktop environment, not a headless
terminal session:

```bash
python3 main.py
```

If you are inside a virtual environment, activate it first:

```bash
source .venv/bin/activate
python3 main.py
```

## Development Notes

- `main.py` is the application entry point.
- `grid.py` owns all board and collision logic.
- `engine.py` owns score, level, and wall contraction logic.
- `shapes.py` owns piece definitions and shape transformations.
- The PostgreSQL integration is intentionally non-blocking for gameplay: failed
  database connections update the on-screen DB status instead of crashing the
  game.

## Quick Start

```bash
git clone https://github.com/Sk-Muhaiminul-Hasan/Weird_Tetris.git
cd Weird_Tetris
python3 -m pip install pygame-ce psycopg[binary]
python3 main.py
```
