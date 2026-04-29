from settings import *
import states.gameplay
from groups import AllSprites
from support import *
from sprites import *
from sound import Sound


class Game:
    def __init__(self):
        pygame.init()
        self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption('Blitzframe')
        self.clock = pygame.time.Clock()
        self.running = True

        self.music_volume = 0.3

        self.reset_game()

        self.sound = Sound(self)

    def reset_game(self):
        self.game_paused = False
        self.all_sprites = AllSprites()
        self.enemy_sprites = pygame.sprite.Group()
        self.bullet_sprites = pygame.sprite.Group()
        self.enemies_bullet_sprites = pygame.sprite.Group()

        if hasattr(self, 'player'):
            delattr(self, 'player')

        self.load_assets()

        self.states = {
            'gameplay': states.gameplay.Gameplay(self),
            'game_over': states.gameplay.GameOver(self),
        }

        self.current_state = self.states['gameplay']
        self.current_state.on_enter()

    def change_state(self, new_state: str, animation=False):
        self.current_state = self.states[new_state]
        self.current_state.on_enter()

    def load_assets(self):
        def scale_frame(surf, scale=2):
            return pygame.transform.scale(
                surf, (int(surf.get_width() * scale), int(surf.get_height() * scale))
            )

        self.enemies_frames_dict = {}
        for enemy_type in ['normal', 'fast', 'heavy']:
            frames = folder_importer('images', 'enemies', enemy_type)
            self.enemies_frames_dict[enemy_type] = {k: scale_frame(v) for k, v in frames.items()}

        # boss uses heavy sprite scaled up for visual distinction
        boss_base = folder_importer('images', 'enemies', 'heavy')
        self.enemies_frames_dict['first_boss'] = {k: scale_frame(v, scale=4) for k, v in boss_base.items()}

    def run(self):
        while self.running:
            dt = self.clock.tick(FRAMERATE) / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
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
