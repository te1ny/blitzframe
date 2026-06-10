from settings import *
from ui import Button, Slider
from support import load_json


class Background:
    def __init__(self, screen_size, game):
        self.screen_size = screen_size
        self.game = game
        self.map_surface = None
        self.offset = pygame.Vector2(800, 600)
        self.scroll = pygame.Vector2(22, 11)
        self._max_x = self._max_y = 0
        self.overlay = pygame.Surface(screen_size, pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 130))

    def _build(self):
        tm = self.game.tilemap
        w, h = tm.level_width, tm.level_height
        self.map_surface = pygame.Surface((w, h))
        self.map_surface.fill((30, 50, 30))
        for x, y, image in tm.map.get_layer_by_name('Ground').tiles():
            if image:
                self.map_surface.blit(image, (x * TILE_SIZE, y * TILE_SIZE))
        self._max_x = max(w - self.screen_size[0], 0)
        self._max_y = max(h - self.screen_size[1], 0)

    def draw(self, surface):
        if self.map_surface is None:
            if hasattr(self.game, 'tilemap'):
                self._build()
            else:
                surface.fill((15, 25, 15))
                return
        ox = int(self.offset.x) % (self._max_x + 1) if self._max_x else 0
        oy = int(self.offset.y) % (self._max_y + 1) if self._max_y else 0
        surface.blit(self.map_surface, (-ox, -oy))
        surface.blit(self.overlay, (0, 0))

    def update(self, dt):
        if self.map_surface is None:
            return
        self.offset.x += self.scroll.x * dt
        self.offset.y += self.scroll.y * dt
        if self._max_x and self.offset.x > self._max_x:
            self.offset.x = 0
        if self._max_y and self.offset.y > self._max_y:
            self.offset.y = 0


class MainMenu:
    music_state = 'main_menu'

    def __init__(self, game):
        self.game = game
        self.display_surface = pygame.display.get_surface()

    def on_enter(self):
        self.create_buttons()

    def create_buttons(self):
        pass

    def draw(self):
        self.game.background.draw(self.display_surface)
        self.game.buttons_sprites.draw(self.display_surface)

    def update(self, dt):
        self.game.background.update(dt)
        self.game.buttons_sprites.update(dt)


class Menu(MainMenu):
    state_name = 'main_menu'

    def create_buttons(self):
        self.start_game_button = Button(
            groups=self.game.buttons_sprites,
            pos=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3),
            image=self.game.buttons_frames['new_game']
        )
        self.settings_button = Button(
            groups=self.game.buttons_sprites,
            pos=(WINDOW_WIDTH // 2,
                 WINDOW_HEIGHT // 3 + self.start_game_button.rect.height + 50),
            image=self.game.buttons_frames['settings']
        )
        self.exit_button = Button(
            groups=self.game.buttons_sprites,
            pos=(WINDOW_WIDTH // 2,
                 WINDOW_HEIGHT // 3 + (self.start_game_button.rect.height + 50) * 2),
            image=self.game.buttons_frames['exit']
        )

    def input(self):
        if self.start_game_button.is_clicked():
            self.game.change_state('gameplay')
        if self.settings_button.is_clicked():
            self.game.change_state('settings')
        if self.exit_button.is_clicked():
            self.game.running = False

    def draw_score(self):
        font = self.game.s_font
        entry_font = self.game.xs_font
        padding = 16
        window_rect = pygame.Rect(0, WINDOW_HEIGHT // 2 - WINDOW_HEIGHT // 5, 480, 400)

        window_surf = pygame.Surface(window_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(window_surf, (50, 50, 50, 150), window_surf.get_rect(),
                         border_top_right_radius=20, border_bottom_right_radius=20)

        title = font.render('Лучшие результаты', True, (255, 255, 255))
        window_surf.blit(title, title.get_rect(midtop=(window_rect.width // 2, 15)))

        scores = load_json(join('settings', 'score.json'))
        lh = entry_font.get_height() + 6
        for i, (key, entry) in enumerate(sorted(scores.items(), key=lambda x: int(x[0]))):
            if i >= 6:
                break
            text = f"{key}. Вл:{entry['waves']}  Уб:{entry['kills']}  Оч:{entry['total']}"
            surf = entry_font.render(text, True, (220, 220, 220))
            # обрезаем по ширине таблички
            max_w = window_rect.width - padding * 2
            if surf.get_width() > max_w:
                surf = surf.subsurface((0, 0, max_w, surf.get_height()))
            y = 75 + i * lh
            if y + surf.get_height() > window_rect.height - padding:
                break
            window_surf.blit(surf, (padding, y))

        self.display_surface.blit(window_surf, window_rect.topleft)

    def draw(self):
        super().draw()
        self.draw_score()

    def update(self, dt):
        super().update(dt)
        self.input()


class Settings(MainMenu):
    state_name = 'settings'

    def create_buttons(self):
        self.sounds_volume_slider = Slider(
            groups=self.game.buttons_sprites,
            pos=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3),
            size=(300, 20),
            initial_value=self.game.sounds_volume,
            label_text='Громкость эффектов:',
            label_font=self.game.m_font
        )
        self.music_volume_slider = Slider(
            groups=self.game.buttons_sprites,
            pos=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3 + 100),
            size=(300, 20),
            initial_value=self.game.music_volume,
            label_text='Громкость музыки:',
            label_font=self.game.m_font
        )
        self.back_button = Button(
            groups=self.game.buttons_sprites,
            pos=(150, 100),
            image=self.game.buttons_frames['back']
        )

    def input(self):
        keys = pygame.key.get_pressed()
        prev_esc = getattr(self, '_prev_esc', False)
        just_esc = keys[pygame.K_ESCAPE] and not prev_esc
        self._prev_esc = bool(keys[pygame.K_ESCAPE])

        if just_esc or self.back_button.is_clicked():
            self.game.change_state('main_menu')
            return

        self.game.sounds_volume = self.sounds_volume_slider.get_value()
        self.game.music_volume = self.music_volume_slider.get_value()

    def update(self, dt):
        super().update(dt)
        self.input()
