# Echofoam Logic Game Engine

`tension_game.py` is a compact demonstration of an "echofoam logic" game engine using Pygame. The script runs a basic loop where the player's tension level affects game behavior.

## Tension Mechanic
- **Proximity based**: Tension rises when the player sprite approaches the enemy within `TENSION_RADIUS` pixels.
- **Decay over time**: Each frame reduces tension by `TENSION_DECAY` so calm periods slowly reset the value.
- **Gameplay effects**: Higher tension speeds up the enemy and darkens the screen, showing how a single parameter can drive multiple responses.

## Requirements
- Python 3.10+
- `pygame`

Install Pygame with:
```bash
pip install pygame
```
(Other packages used by the project can be installed from `environment.yml`.)

## Running the Demo
From the repository root, execute:
```bash
python tension_game.py
```
Use the arrow keys or WASD to move. Close the window or press ESC to exit.
