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
            'pause':      states.gameplay.Pause(self),
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
            self.enemies_frames_dict[enemy_type] = {k: scale_frame(v, scale=1.2) for k, v in frames.items()}

        boss_frames = folder_importer('images', 'enemies', 'first_boss')
        self.enemies_frames_dict['first_boss'] = {k: scale_frame(v, scale=1.3) for k, v in boss_frames.items()}

        # button images
        self.buttons_frames = folder_importer('images', 'buttons')

        # fonts (SysFont — no TTF file available)
        self.m_font  = pygame.font.SysFont('monospace', 40)
        self.l_font  = pygame.font.SysFont('monospace', 80)
        self.s_font  = pygame.font.SysFont('monospace', 30)
        self.xs_font = pygame.font.SysFont('monospace', 24)

    def run(self):
        while self.running:
            dt = self.clock.tick(FRAMERATE) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset_game()
                if hasattr(self.current_state, 'on_event'):
                    self.current_state.on_event(event)

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
