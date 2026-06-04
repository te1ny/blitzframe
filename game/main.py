from settings import *
import states.gameplay
import states.menu
from states.menu import Background
from groups import AllSprites
from support import *
from sprites import *
from sound import Sound
from tilemap import Tilemap


class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Blitzframe')
        self.clock = pygame.time.Clock()
        self.running = True

        self.music_volume = 0.3
        self.sounds_volume = 0.3

        create_score_json()

        self.reset_game()
        self.background = Background((WINDOW_WIDTH, WINDOW_HEIGHT), self)
        self.sound = Sound(self)

    def reset_game(self):
        self.game_paused = False
        self.all_sprites = AllSprites()
        self.buttons_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemies_bullet_sprites = pygame.sprite.Group()
        self.collision_sprites = pygame.sprite.Group()

        self.available_weapons = {'pistol': Pistol}

        self.tilemap = Tilemap(self.all_sprites, self.collision_sprites)
        self.tilemap.setup()

        if hasattr(self, 'background'):
            self.background.map_surface = None

        if hasattr(self, 'player'):
            delattr(self, 'player')

        if hasattr(self, 'sound'):
            self.sound.prev_state = None

        self.load_assets()

        self.states = {
            'main_menu':  states.menu.Menu(self),
            'settings':   states.menu.Settings(self),
            'gameplay':   states.gameplay.Gameplay(self),
            'shop':       states.gameplay.Shop(self),
            'game_over':  states.gameplay.GameOver(self),
        }

        self.current_state = self.states['main_menu']
        self.current_state.on_enter()

    def change_gun(self, gun, sound=True):
        if gun in self.available_weapons:
            self.current_gun.kill()
            self.current_gun = self.available_weapons[gun](
                (self.all_sprites, self.bullet_sprites), self.player
            )
            if sound:
                self.play_sound('gun_swap')

    def change_state(self, new_state: str, animation=True):
        def state_func():
            self.buttons_sprites.empty()
            self.current_state = self.states[new_state]
            self.current_state.on_enter()
        if animation:
            transition_effect(
                surface=self.display_surface,
                callback=state_func,
                draw_callback=lambda: self.current_state.draw()
            )
        else:
            state_func()

    def play_sound(self, name):
        if hasattr(self, 'sound') and name in self.sound.sounds:
            self.sound.sounds[name].play()

    def load_assets(self):
        def scale_frame(surf, scale=2):
            return pygame.transform.scale(
                surf, (int(surf.get_width() * scale), int(surf.get_height() * scale))
            )

        # player frames — 8 directions, sorted list of surfaces
        directions = ['down', 'left_down', 'left', 'left_up', 'up', 'right_up', 'right', 'right_down']
        self.player_frames = {}
        for direction in directions:
            frames_dict = folder_importer('images', 'player', direction)
            frames_list = [surf for _, surf in sorted(frames_dict.items(), key=lambda item: int(item[0]))]
            self.player_frames[direction] = [scale_frame(surf, scale=3) for surf in frames_list]

        # enemy frames
        self.enemies_frames_dict = {}
        for enemy_type in ['normal', 'fast', 'heavy']:
            frames = folder_importer('images', 'enemies', enemy_type)
            self.enemies_frames_dict[enemy_type] = {k: scale_frame(v) for k, v in frames.items()}

        boss_frames = folder_importer('images', 'enemies', 'first_boss')
        self.enemies_frames_dict['first_boss'] = {k: scale_frame(v, scale=0.8) for k, v in boss_frames.items()}

        # real button images
        self.buttons_frames = folder_importer('images', 'buttons')

        # placeholder button images for shop (generated programmatically)
        self._add_placeholder_buttons()

        # fonts (SysFont — no TTF file available)
        self.m_font  = pygame.font.SysFont('monospace', 40)
        self.l_font  = pygame.font.SysFont('monospace', 80)
        self.s_font  = pygame.font.SysFont('monospace', 30)
        self.xs_font = pygame.font.SysFont('monospace', 24)

    def _add_placeholder_buttons(self):
        font_sm = pygame.font.SysFont('monospace', 17)
        font_md = pygame.font.SysFont('monospace', 20)

        def make(text, color, size=(210, 76), font=None):
            f = font or font_sm
            surf = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(surf, (*color, 210), surf.get_rect(), border_radius=10)
            pygame.draw.rect(surf, (180, 180, 180, 120), surf.get_rect(), 1, border_radius=10)
            lines = text.split('\n')
            lh = f.get_height()
            total_h = lh * len(lines)
            start_y = (size[1] - total_h) // 2
            for i, line in enumerate(lines):
                txt = f.render(line, True, (240, 240, 240))
                surf.blit(txt, txt.get_rect(centerx=size[0] // 2, top=start_y + i * lh))
            return surf

        gun_labels = {
            'pistol':      'Пистолет',
            'shotgun':     'Дробовик',
            'sniper':      'Снайперка',
            'machine-gun': 'Автомат',
        }
        for gn, label in gun_labels.items():
            self.buttons_frames[f'open_{gn}']    = make(label,        (35, 80, 50))
            self.buttons_frames[f'locked_{gn}']  = make(f'[?] {label}', (55, 55, 55))
            self.buttons_frames[f'choosen_{gn}'] = make(label,        (140, 110, 15))

        self.buttons_frames['heal']             = make('Лечение\nполностью', (130, 35, 35))
        self.buttons_frames['health_upgrade']   = make('HP +',        (35, 110, 75), font=font_md)
        self.buttons_frames['damage_upgrade']   = make('Урон +',      (160, 75, 25), font=font_md)
        self.buttons_frames['speed_upgrade']    = make('Скорость +',  (25, 75, 155), font=font_md)
        self.buttons_frames['start_wave']       = make('Далее\n--->',  (20, 115, 55))

    def run(self):
        while self.running:
            dt = self.clock.tick(FRAMERATE) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()

            if not self.game_paused:
                self.all_sprites.update(dt)
            self.current_state.update(dt)
            self.sound.update(dt)

            self.display_surface.fill((30, 30, 30))
            self.current_state.draw()

            pygame.display.update()

        pygame.quit()


if __name__ == '__main__':
    game = Game()
    game.run()
