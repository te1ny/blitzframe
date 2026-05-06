from settings import *
from sprites import *
from support import *


class InGameStats:
    def __init__(self, game):
        self.game = game
        self.wave = 1
        self.kills = 0
        self.money = 0
        self.prev_enemies_counter = self.enemies_counter = 0
        self.wave_active = False

        # отслеживание уровней апгрейдов
        self.health_upgrade = 100
        self.damage_upgrade = load_json(join('settings', 'gun_settings.json'))['base_damage']
        self.speed_upgrade = 150

    def update(self):
        self.prev_enemies_counter = self.enemies_counter
        self.enemies_counter = len(self.game.enemy_sprites)
        killed = self.prev_enemies_counter - self.enemies_counter
        if killed > 0:
            self.kills += killed
            self.money += random.randint(15, 20) * killed


class Gameplay:
    state_name = 'gameplay'
    music_state = 'gameplay'

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
        self.game.game_paused = False

    def start_wave_timer(self):
        self.starting_wave_timer = Timer(2000, False, True, self.starting_wave)

    def starting_wave(self):
        self.game_stats.wave_active = True

        waves_data = load_json(join('settings', 'waves.json'))
        max_wave = max(int(k) for k in waves_data.keys())
        wave_key = str(min(self.game_stats.wave, max_wave))
        wave_settings: dict = waves_data[wave_key]

        self.boss_wave = wave_settings.get('boss', False)

        enemies_dict = {
            NormalEnemy.name: NormalEnemy,
            FastEnemy.name:   FastEnemy,
            HeavyEnemy.name:  HeavyEnemy,
            FirstBoss.name:   FirstBoss,
        }
        wave_multipliers = wave_settings['enemies_multiplier']

        self.spawn_timers: list[Timer] = []
        for enemy_name, enemy_num in wave_settings['enemies'].items():
            if enemy_name not in enemies_dict:
                continue
            is_boss = enemies_dict[enemy_name].boss
            for _ in range(enemy_num):
                def make_spawn(en=enemy_name, boss=is_boss):
                    def spawn():
                        pos = self._boss_spawn_pos() if boss else self._spawn_pos()
                        enemies_dict[en](
                            (self.game.all_sprites, self.game.enemy_sprites),
                            pos,
                            self.game.enemies_frames_dict[en],
                            self.game.player,
                            health_multiplier=wave_multipliers['health'],
                            speed_multiplier=wave_multipliers['speed'],
                            damage_multiplier=wave_multipliers['damage'],
                        )
                    return spawn
                self.spawn_timers.append(Timer(
                    random.randint(500, self.game_stats.wave * 800),
                    False, True, make_spawn()
                ))

    def _spawn_pos(self):
        px, py = self.game.player.rect.center
        side = random.choice(['top', 'bottom', 'left', 'right'])
        hw, hh = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        m = 100
        if side == 'top':    return (random.randint(px - hw, px + hw), py - hh - m)
        if side == 'bottom': return (random.randint(px - hw, px + hw), py + hh + m)
        if side == 'left':   return (px - hw - m, random.randint(py - hh, py + hh))
        return (px + hw + m, random.randint(py - hh, py + hh))

    def _boss_spawn_pos(self):
        px, py = self.game.player.rect.center
        side = random.choice(['top', 'bottom', 'left', 'right'])
        hw, hh, m = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2, 300
        if side == 'top':    return (px, py - hh - m)
        if side == 'bottom': return (px, py + hh + m)
        if side == 'left':   return (px - hw - m, py)
        return (px + hw + m, py)

    def ending_wave(self):
        self.game_stats.wave_active = False
        self.game_stats.wave += 1
        self.ending_wave_timer = Timer(2000, False, True, lambda: self.game.change_state('shop'))

    def collision(self):
        for bullet in list(self.game.bullet_sprites):
            hits = pygame.sprite.spritecollide(bullet, self.game.enemy_sprites, False)
            if hits:
                bullet.kill()
                for enemy in hits:
                    if enemy.collision_active:
                        enemy.take_damage(bullet.damage)

        hits = pygame.sprite.spritecollide(self.game.player, self.game.enemies_bullet_sprites, True)
        for bullet in hits:
            self.game.player.take_damage(damage=bullet.damage)

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
        font  = pygame.font.SysFont('monospace', 22)
        small = pygame.font.SysFont('monospace', 16)

        bar_w, bar_h = 200, 24
        x, y = 20, 20
        hp, max_hp = self.game.player.health, self.game.player.max_health
        pygame.draw.rect(surface, (60, 60, 60), (x, y, bar_w, bar_h), border_radius=6)
        pygame.draw.rect(surface, (76, 184, 28), (x, y, int(bar_w * max(hp, 0) / max_hp), bar_h), border_radius=6)
        pygame.draw.rect(surface, (255, 255, 255), (x, y, bar_w, bar_h), 1, border_radius=6)
        surface.blit(font.render(f'{int(hp)} / {max_hp}', True, (255, 255, 255)),
                     font.render(f'{int(hp)} / {max_hp}', True, (255,255,255)).get_rect(center=(x + bar_w//2, y + bar_h//2)))

        surface.blit(font.render(f'Волна: {self.game_stats.wave}',   True, (255,255,255)), (20, 52))
        surface.blit(font.render(f'{self.game_stats.money} $',       True, (255,220,0)),   (20, 78))
        surface.blit(small.render(f'Врагов: {len(self.game.enemy_sprites)}', True, (200,200,200)), (20, 104))
        surface.blit(small.render(f'Убито: {self.game_stats.kills}', True, (200,200,200)), (20, 122))

    def draw(self):
        self.game.all_sprites.draw(self.game.player.rect.center)
        self.draw_game_ui()

        if (hasattr(self, 'spawn_timers') and not self.spawn_timers
                and self.game_stats.enemies_counter == 0
                and self.game_stats.wave_active
                and not self.game.enemy_sprites):
            self.ending_wave()

    # Временно для разработки: K — убить всех врагов
    def input(self):
        keys = pygame.key.get_pressed()
        prev_k = getattr(self, '_prev_k', False)
        if keys[pygame.K_k] and not prev_k:
            for sprite in list(self.game.enemy_sprites):
                sprite.kill()
            self.game.enemies_bullet_sprites.empty()
        self._prev_k = bool(keys[pygame.K_k])

    def update(self, dt):
        self.input()
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


# ===================== Shop =====================

class Shop:
    state_name = 'shop'
    music_state = 'shop'

    HEAL_PRICE = 30

    def __init__(self, game):
        self.game = game
        self._buttons = {}

    def on_enter(self):
        self.game.game_paused = True

    # --- цены апгрейдов (формула из Blitzframe-main) ---
    def _health_price(self):
        level = (self.game.game_stats.health_upgrade - 100) // 20 + 1
        return 30 + level * 10

    def _damage_price(self):
        level = (self.game.game_stats.damage_upgrade - 50) // 4 + 1
        return 40 + level * 15

    def _speed_price(self):
        level = (self.game.game_stats.speed_upgrade - 150) // 10 + 1
        return 50 + level * 20

    def _can_buy(self, price):
        if self.game.game_stats.money >= price:
            self.game.game_stats.money -= price
            return True
        return False

    # --- отрисовка одной кнопки, возвращает Rect ---
    def _draw_btn(self, surface, rect, label, font, affordable=True):
        color = (50, 140, 50) if affordable else (80, 80, 80)
        pygame.draw.rect(surface, color, rect, border_radius=8)
        pygame.draw.rect(surface, (200, 200, 200), rect, 1, border_radius=8)
        txt = font.render(label, True, (255, 255, 255))
        surface.blit(txt, txt.get_rect(center=rect.center))
        return rect

    def draw(self):
        surface = self.game.display_surface

        # фон — замёрший игровой мир
        self.game.all_sprites.draw(self.game.player.rect.center)

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        surface.blit(overlay, (0, 0))

        title_font = pygame.font.SysFont('monospace', 52, bold=True)
        font       = pygame.font.SysFont('monospace', 26)
        small      = pygame.font.SysFont('monospace', 20)

        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT // 2

        # заголовок
        surface.blit(
            title_font.render('МАГАЗИН', True, (255, 220, 80)),
            title_font.render('МАГАЗИН', True, (255,220,80)).get_rect(center=(cx, cy - 220))
        )

        stats = self.game.game_stats
        hp_lvl  = (stats.health_upgrade - 100) // 20 + 1
        dmg_lvl = (stats.damage_upgrade - 50)  // 4  + 1
        spd_lvl = (stats.speed_upgrade  - 150) // 10 + 1

        # деньги / убийства
        surface.blit(font.render(f'Деньги: {stats.money} $', True, (255, 220, 0)),
                     font.render(f'Деньги: {stats.money} $', True, (255,220,0)).get_rect(center=(cx, cy - 165)))
        surface.blit(small.render(f'Волна {stats.wave}  |  Убито: {stats.kills}', True, (180, 180, 180)),
                     small.render(f'Волна {stats.wave}  |  Убито: {stats.kills}', True, (180,180,180)).get_rect(center=(cx, cy - 135)))

        # кнопки
        bw, bh, sp = 340, 46, 58
        self._buttons = {
            'heal':   pygame.Rect(0, 0, bw, bh),
            'health': pygame.Rect(0, 0, bw, bh),
            'damage': pygame.Rect(0, 0, bw, bh),
            'speed':  pygame.Rect(0, 0, bw, bh),
            'start':  pygame.Rect(0, 0, bw, bh),
        }
        for i, key in enumerate(['heal', 'health', 'damage', 'speed']):
            self._buttons[key].center = (cx, cy - 90 + i * sp)
        self._buttons['start'].center = (cx, cy - 90 + 4 * sp + 20)

        money = stats.money
        self._draw_btn(surface, self._buttons['heal'],
                       f'Лечение полностью — {self.HEAL_PRICE} $', small,
                       money >= self.HEAL_PRICE)
        self._draw_btn(surface, self._buttons['health'],
                       f'HP (ур.{hp_lvl}) — {self._health_price()} $', small,
                       money >= self._health_price())
        self._draw_btn(surface, self._buttons['damage'],
                       f'Урон (ур.{dmg_lvl}) — {self._damage_price()} $', small,
                       money >= self._damage_price())
        self._draw_btn(surface, self._buttons['speed'],
                       f'Скорость (ур.{spd_lvl}) — {self._speed_price()} $', small,
                       money >= self._speed_price())
        self._draw_btn(surface, self._buttons['start'],
                       'Следующая волна  →', font, True)

    def input(self):
        mouse = pygame.mouse.get_pressed()
        prev = getattr(self, '_prev_mouse', False)
        just_clicked = mouse[0] and not prev
        self._prev_mouse = mouse[0]
        if not just_clicked:
            return
        pos = pygame.mouse.get_pos()
        stats = self.game.game_stats
        player = self.game.player

        if self._buttons.get('heal') and self._buttons['heal'].collidepoint(pos):
            if player.health < player.max_health and self._can_buy(self.HEAL_PRICE):
                player.health = player.max_health

        elif self._buttons.get('health') and self._buttons['health'].collidepoint(pos):
            if self._can_buy(self._health_price()):
                was_full = player.health == player.max_health
                stats.health_upgrade += 20
                player.max_health = stats.health_upgrade
                if was_full:
                    player.health = stats.health_upgrade

        elif self._buttons.get('damage') and self._buttons['damage'].collidepoint(pos):
            if self._can_buy(self._damage_price()):
                stats.damage_upgrade += 4

        elif self._buttons.get('speed') and self._buttons['speed'].collidepoint(pos):
            if self._can_buy(self._speed_price()):
                stats.speed_upgrade += 10
                player.speed = stats.speed_upgrade

        elif self._buttons.get('start') and self._buttons['start'].collidepoint(pos):
            self.game.change_state('gameplay')
            self.game.gameplay.start_wave_timer()

    def update(self, dt):
        self.input()


# ===================== GameOver =====================

class GameOver:
    state_name = 'game_over'
    music_state = 'gameplay'

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
        font     = pygame.font.SysFont('monospace', 28)

        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2
        stats = self.game.game_stats

        for surf, pos in [
            (big_font.render('GAME OVER', True, (220, 40, 40)),         (cx, cy - 70)),
            (font.render('Нажмите R для рестарта', True, (255,255,255)), (cx, cy + 10)),
            (font.render(f'Убито: {stats.kills}   Волна: {stats.wave}', True, (200,200,200)), (cx, cy + 55)),
        ]:
            surface.blit(surf, surf.get_rect(center=pos))

    def update(self, dt):
        pass
