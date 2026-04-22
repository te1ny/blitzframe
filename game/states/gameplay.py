from settings import *
from sprites import *
from support import *


class InGameStats:
    def __init__(self, game):
        self.game = game
        self.wave = 1
        self.kills = 0
        self.prev_enemies_counter = self.enemies_counter = 0
        self.wave_active = False

    def update(self):
        self.prev_enemies_counter = self.enemies_counter
        self.enemies_counter = len(self.game.enemy_sprites)
        if self.prev_enemies_counter > self.enemies_counter:
            self.kills += self.prev_enemies_counter - self.enemies_counter


class Gameplay:
    state_name = 'gameplay'

    def __init__(self, game):
        self.game = game

    def on_enter(self):
        if not hasattr(self.game, 'player'):
            self.game.gameplay = self
            self.game.player = Player(
                self.game.all_sprites,
                (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2),
                self.game
            )
            self.game.game_stats = self.game_stats = InGameStats(self.game)
            self.game.current_gun = Pistol(
                (self.game.all_sprites, self.game.bullet_sprites),
                self.game.player
            )
            self.start_wave_timer()
        else:
            self.game_stats = self.game.game_stats

    def start_wave_timer(self):
        self.starting_wave_timer = Timer(2000, False, True, self.starting_wave)

    def starting_wave(self):
        self.game_stats.wave_active = True

        wave_key = str(min(self.game_stats.wave, 5))
        wave_settings: dict = load_json(join('settings', 'waves.json'))[wave_key]

        enemies_dict = {
            NormalEnemy.name: NormalEnemy,
            FastEnemy.name: FastEnemy,
            HeavyEnemy.name: HeavyEnemy,
        }
        wave_multipliers = wave_settings['enemies_multiplier']

        self.spawn_timers: list[Timer] = []
        for enemy_name, enemy_num in wave_settings['enemies'].items():
            if enemy_name not in enemies_dict:
                continue
            for _ in range(enemy_num):
                self.spawn_timers.append(Timer(
                    random.randint(500, self.game_stats.wave * 800),
                    False, True,
                    lambda en=enemy_name: enemies_dict[en](
                        (self.game.all_sprites, self.game.enemy_sprites),
                        self._spawn_pos(),
                        self.game.enemies_frames_dict[en],
                        self.game.player,
                        health_multiplier=wave_multipliers['health'],
                        speed_multiplier=wave_multipliers['speed'],
                        damage_multiplier=wave_multipliers['damage'],
                    )
                ))

    def _spawn_pos(self):
        player_pos = self.game.player.rect.center
        side = random.choice(['top', 'bottom', 'left', 'right'])
        margin = 100
        half_w, half_h = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        if side == 'top':
            return (random.randint(player_pos[0] - half_w, player_pos[0] + half_w), player_pos[1] - half_h - margin)
        if side == 'bottom':
            return (random.randint(player_pos[0] - half_w, player_pos[0] + half_w), player_pos[1] + half_h + margin)
        if side == 'left':
            return (player_pos[0] - half_w - margin, random.randint(player_pos[1] - half_h, player_pos[1] + half_h))
        return (player_pos[0] + half_w + margin, random.randint(player_pos[1] - half_h, player_pos[1] + half_h))

    def ending_wave(self):
        self.game_stats.wave_active = False
        self.game_stats.wave += 1
        self.ending_wave_timer = Timer(3000, False, True, self.start_wave_timer)

    def collision(self):
        for bullet in list(self.game.bullet_sprites):
            hits = pygame.sprite.spritecollide(bullet, self.game.enemy_sprites, False)
            if hits:
                bullet.kill()
                for enemy in hits:
                    if enemy.collision_active:
                        enemy.take_damage(bullet.damage)

        for enemy in self.game.enemy_sprites:
            if enemy.rect.colliderect(self.game.player.rect):
                self.game.player.take_damage(enemy=enemy)
                if not self.game.player.damage_delay_timer:
                    enemy.deal_damage()

    def check_player_alive(self):
        if self.game.player.health <= 0:
            self.game.player.health = 0
            self.game.player.death()
            self.game.current_gun.kill()
            if not hasattr(self, 'game_over_timer'):
                self.game_over_timer = Timer(2000, False, True, lambda: self.game.change_state('game_over'))

    def draw_game_ui(self):
        surface = pygame.display.get_surface()
        font = pygame.font.SysFont('monospace', 22)
        small = pygame.font.SysFont('monospace', 16)

        bar_w, bar_h = 200, 24
        x, y = 20, 20
        hp = self.game.player.health
        max_hp = self.game.player.max_health
        pygame.draw.rect(surface, (60, 60, 60), (x, y, bar_w, bar_h), border_radius=6)
        fill = int(bar_w * max(hp, 0) / max_hp)
        pygame.draw.rect(surface, (76, 184, 28), (x, y, fill, bar_h), border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255), (x, y, bar_w, bar_h), 1, border_radius=6)
        hp_text = font.render(f'{int(hp)} / {max_hp}', True, (255, 255, 255))
        surface.blit(hp_text, hp_text.get_rect(center=(x + bar_w // 2, y + bar_h // 2)))

        wave_text = font.render(f'Волна: {self.game_stats.wave}', True, (255, 255, 255))
        surface.blit(wave_text, (20, 52))

        enemies_text = small.render(f'Врагов: {len(self.game.enemy_sprites)}', True, (200, 200, 200))
        surface.blit(enemies_text, (20, 78))

        kills_text = small.render(f'Убито: {self.game_stats.kills}', True, (200, 200, 200))
        surface.blit(kills_text, (20, 96))

    def draw(self):
        self.game.all_sprites.draw(self.game.player.rect.center)
        self.draw_game_ui()

        if (hasattr(self, 'spawn_timers') and not self.spawn_timers
                and self.game_stats.enemies_counter == 0
                and self.game_stats.wave_active
                and not self.game.enemy_sprites):
            self.ending_wave()

    def update(self, dt):
        self.game_stats.update()
        self.collision()
        self.check_player_alive()

        self.starting_wave_timer.update()

        if hasattr(self, 'ending_wave_timer'):
            self.ending_wave_timer.update()

        if hasattr(self, 'game_over_timer'):
            self.game_over_timer.update()

        if hasattr(self, 'spawn_timers'):
            for timer in list(self.spawn_timers):
                timer.update()
                if not timer:
                    self.spawn_timers.remove(timer)


class GameOver:
    state_name = 'game_over'

    def __init__(self, game):
        self.game = game

    def on_enter(self):
        self.game.game_paused = True

    def draw(self):
        self.game.all_sprites.draw(self.game.player.rect.center)

        surface = pygame.display.get_surface()
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        big_font = pygame.font.SysFont('monospace', 64, bold=True)
        font = pygame.font.SysFont('monospace', 28)

        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        big = big_font.render('GAME OVER', True, (220, 40, 40))
        sub = font.render('Нажмите R для рестарта', True, (255, 255, 255))
        stats = font.render(
            f'Убито: {self.game.game_stats.kills}   Волна: {self.game.game_stats.wave}',
            True, (200, 200, 200)
        )
        surface.blit(big, big.get_rect(center=(cx, cy - 60)))
        surface.blit(sub, sub.get_rect(center=(cx, cy + 20)))
        surface.blit(stats, stats.get_rect(center=(cx, cy + 65)))

    def update(self, dt):
        pass
