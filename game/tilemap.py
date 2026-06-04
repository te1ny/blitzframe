from settings import *
from sprites import Sprite


class Tilemap:
    def __init__(self, all_sprites, collision_sprites):
        self.all_sprites = all_sprites
        self.collision_sprites = collision_sprites
        self.map = load_pygame(join('data', 'maps', 'gameworld_forest.tmx'))
        self.level_width = self.map.width * TILE_SIZE
        self.level_height = self.map.height * TILE_SIZE

    def player_spawner(self):
        for obj in self.map.get_layer_by_name('Entities'):
            if obj.name == 'Player':
                return (obj.x, obj.y)
        return (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

    def enemy_spawner(self):
        spawners = []
        for obj in self.map.get_layer_by_name('Entities'):
            if obj.name == 'Enemy':
                spawners.append((obj.x, obj.y))
        return spawners

    def boss_spawner(self):
        for obj in self.map.get_layer_by_name('Entities'):
            if obj.name == 'Boss':
                return (obj.x, obj.y)
        return (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

    def setup(self):
        for x, y, image in self.map.get_layer_by_name('Ground').tiles():
            tile = Sprite(self.all_sprites, (x * TILE_SIZE, y * TILE_SIZE), image)
            tile.ground = True
        for obj in self.map.get_layer_by_name('Objects'):
            sprite = Sprite((self.all_sprites, self.collision_sprites), (obj.x, obj.y), obj.image)
            sprite.rect = sprite.rect.inflate(-(sprite.rect.width // 6), -(sprite.rect.height // 4))
        for obj in self.map.get_layer_by_name('Collisions'):
            Sprite(self.collision_sprites, (obj.x, obj.y), pygame.Surface((obj.width, obj.height), pygame.SRCALPHA))
