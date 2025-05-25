"""Simple tension-based first person game prototype.

This script implements a minimal game loop in Pygame where the player's
"tension" level rises when near an enemy sprite. High tension speeds up
the enemy and darkens the screen. This is a small prototype demonstrating
how game logic can react to a tension metric.

Controls:
- Arrow keys/WASD: Move the player
- ESC or close the window: Quit
"""

import math
import sys
import pygame
from pygame.locals import QUIT, KEYDOWN, K_ESCAPE

WIDTH, HEIGHT = 800, 600
PLAYER_SPEED = 200  # pixels per second
BASE_ENEMY_SPEED = 50
TENSION_DECAY = 0.1  # per second
TENSION_RADIUS = 200  # distance for maximum tension


def clamp(value, lo, hi):
    return max(lo, min(value, hi))


class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((20, 20))
        self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt, keys):
        dx = (keys[pygame.K_d] - keys[pygame.K_a]) * PLAYER_SPEED * dt
        dy = (keys[pygame.K_s] - keys[pygame.K_w]) * PLAYER_SPEED * dt
        self.rect.x += int(dx)
        self.rect.y += int(dy)
        self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect(center=pos)
        self.velocity = pygame.math.Vector2(1, 0).rotate(45)

    def update(self, dt, speed_multiplier):
        move = self.velocity * BASE_ENEMY_SPEED * speed_multiplier * dt
        self.rect.move_ip(int(move.x), int(move.y))
        if not pygame.Rect(0, 0, WIDTH, HEIGHT).contains(self.rect):
            self.velocity = -self.velocity
            self.rect.clamp_ip(pygame.Rect(0, 0, WIDTH, HEIGHT))


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Tension Prototype")
        self.clock = pygame.time.Clock()
        self.player = Player((WIDTH // 2, HEIGHT // 2))
        self.enemy = Enemy((WIDTH // 4, HEIGHT // 4))
        self.sprites = pygame.sprite.Group(self.player, self.enemy)
        self.tension = 0.0
        self.font = pygame.font.SysFont(None, 24)

    def compute_tension(self):
        dist = self.player.rect.centerx - self.enemy.rect.centerx
        dist_y = self.player.rect.centery - self.enemy.rect.centery
        distance = math.hypot(dist, dist_y)
        proximity = clamp(1.0 - distance / TENSION_RADIUS, 0.0, 1.0)
        return proximity

    def draw(self):
        darken = int(100 * self.tension)
        bg_color = (30 - darken, 30 - darken, 30 - darken)
        self.screen.fill(bg_color)
        self.sprites.draw(self.screen)
        text = self.font.render(f"Tension: {self.tension:.2f}", True, (255, 255, 255))
        self.screen.blit(text, (10, 10))
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == QUIT or (
                    event.type == KEYDOWN and event.key == K_ESCAPE
                ):
                    running = False

            keys = pygame.key.get_pressed()
            self.player.update(dt, keys)
            # tension logic
            self.tension = clamp(
                self.tension + self.compute_tension() * dt - TENSION_DECAY * dt,
                0.0,
                1.0,
            )
            enemy_speed_factor = 1.0 + self.tension
            self.enemy.update(dt, enemy_speed_factor)
            self.draw()

        pygame.quit()


if __name__ == "__main__":
    Game().run()

