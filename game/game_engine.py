import pygame
import random
from .player import Player
from .enemy import EnemyGrid
from .bullet import Bullet
from .sound import SoundManager

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 220, 0)
RED = (220, 60, 60)
GOLD = (255, 215, 0)
GRAY = (180, 180, 180)

DIFFICULTIES = {
    "Easy": {"speed": 1.0, "fire_chance": 0.005},
    "Medium": {"speed": 1.8, "fire_chance": 0.01},
    "Hard": {"speed": 2.6, "fire_chance": 0.02},
}

class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.font = pygame.font.SysFont("Arial", 28)
        self.big_font = pygame.font.SysFont("Arial", 46, bold=True)
        self.small_font = pygame.font.SysFont("Arial", 20)

        # Sound effects manager (Task 4)
        self.sound = SoundManager()

        self.current_difficulty = "Medium"
        self.reset_game(self.current_difficulty)

    def reset_game(self, difficulty="Medium"):
        """Resets all game state and entities with the given difficulty (Task 3)."""
        self.current_difficulty = difficulty
        settings = DIFFICULTIES.get(difficulty, DIFFICULTIES["Medium"])

        self.player = Player(self.width // 2 - 20, self.height - 50, 40, 20)
        self.enemy_grid = EnemyGrid(self.width, speed=settings["speed"])

        self.player_bullets = []
        self.enemy_bullets = []
        self._shoot_cooldown = 0
        self.enemy_fire_chance = settings["fire_chance"]

        self.score = 0
        self.game_over = False
        self.victory = False

    def handle_event(self, event):
        # Task 3: Handle difficulty selection or exit after Game Over
        if self.game_over:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_1, pygame.K_e):
                    self.reset_game("Easy")
                elif event.key in (pygame.K_2, pygame.K_m):
                    self.reset_game("Medium")
                elif event.key in (pygame.K_3, pygame.K_h):
                    self.reset_game("Hard")
                elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                    pygame.event.post(pygame.event.Event(pygame.QUIT))
            return

        # Player shooting with sound effect (Task 4)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            if self._shoot_cooldown <= 0:
                bullet_x = self.player.center_x() - 2
                self.player_bullets.append(Bullet(bullet_x, self.player.y, direction=-1))
                self._shoot_cooldown = 15
                self.sound.play("laser")

    def handle_input(self):
        if self.game_over:
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.move(-self.player.speed, self.width)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.move(self.player.speed, self.width)

    def trigger_game_over(self, victory=False):
        """Transitions into game-over state and plays sound (Task 2 & 4)."""
        if not self.game_over:
            self.game_over = True
            self.victory = victory
            self.sound.play("game_over")

    def update(self):
        if self.game_over:
            return

        if self._shoot_cooldown > 0:
            self._shoot_cooldown -= 1

        self.enemy_grid.move()

        # Enemies firing
        for enemy in self.enemy_grid.alive_enemies():
            if random.random() < self.enemy_fire_chance:
                bullet_x = enemy.x + enemy.width // 2
                self.enemy_bullets.append(Bullet(bullet_x, enemy.y + enemy.height, direction=1))

        # Move bullets
        for bullet in self.player_bullets:
            bullet.move()
        for bullet in self.enemy_bullets:
            bullet.move()

        self.player_bullets = [b for b in self.player_bullets if not b.off_screen(self.height)]
        self.enemy_bullets = [b for b in self.enemy_bullets if not b.off_screen(self.height)]

        # Task 1: Refined collision detection
        # Avoid mutating self.player_bullets during iteration to ensure all collisions register
        remaining_bullets = []
        for bullet in self.player_bullets:
            hit = False
            for enemy in self.enemy_grid.alive_enemies():
                if bullet.rect().colliderect(enemy.rect()):
                    enemy.alive = False
                    self.score += 1
                    hit = True
                    self.sound.play("explosion")
                    break
            if not hit:
                remaining_bullets.append(bullet)
        self.player_bullets = remaining_bullets

        # Check player hit by enemy bullet (Task 2)
        for bullet in self.enemy_bullets:
            if bullet.rect().colliderect(self.player.rect()):
                self.trigger_game_over(victory=False)
                break

        # Check enemies reached bottom (Task 2)
        if self.enemy_grid.reached_bottom(self.player.y):
            self.trigger_game_over(victory=False)

        # Check all enemies eliminated (Victory condition)
        if len(self.enemy_grid.alive_enemies()) == 0:
            self.trigger_game_over(victory=True)

    def render(self, screen):
        # Render player
        pygame.draw.rect(screen, GREEN, self.player.rect())

        # Render enemies
        for enemy in self.enemy_grid.alive_enemies():
            pygame.draw.rect(screen, WHITE, enemy.rect())

        # Render bullets
        for bullet in self.player_bullets:
            pygame.draw.rect(screen, WHITE, bullet.rect())
        for bullet in self.enemy_bullets:
            pygame.draw.rect(screen, RED, bullet.rect())

        # Render HUD (Score & Difficulty)
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        diff_text = self.small_font.render(f"Difficulty: {self.current_difficulty}", True, GRAY)
        screen.blit(score_text, (10, 10))
        screen.blit(diff_text, (self.width - diff_text.get_width() - 10, 15))

        # Task 2 & 3: Game Over & Replay Screen Overlay
        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))

            title_text = "VICTORY!" if self.victory else "GAME OVER"
            title_color = GREEN if self.victory else RED
            title_surf = self.big_font.render(title_text, True, title_color)
            score_surf = self.font.render(f"Final Score: {self.score}", True, WHITE)

            instruct_header = self.font.render("Select Replay Difficulty:", True, GOLD)
            opt_easy = self.small_font.render("[1] or [E] : Easy", True, WHITE)
            opt_med = self.small_font.render("[2] or [M] : Medium", True, WHITE)
            opt_hard = self.small_font.render("[3] or [H] : Hard", True, WHITE)
            opt_quit = self.small_font.render("[Q] or [ESC] : Quit", True, GRAY)

            center_x = self.width // 2
            screen.blit(title_surf, title_surf.get_rect(center=(center_x, self.height // 2 - 120)))
            screen.blit(score_surf, score_surf.get_rect(center=(center_x, self.height // 2 - 60)))
            screen.blit(instruct_header, instruct_header.get_rect(center=(center_x, self.height // 2)))
            screen.blit(opt_easy, opt_easy.get_rect(center=(center_x, self.height // 2 + 40)))
            screen.blit(opt_med, opt_med.get_rect(center=(center_x, self.height // 2 + 70)))
            screen.blit(opt_hard, opt_hard.get_rect(center=(center_x, self.height // 2 + 100)))
            screen.blit(opt_quit, opt_quit.get_rect(center=(center_x, self.height // 2 + 145)))
