# Tension-Driven First Person Game Concept

This document outlines a simple standalone game concept where the player's actions build up tension that changes the game world. The focus is on an "exploration horror" experience that reacts to how nervous or calm the player is.

## Core Loop
1. The player explores an abandoned facility from a first-person perspective.
2. The environment includes interactive objects, clues, and roaming threats.
3. Tension rises when the player is near threats or witnesses unsettling events.
4. High tension increases difficulty by amplifying enemy aggression and distorting audio/visual feedback.
5. Low tension allows the player to recover stamina and provides clearer audio/visual cues.

## Tension System
- **Tension Value**: a continuous value between 0 and 1.
- **Increase sources**:
  - Seeing or hearing threats.
  - Remaining in darkness for too long.
  - Triggering scripted jump scares.
- **Decrease sources**:
  - Staying in well‑lit safe zones.
  - Completing objectives.
  - Finding calming items (e.g., music boxes).
- **Effects**:
  - 0.0–0.3: calm; minimal threats; normal movement speed.
  - 0.3–0.7: moderate tension; minor visual effects; enemies begin to appear.
  - 0.7–1.0: high tension; heavy distortion; frequent enemy attacks; music intensifies.

## Example Pseudocode
```python
class Game:
    def __init__(self):
        self.tension = 0.0
        self.player = Player()
        self.world = World()

    def update(self, dt):
        self.tension = clamp(self.tension + self.world.fear_factor(self.player) * dt, 0.0, 1.0)
        self.tension -= dt * self.world.relief_factor(self.player)
        self.world.adjust_difficulty(self.tension)
        self.player.update(dt)
        self.world.update(dt)
```

## Implementation Notes
- A lightweight engine such as **Pygame** can be used to prototype the first-person view.
- The game logic should remain offline and not rely on external network calls.
- Save files store only local progress and tension state for a truly standalone experience.

