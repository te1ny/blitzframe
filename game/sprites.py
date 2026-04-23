from settings import *
from support import *
from math import degrees, atan2, radians, cos, sin

PLAYER_SIZE = 32


class Sprite(pygame.sprite.Sprite):
    def __init__(self, groups, pos, surf):
        super().__init__(groups)
        self.image = surf
        self.rect = self.image.get_rect(topleft=pos)


class AnimatedSprite(Sprite):
    def __init__(self, groups, pos, frames):
        self.frames, self.frame_index, self.animation_speed = frames, 0, 5
        super().__init__(groups, pos, self.frames[str(self.frame_index)])

    def animate(self, dt):
        self.frame_index += self.animation_speed * dt
        self.image = self.frames[str(int(self.frame_index) % len(self.frames))]


# =============== player =====================

class Player(pygame.sprite.Sprite):
    def __init__(self, groups, pos, game):
        super().__init__(groups)
        self.game = game
        surf = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
        surf.fill((220, 40, 40))
        self.image = surf
        self.rect = self.image.get_rect(center=pos)
        self.hitbox_rect = self.rect.copy()

        self.direction = pygame.Vector2()
        self.speed = 150
        self.state = 'down'

        self.health = self.max_health = 100
        self.player_alive = True
        self.damage_delay_timer = Timer(1000, False, False)

    def input(self):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        self.direction.y = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        if self.direction.length_squared() > 0:
            self.direction = self.direction.normalize()

    def move(self, dt):
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.rect.center = self.hitbox_rect.center

    def take_damage(self, enemy=None, damage=None):
        if not self.damage_delay_timer:
            if enemy:
                damage = enemy.damage
            self.health -= int(damage)
            self.damage_delay_timer.activate()
            self.game.all_sprites.shake(10)

    def death(self):
        self.player_alive = False
        surf = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
        surf.fill((80, 80, 80))
        self.image = surf

    def update(self, dt):
        if self.player_alive:
            self.input()
            self.move(dt)
            self.damage_delay_timer.update()


# =============== enemies ====================

class Enemy(AnimatedSprite):
    boss = False

    def __init__(self, groups, pos, frames, player, health_multiplier=1, speed_multiplier=1, damage_multiplier=1):
        super().__init__(groups, pos, frames)
        self.player = player
        self.collision_active = True
        self.direction = pygame.Vector2()
        self.hitbox_rect = self.rect.copy()

        info = load_json(join('settings', 'enemy_settings.json'))[self.name]
        self.speed = info['speed'] * speed_multiplier
        self.max_health = self.health = info['health'] * health_multiplier
        self.base_damage = self.damage = info['damage'] * damage_multiplier

        def reset_damage():
            self.damage = self.base_damage
            self.speed = info['speed'] * speed_multiplier
        self.deal_damage_timer = Timer(1000, func=reset_damage)
        self.death_timer = Timer(200, func=self.kill)

    def deal_damage(self):
        if not self.deal_damage_timer:
            self.damage = 0
            self.speed = 20
            self.deal_damage_timer.activate()

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            self.destroy()

    def destroy(self):
        self.collision_active = False
        self.death_timer.activate()
        self.animation_speed = 0
        self.image = pygame.mask.from_surface(self.image).to_surface()
        self.image.set_colorkey('black')

    def move(self, dt):
        direction = pygame.Vector2(self.player.rect.center) - pygame.Vector2(self.rect.center)
        if direction.length() > 0:
            self.direction = direction.normalize()
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self.rect.center = self.hitbox_rect.center

    def draw_health(self, surface, offset):
        bar_width, bar_height = 40, 6
        health_ratio = max(self.health / self.max_health, 0)
        current_width = int(bar_width * health_ratio)
        x = self.rect.centerx + offset.x - bar_width // 2
        y = self.rect.top + offset.y - 12
        pygame.draw.rect(surface, (60, 60, 60), (x, y, bar_width, bar_height), border_radius=3)
        pygame.draw.rect(surface, (220, 30, 30), (x, y, current_width, bar_height), border_radius=3)

    def update(self, dt):
        self.death_timer.update()
        if not self.death_timer:
            self.deal_damage_timer.update()
            self.move(dt)
            self.animate(dt)


class NormalEnemy(Enemy):
    name = 'normal'
    def __init__(self, groups, pos, frames, player, health_multiplier=1, speed_multiplier=1, damage_multiplier=1):
        super().__init__(groups, pos, frames, player, health_multiplier, speed_multiplier, damage_multiplier)


class FastEnemy(Enemy):
    name = 'fast'
    def __init__(self, groups, pos, frames, player, health_multiplier=1, speed_multiplier=1, damage_multiplier=1):
        super().__init__(groups, pos, frames, player, health_multiplier, speed_multiplier, damage_multiplier)


class HeavyEnemy(Enemy):
    name = 'heavy'
    def __init__(self, groups, pos, frames, player, health_multiplier=1, speed_multiplier=1, damage_multiplier=1):
        super().__init__(groups, pos, frames, player, health_multiplier, speed_multiplier, damage_multiplier)


# ================== bullets & guns ====================

class Bullet(Sprite):
    def __init__(self, groups, pos, surf, direction, damage=50, lifetime=2000, speed=600):
        super().__init__(groups, pos, surf)
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.lifetime_timer = Timer(lifetime, False, True, self.kill)

    def update(self, dt):
        self.rect.center += self.direction * self.speed * dt
        self.lifetime_timer.update()


class Gun(pygame.sprite.Sprite):
    def __init__(self, groups, player):
        self.all_sprites, self.bullet_sprites = groups
        self.player = player
        self.player_direction = pygame.Vector2(1, 0)

        gun_surf = pygame.Surface((16, 6), pygame.SRCALPHA)
        gun_surf.fill((200, 200, 50))
        self.gun_surf = gun_surf

        bullet_surf = pygame.Surface((6, 6))
        bullet_surf.fill((255, 220, 0))
        self.bullet_surf = bullet_surf

        super().__init__(self.all_sprites)
        self.image = self.gun_surf
        self.rect = self.image.get_rect(center=self.player.rect.center)

        info = load_json(join('settings', 'gun_settings.json'))
        self.base_damage = info['base_damage']
        self.damage = self.base_damage * info[self.gun_name]['damage_multiplier']
        self.cooldown = info[self.gun_name]['cooldown']

    def get_direction(self):
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        player_screen = pygame.Vector2(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        diff = mouse_pos - player_screen
        self.player_direction = diff.normalize() if diff.length() > 0 else pygame.Vector2(1, 0)

    def rotate_gun(self):
        angle = -degrees(atan2(self.player_direction.y, self.player_direction.x))
        self.image = pygame.transform.rotate(self.gun_surf, angle)
        offset = self.player_direction * 20
        self.rect = self.image.get_rect(
            center=(int(self.player.rect.centerx + offset.x), int(self.player.rect.centery + offset.y))
        )

    def create_bulet(self):
        pass

    def input(self):
        if pygame.mouse.get_pressed()[0]:
            self.create_bulet()

    def update(self, _):
        self.get_direction()
        self.rotate_gun()
        self.input()


class Pistol(Gun):
    gun_name = 'pistol'

    def __init__(self, groups, player):
        super().__init__(groups, player)
        self.cooldown_timer = Timer(self.cooldown)

    def create_bulet(self):
        if not self.cooldown_timer:
            Bullet(
                (self.all_sprites, self.bullet_sprites),
                self.rect.center,
                self.bullet_surf,
                self.player_direction,
                self.base_damage
            )
            self.cooldown_timer.activate()

    def update(self, dt):
        super().update(dt)
        self.cooldown_timer.update()
