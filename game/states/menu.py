from settings import *
from ui import Button, Slider
from support import load_json


class Background:
    def __init__(self, screen_size, speed=20):
        self.surface = pygame.Surface(screen_size)
        self.surface.fill((15, 15, 25))
        self.offset = pygame.Vector2(0, 0)
        self.direction = pygame.Vector2(1, 1).normalize()
        self.speed = speed
        # subtle star-like dots
        self._dots = [
            (random.randint(0, screen_size[0]), random.randint(0, screen_size[1]),
             random.randint(1, 3), random.randint(80, 180))
            for _ in range(120)
        ]
        self._render()

    def _render(self):
        self.surface.fill((15, 15, 25))
        for x, y, r, a in self._dots:
            dot = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(dot, (255, 255, 255, a), (r, r), r)
            self.surface.blit(dot, (x - r, y - r))

    def draw(self, surface):
        surface.blit(self.surface, (0, 0))

    def update(self, dt):
        pass


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
        window_rect = pygame.Rect(0, WINDOW_HEIGHT // 2 - WINDOW_HEIGHT // 5, 480, 400)

        window_surf = pygame.Surface(window_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(window_surf, (50, 50, 50, 150), window_surf.get_rect(),
                         border_top_right_radius=20, border_bottom_right_radius=20)
        self.display_surface.blit(window_surf, window_rect.topleft)

        title = font.render('Лучшие результаты', True, (255, 255, 255))
        self.display_surface.blit(title, title.get_rect(midtop=(window_rect.centerx, window_rect.top + 15)))

        scores = load_json(join('settings', 'score.json'))
        for i, (key, entry) in enumerate(sorted(scores.items(), key=lambda x: int(x[0]))):
            if i >= 6:
                break
            text = f"{key}. Волны: {entry['waves']}  Убийства: {entry['kills']}  Очки: {entry['total']}"
            surf = entry_font.render(text, True, (220, 220, 220))
            self.display_surface.blit(surf, (window_rect.left + 20, window_rect.top + 90 + i * 46))

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
