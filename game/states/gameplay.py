from settings import *
from sprites import *
from support import *
from ui import Button, draw_text_window
from support import FadeText


class InGameStats:
    def __init__(self, game):
        self.game = game
        self.money = 0
        self.wave = 1
        self.kills = 0
        self.prev_enemies_counter = self.enemies_counter = 0
        self.wave_active = False

        self.heal_price = 30

        self.health_upgrade       = 100
        self.health_upgrade_step  = 20
        self.health_level         = 1
        self.health_upgrade_price = 30
        self.health_price_step    = 10

        self.damage_upgrade       = load_json(join('settings', 'gun_settings.json'))['base_damage']
        self.damage_upgrade_step  = 4
        self.damage_level         = 1
        self.damage_upgrade_price = 40
        self.damage_price_step    = 15

        self.speed_upgrade        = 150
        self.speed_upgrade_step   = 10
        self.speed_level          = 1
        self.speed_upgrade_price  = 50
        self.speed_price_step     = 20

    def update_skill_level(self):
        self.health_level = (self.health_upgrade - 100) // self.health_upgrade_step + 1
        self.damage_level = (self.damage_upgrade - 50)  // self.damage_upgrade_step  + 1
        self.speed_level  = (self.speed_upgrade  - 150) // self.speed_upgrade_step   + 1

    def get_upgrade_price(self, skill):
        if skill == 'health':
            return self.health_upgrade_price + self.health_level * self.health_price_step
        if skill == 'damage':
            return self.damage_upgrade_price + self.damage_level * self.damage_price_step
        if skill == 'speed':
            return self.speed_upgrade_price  + self.speed_level  * self.speed_price_step

    def next_upgrage_price(self):
        self.next_health_upgrade_price = self.get_upgrade_price('health')
        self.next_damage_upgrade_price = self.get_upgrade_price('damage')
        self.next_speed_upgrade_price  = self.get_upgrade_price('speed')

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
                self.game.tilemap.player_spawner(),
                self.game.player_frames,
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
        self.game.change_gun(self.game.current_gun.gun_name, sound=False)
        self.game.game_paused = False

    def start_wave_timer(self):
        self.starting_wave_timer = Timer(2000, False, True, self.starting_wave)

    def starting_wave(self):
        self.game_stats.wave_active = True
        self.game.play_sound('tick')
        cx = WINDOW_WIDTH // 2
        self.fade_text = FadeText(f'Волна {self.game_stats.wave}', self.game.l_font, (82, 61, 80), (cx, 70))
        self.fade_text.start()

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

    def _spawn_pos(self, min_distance=600):
        player_pos = self.game.player.rect.center
        all_spawners = self.game.tilemap.enemy_spawner()
        spawners = [
            pos for pos in all_spawners
            if ((pos[0] - player_pos[0]) ** 2 + (pos[1] - player_pos[1]) ** 2) ** 0.5 > min_distance
        ]
        if not spawners:
            spawners = all_spawners
        return random.choice(spawners) if spawners else player_pos

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
        cx = WINDOW_WIDTH // 2
        self.fade_text = FadeText(f'Волна {self.game_stats.wave} пройдена!', self.game.l_font, (82, 61, 80), (cx, 70))
        self.fade_text.start()
        self.game_stats.wave += 1
        self.ending_wave_timer = Timer(2000, False, True, lambda: self.game.change_state('shop'))

    def collision(self):
        for bullet in list(self.game.bullet_sprites):
            if pygame.sprite.spritecollideany(bullet, self.game.collision_sprites):
                bullet.kill()
                continue
            hits = pygame.sprite.spritecollide(bullet, self.game.enemy_sprites, False)
            if hits:
                bullet.kill()
                for enemy in hits:
                    if enemy.collision_active:
                        enemy.take_damage(bullet.damage)

        for bullet in list(self.game.enemies_bullet_sprites):
            if pygame.sprite.spritecollideany(bullet, self.game.collision_sprites):
                bullet.kill()

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
        font  = pygame.font.SysFont('monospace', 24)
        small = pygame.font.SysFont('monospace', 16)

        bar_w, bar_h = 200, 30
        x, y = 20, 20
        hp, max_hp = self.game.player.health, self.game.player.max_health
        pygame.draw.rect(surface, (60, 60, 60),   (x, y, bar_w, bar_h), border_radius=8)
        pygame.draw.rect(surface, (76, 184, 28),  (x, y, int(bar_w * max(hp, 0) / max_hp), bar_h), border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255),(x, y, bar_w, bar_h), 1, border_radius=8)
        hp_txt = font.render(f'{int(hp)} / {max_hp}', True, (255, 255, 255))
        surface.blit(hp_txt, hp_txt.get_rect(center=(x + bar_w // 2, y + bar_h // 2)))

        money_font = pygame.font.SysFont('monospace', 32)
        surface.blit(money_font.render(f'{self.game_stats.money} $', True, (0, 0, 0)), (20, 58))
        surface.blit(small.render(f'Волна: {self.game_stats.wave}',              True, (200, 200, 200)), (20, 96))
        surface.blit(small.render(f'Врагов: {len(self.game.enemy_sprites)}',    True, (200, 200, 200)), (20, 114))
        surface.blit(small.render(f'Убито: {self.game_stats.kills}',            True, (200, 200, 200)), (20, 132))

    def draw(self):
        self.game.all_sprites.draw(self.game.player.rect.center)
        self.draw_game_ui()

        if hasattr(self, 'fade_text'):
            self.fade_text.update(self.game.display_surface)

        if (hasattr(self, 'spawn_timers') and not self.spawn_timers
                and self.game_stats.enemies_counter == 0
                and self.game_stats.wave_active
                and not self.game.enemy_sprites):
            self.ending_wave()

    def input(self):
        keys = pygame.key.get_pressed()
        prev_esc = getattr(self, '_prev_esc', False)
        if keys[pygame.K_ESCAPE] and not prev_esc:
            self.game.change_state('pause', False)
        self._prev_esc = bool(keys[pygame.K_ESCAPE])

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


# ===================== InGameWindow =====================

class InGameWindow:
    def __init__(self, game, title='', size=(800, 520)):
        self.game = game
        self.display_surface = pygame.display.get_surface()
        self.width, self.height = size
        self.bg_color = (30, 30, 30, 180)
        self.window_rect = pygame.Rect(0, 0, *size)
        self.window_rect.center = self.display_surface.get_rect().center
        self.title = title

    def on_enter(self):
        self.create_buttons()

    def create_buttons(self):
        pass

    def draw(self):
        self.game.all_sprites.draw(self.game.player.rect.center)

        overlay = pygame.Surface(self.display_surface.get_size(), pygame.SRCALPHA)
        overlay.fill(self.bg_color)
        self.display_surface.blit(overlay, (0, 0))

        window_surf = pygame.Surface(self.window_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(window_surf, (50, 50, 50, 120), window_surf.get_rect(), border_radius=20)
        self.display_surface.blit(window_surf, self.window_rect.topleft)

        if self.title:
            font = self.game.m_font
            title_surf = font.render(self.title, True, 'white')
            self.display_surface.blit(
                title_surf,
                title_surf.get_rect(center=(self.window_rect.centerx, self.window_rect.top - 50))
            )

        self.game.buttons_sprites.draw(self.display_surface)

    def update(self, dt):
        self.game.buttons_sprites.update(dt)


# ===================== Shop =====================

class Shop(InGameWindow):
    state_name = 'shop'
    music_state = 'shop'

    _ALL_GUNS = None  # populated lazily after sprites module is fully loaded

    def __init__(self, game):
        super().__init__(game, title='Магазин', size=(800, 520))
        self.all_guns = {
            Pistol.gun_name:      Pistol,
            Shotgun.gun_name:     Shotgun,
            SniperRifle.gun_name: SniperRifle,
            MachineGun.gun_name:  MachineGun,
        }

    def on_enter(self):
        self.game.game_paused = True
        super().on_enter()

    def create_buttons(self):
        cols, rows = 3, 4
        h_margin, v_top, v_bot = 40, 70, 70
        sp_y = 20

        # Центры колонок: правая сдвинута влево для визуального баланса
        avail_w = self.window_rect.width - 2 * h_margin
        col_centers = [
            self.window_rect.left + int(h_margin + (c + 0.5) * avail_w / cols)
            for c in range(cols)
        ]

        btn_h = (self.window_rect.height - v_top - v_bot - (rows - 1) * sp_y) // rows

        self.buttons = [[None] * cols for _ in range(rows)]

        gun_order = [Pistol.gun_name, Shotgun.gun_name, SniperRifle.gun_name, MachineGun.gun_name]

        for row in range(rows):
            for col in range(cols):
                x = col_centers[col]
                y = self.window_rect.top  + v_top    + row * (btn_h + sp_y) + btn_h // 2
                btn = None

                # col 0 — guns
                if col == 0:
                    gn = gun_order[row]
                    if gn in self.game.available_weapons:
                        img_key = f'choosen_{gn}' if self.game.current_gun.gun_name == gn else f'open_{gn}'
                        btn = Button(groups=self.game.buttons_sprites, pos=(x, y),
                                     image=self.game.buttons_frames[img_key],
                                     callback=f'select_{gn}')
                    else:
                        btn = Button(groups=self.game.buttons_sprites, pos=(x, y),
                                     image=self.game.buttons_frames[f'locked_{gn}'],
                                     callback=f'buy_{gn}')

                # col 1 — start wave (row 0 only)
                elif col == 1 and row == 0:
                    btn = Button(groups=self.game.buttons_sprites, pos=(x, y),
                                 image=self.game.buttons_frames['start_wave'],
                                 callback='next_wave')

                # col 2 — heal + upgrades
                elif col == 2:
                    callbacks = ['heal_player', 'health_upgrade', 'damage_upgrade', 'speed_upgrade']
                    keys      = ['heal',        'health_upgrade', 'damage_upgrade', 'speed_upgrade']
                    btn = Button(groups=self.game.buttons_sprites, pos=(x, y),
                                 image=self.game.buttons_frames[keys[row]],
                                 callback=callbacks[row])

                if btn:
                    self.buttons[row][col] = btn

    def can_buy(self, price):
        if price <= self.game.game_stats.money:
            self.game.game_stats.money -= price
            return True
        self.game.play_sound('not_money')
        return False

    def input(self):
        for row in self.buttons:
            for btn in row:
                if btn and btn.is_clicked():
                    cb = btn.callback

                    if cb == 'next_wave':
                        self.game.change_state('gameplay')
                        self.game.gameplay.start_wave_timer()

                    elif cb == 'heal_player':
                        player = self.game.player
                        if player.health < player.max_health and self.can_buy(self.game.game_stats.heal_price):
                            player.health = player.max_health
                            self.game.play_sound('heal')

                    elif cb == 'health_upgrade':
                        price = self.game.game_stats.get_upgrade_price('health')
                        if self.can_buy(price):
                            self.game.play_sound('skill_upgrade')
                            stats = self.game.game_stats
                            was_full = self.game.player.health == self.game.player.max_health
                            stats.health_upgrade += stats.health_upgrade_step
                            stats.update_skill_level()
                            self.game.player.max_health = stats.health_upgrade
                            if was_full:
                                self.game.player.health = stats.health_upgrade

                    elif cb == 'damage_upgrade':
                        price = self.game.game_stats.get_upgrade_price('damage')
                        if self.can_buy(price):
                            self.game.play_sound('skill_upgrade')
                            stats = self.game.game_stats
                            stats.damage_upgrade += stats.damage_upgrade_step
                            stats.update_skill_level()
                            self.game.current_gun.damage = stats.damage_upgrade

                    elif cb == 'speed_upgrade':
                        price = self.game.game_stats.get_upgrade_price('speed')
                        if self.can_buy(price):
                            self.game.play_sound('skill_upgrade')
                            stats = self.game.game_stats
                            stats.speed_upgrade += stats.speed_upgrade_step
                            stats.update_skill_level()
                            self.game.player.speed = stats.speed_upgrade

                    elif cb.startswith(('select_', 'buy_')):
                        _, gn = cb.split('_', 1)
                        if cb.startswith('select_'):
                            self.game.change_gun(gn)
                        else:
                            price = self.all_guns[gn].price
                            if self.can_buy(price):
                                self.game.available_weapons[gn] = self.all_guns[gn]
                                self.game.change_gun(gn)
                                self.game.play_sound('buy_gun')
                                btn.custom_image = self.game.buttons_frames[f'open_{gn}']
                                btn.image = btn.custom_image.copy()
                                btn.callback = f'select_{gn}'
                        self.update_gun_buttons_icons()

    def update_gun_buttons_icons(self):
        for row in self.buttons:
            for btn in row:
                if btn and btn.callback.startswith(('select_', 'buy_')):
                    _, gn = btn.callback.split('_', 1)
                    if btn.callback.startswith('select_'):
                        key = f'choosen_{gn}' if self.game.current_gun.gun_name == gn else f'open_{gn}'
                        btn.custom_image = self.game.buttons_frames[key]
                        btn.image = btn.custom_image.copy()

    def draw_stats(self):
        font  = self.game.s_font
        small = self.game.xs_font
        stats = self.game.game_stats
        color = (255, 255, 255)

        # upgrade levels (центральная колонка)
        mid_btn = self.buttons[0][1]
        if mid_btn:
            small_font = pygame.font.SysFont('monospace', 20)
            bx, by = mid_btn.rect.centerx, mid_btn.rect.bottom + 20
            lh = 28
            for i, (label, level) in enumerate([
                ('Здоровье', stats.health_level),
                ('Урон',     stats.damage_level),
                ('Скорость', stats.speed_level),
            ]):
                txt = small_font.render(f'{label}: {level}', True, color)
                self.display_surface.blit(txt, txt.get_rect(center=(bx, by + (i + 1) * lh)))

        # цены апгрейдов (правая колонка) — под кнопками
        stats.next_upgrage_price()
        price_map = {
            'heal':   stats.heal_price,
            'health': stats.next_health_upgrade_price,
            'damage': stats.next_damage_upgrade_price,
            'speed':  stats.next_speed_upgrade_price,
        }
        for row in range(4):
            btn = self.buttons[row][2]
            if not btn:
                continue
            prefix = btn.callback.split('_')[0]
            if prefix in price_map:
                price = price_map[prefix]
                can = stats.money >= price
                txt_col = '#2BCD3B' if can else '#E21A1A'
                txt = small.render(f'{price} $', True, txt_col)
                self.display_surface.blit(txt, txt.get_rect(center=(btn.rect.centerx - 34, btn.rect.centery + 2)))

        # цены оружия (левая колонка) + tooltip при наведении
        gun_settings = load_json(join('settings', 'gun_settings.json'))
        for row in range(4):
            btn = self.buttons[row][0]
            if not btn:
                continue
            _, gn = btn.callback.split('_', 1)
            if btn.callback.startswith('buy_'):
                price = self.all_guns[gn].price
                can = stats.money >= price
                txt = small.render(f'{price} $', True, '#2BCD3B' if can else '#E21A1A')
                self.display_surface.blit(txt, txt.get_rect(center=(btn.rect.centerx, btn.rect.bottom + 14)))

            if btn.was_hovered and gn in self.all_guns:
                desc = gun_settings.get(gn, {}).get('description', '')
                if desc:
                    draw_text_window(self.display_surface, (btn.rect.left, btn.rect.centery), desc)

        # деньги над окном
        money_txt = font.render(f'{stats.money} $', True, (255, 220, 0))
        self.display_surface.blit(
            money_txt,
            money_txt.get_rect(center=(self.window_rect.centerx, self.window_rect.top - 100))
        )

    def draw(self):
        super().draw()
        self.draw_stats()
        self.game.states['gameplay'].draw_game_ui()

    def update(self, dt):
        super().update(dt)
        self.input()
        self.update_gun_buttons_icons()


# ===================== Pause =====================

class Pause(InGameWindow):
    state_name = 'pause'
    music_state = 'gameplay'

    def __init__(self, game):
        super().__init__(game, title='Пауза', size=(400, 300))

    def on_enter(self):
        super().on_enter()
        self.game.game_paused = True

    def create_buttons(self):
        cx = self.window_rect.centerx
        self.resume_button = Button(
            groups=self.game.buttons_sprites,
            pos=(cx, self.window_rect.top + self.window_rect.height // 3),
            image=self.game.buttons_frames['resume']
        )
        self.menu_button = Button(
            groups=self.game.buttons_sprites,
            pos=(cx, self.window_rect.top + self.window_rect.height // 3 + 100),
            image=self.game.buttons_frames['menu']
        )

    def input(self):
        keys = pygame.key.get_pressed()
        prev_esc = getattr(self, '_prev_esc', False)
        just_esc = keys[pygame.K_ESCAPE] and not prev_esc
        self._prev_esc = bool(keys[pygame.K_ESCAPE])

        if just_esc or self.resume_button.is_clicked():
            self.game.game_paused = False
            self.game.change_state('gameplay', False)
        elif self.menu_button.is_clicked():
            # Плавное затухание только до чёрного, затем reset (player уже не нужен)
            clock = pygame.time.Clock()
            surface = pygame.display.get_surface()
            overlay = pygame.Surface(surface.get_size()).convert_alpha()
            for alpha in range(0, 256, 5):
                self.draw()
                overlay.fill((0, 0, 0, alpha))
                surface.blit(overlay, (0, 0))
                pygame.display.update()
                clock.tick(60)
            self.game.reset_game()

    def update(self, dt):
        super().update(dt)
        self.input()


# ===================== GameOver =====================

class GameOver:
    state_name = 'game_over'
    music_state = 'gameplay'

    def __init__(self, game):
        self.game = game

    def on_enter(self):
        self.game.game_paused = True
        stats = self.game.game_stats
        total = calculate_total_score(stats.kills, stats.wave)
        write_score(stats.kills, stats.wave, total)
        self.menu_button = Button(
            groups=self.game.buttons_sprites,
            pos=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 120),
            image=self.game.buttons_frames['menu']
        )

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
            (big_font.render('GAME OVER', True, (220, 40, 40)),            (cx, cy - 70)),
            (font.render('Нажмите R для рестарта', True, (255, 255, 255)), (cx, cy + 10)),
            (font.render(f'Убито: {stats.kills}   Волна: {stats.wave}', True, (200, 200, 200)), (cx, cy + 55)),
        ]:
            surface.blit(surf, surf.get_rect(center=pos))

        self.game.buttons_sprites.draw(surface)

    def update(self, dt):
        self.game.buttons_sprites.update(dt)
        if hasattr(self, 'menu_button') and self.menu_button.is_clicked():
            self.game.reset_game()
            return
