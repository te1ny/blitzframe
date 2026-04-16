import pygame
import random
import math

# Settings (временно здесь)
WINDOW_WIDTH  = 1500
WINDOW_HEIGHT = 900
FRAMERATE     = 60
PLAYER_SPEED  = 300
ENEMY_SPEED   = 120
PLAYER_SIZE   = 32
ENEMY_SIZE    = 28
SPAWN_INTERVAL = 2.0   # секунд между волнами
ENEMIES_PER_WAVE = 3


# ─────────────────────────── Sprites ────────────────────────────

class Player(pygame.sprite.Sprite):
    def __init__(self, groups):
        super().__init__(groups)
        self.image = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
        self.image.fill((220, 40, 40))          # красный квадрат
        self.rect = self.image.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.pos = pygame.math.Vector2(self.rect.center)
        self.health = 100

    def update(self, dt):
        keys = pygame.key.get_pressed()
        direction = pygame.math.Vector2(0, 0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:    direction.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  direction.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  direction.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: direction.x += 1

        if direction.length() > 0:
            direction = direction.normalize()
        self.pos += direction * PLAYER_SPEED * dt

        # Удержание в пределах экрана
        self.pos.x = max(PLAYER_SIZE // 2, min(WINDOW_WIDTH  - PLAYER_SIZE // 2, self.pos.x))
        self.pos.y = max(PLAYER_SIZE // 2, min(WINDOW_HEIGHT - PLAYER_SIZE // 2, self.pos.y))
        self.rect.center = self.pos


class Enemy(pygame.sprite.Sprite):
    def __init__(self, groups, player):
        super().__init__(groups)
        self.image = pygame.Surface((ENEMY_SIZE, ENEMY_SIZE))
        self.image.fill((40, 200, 60))          # зелёный квадрат
        self.rect = self.image.get_rect(center=self._spawn_pos())
        self.pos = pygame.math.Vector2(self.rect.center)
        self.player = player
        self.health = 3

    @staticmethod
    def _spawn_pos():
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':    return (random.randint(0, WINDOW_WIDTH), -ENEMY_SIZE)
        if side == 'bottom': return (random.randint(0, WINDOW_WIDTH), WINDOW_HEIGHT + ENEMY_SIZE)
        if side == 'left':   return (-ENEMY_SIZE, random.randint(0, WINDOW_HEIGHT))
        return (WINDOW_WIDTH + ENEMY_SIZE, random.randint(0, WINDOW_HEIGHT))

    def update(self, dt):
        direction = pygame.math.Vector2(self.player.rect.center) - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
        self.pos += direction * ENEMY_SPEED * dt
        self.rect.center = self.pos


# ─────────────────────────── States ─────────────────────────────

class Gameplay:
    def __init__(self, game):
        self.game = game

    def on_enter(self):
        pass

    def update(self, dt):
        g = self.game

        # Спавн волн врагов
        g.spawn_timer -= dt
        if g.spawn_timer <= 0:
            g.spawn_timer = SPAWN_INTERVAL
            for _ in range(ENEMIES_PER_WAVE):
                Enemy((g.all_sprites, g.enemy_sprites), g.player)
            
        # Враги ↔ игрок
        if pygame.sprite.spritecollide(g.player, g.enemy_sprites, False):
            g.player.health -= 30 * dt
            if g.player.health <= 0:
                g.change_state('game_over')

    def draw(self):
        g = self.game
        g.all_sprites.draw(g.display_surface)

        # HUD: здоровье
        bar_w = 200
        filled = int(bar_w * max(g.player.health, 0) / 100)
        pygame.draw.rect(g.display_surface, (80, 80, 80), (20, 20, bar_w, 18))
        pygame.draw.rect(g.display_surface, (220, 40, 40), (20, 20, filled, 18))
        pygame.draw.rect(g.display_surface, (255, 255, 255), (20, 20, bar_w, 18), 2)

        # Счётчик врагов
        txt = g.font.render(f'Enemies: {len(g.enemy_sprites)}', True, (255, 255, 255))
        g.display_surface.blit(txt, (20, 46))

        # Подсказка управления
        hint = g.small_font.render('WASD — move   R — reset   ESC — quit', True, (180, 180, 180))
        g.display_surface.blit(hint, (20, WINDOW_HEIGHT - 30))


class GameOver:
    def __init__(self, game):
        self.game = game

    def on_enter(self):
        pass

    def update(self, dt):
        for event in self.game.frame_events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.game.reset_game()

    def draw(self):
        g = self.game
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        g.display_surface.blit(overlay, (0, 0))

        big  = g.big_font.render('GAME OVER', True, (220, 40, 40))
        sub  = g.font.render('Press R to restart', True, (255, 255, 255))
        g.display_surface.blit(big, big.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 40)))
        g.display_surface.blit(sub, sub.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 30)))


# ─────────────────────────── Game ───────────────────────────────

class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Blitzframe')
        self.clock = pygame.time.Clock()
        self.running = True

        self.font       = pygame.font.SysFont('monospace', 22)
        self.small_font = pygame.font.SysFont('monospace', 16)
        self.big_font   = pygame.font.SysFont('monospace', 64, bold=True)

        self.frame_events = []

        self.reset_game()

    def reset_game(self):
        self.game_paused = False

        self.all_sprites           = pygame.sprite.Group()
        self.enemy_sprites         = pygame.sprite.Group()

        self.player = Player(self.all_sprites)

        self.spawn_timer = SPAWN_INTERVAL

        self.states = {
            'gameplay':  Gameplay(self),
            'game_over': GameOver(self),
        }
        self.current_state = self.states['gameplay']
        self.current_state.on_enter()

    def change_state(self, new_state: str):
        self.current_state = self.states[new_state]
        self.current_state.on_enter()

    def run(self):
        while self.running:
            dt = self.clock.tick(FRAMERATE) / 1000

            self.frame_events = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    if event.key == pygame.K_r:
                        self.reset_game()
                self.frame_events.append(event)

            # update
            if not self.game_paused:
                self.all_sprites.update(dt)
            self.current_state.update(dt)

            # draw
            self.display_surface.fill((30, 30, 30))
            self.current_state.draw()

            pygame.display.update()

        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.run()