# PathBlocker AI

A Quoridor-style strategy board game with a neon UI and a Python-powered AI opponent, built with Django. This README doubles as the project plan: what it is, how it will be built, and how to get it running from scratch.

## Overview

Two players (or one player vs. an AI bot) race to move their pawn across a 9x9 grid to the opposite edge of the board, while placing walls to block their opponent's shortest path. The project's core challenge is building an AI opponent that plays competently and responds quickly, using classical adversarial search rather than machine learning.

## Goals

- [ ] Implement the full Quoridor rule set: pawn movement, jumps over an adjacent opponent, wall placement, and the "never fully block a path" legality check.
- [ ] Implement an AI opponent using minimax search with alpha-beta pruning, scored by a BFS shortest-path heuristic.
- [ ] Support three difficulty tiers (Easy, Medium, Hard) with different search depth and a bounded time budget so the AI always responds quickly.
- [ ] Build a responsive canvas-based UI: menu screen, live HUD, move/wall hover previews, and a game-over screen.
- [ ] Support local 2-player mode entirely in the browser (no server round-trip).
- [ ] Add a theme system with multiple visual styles (Neon, Glassmorphism, Cyberpunk, Synthwave, Minimal).
- [ ] Polish pass: sound effects, move animation, and an onboarding/rules overlay.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Django |
| AI / Algorithms | Custom Python (minimax, alpha-beta pruning, BFS pathfinding), no external ML library |
| Frontend | HTML5 Canvas, vanilla JavaScript, CSS (custom properties for theming) |
| Data interchange | JSON over HTTP (Fetch API), CSRF-protected via Django's `csrftoken` cookie |
| Version control | Git |

## How the AI Will Work

The bot's turn is decided by minimax search with alpha-beta pruning:

1. **State**: pawn positions, wall grids (horizontal/vertical), and remaining wall counts per player.
2. **Move generation**: legal pawn moves (including jumps) and legal wall placements, filtered so no wall can fully seal off a player's path.
3. **Search**: recursively simulate future turns to a fixed depth, alternating between maximizing the AI's outcome and minimizing the opponent's, with alpha-beta pruning to cut unproductive branches.
4. **Evaluation**: each leaf is scored primarily by BFS shortest-path distance to the goal row for each player, plus a smaller bonus for remaining walls and mobility.
5. **Move ordering and pruning**: candidate moves are ranked before deep search, and wall candidates are restricted to those near either player's current shortest path, to keep search fast.
6. **Difficulty tiers**: Easy uses a greedy strategy, Medium and Hard use full minimax at increasing depth, each with a time budget so a response is always returned promptly.

## Getting Started

### Prerequisites

- Python 3.10+
- pip

### Setup

```bash
git clone <this-repo-url>
cd "PathBlocker-AI"
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Then open http://127.0.0.1:8000 in a browser.

### How to Play

- Move your pawn one step at a time toward the opposite edge of the board.
- Or place a wall (you start with 10) to block your opponent's path.
- Jump over your opponent if they are directly in your path.
- First to reach the far row wins.

## Planned Project Structure

```
neon_blockade/        # Django project settings/urls
game/
  views.py            # index page + /api/ai-move endpoint
  ai.py                # game engine + minimax AI
  urls.py
  templates/game/index.html
  static/game/{css,js}/
manage.py
requirements.txt
```

## Roadmap / Next Steps

1. Scaffold the Django project and app.
2. Implement the Quoridor rules engine and validate it with unit tests (movement, jumps, wall legality).
3. Implement the minimax AI and tune the evaluation weights.
4. Build the canvas UI and wire it to the AI endpoint.
5. Add the theme system and menu.
6. Polish: sounds, animation, onboarding.
7. Write final documentation and prepare the project proposal/report.

## License

Educational project, license to be decided.
