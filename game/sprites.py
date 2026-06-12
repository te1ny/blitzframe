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
    def __init__(self, groups, pos, frames, game):
        super().__init__(groups)
        self.game = game
        self.frames = frames
        self.state = 'down'
        self.last_state = 'down'
        self.frame_index = 1

        self.death_frame = pygame.image.load(join('images', 'player', 'death.png')).convert_alpha()
        self.death_frame = pygame.transform.scale(
            self.death_frame,
            (int(self.death_frame.get_width() * 3), int(self.death_frame.get_height() * 3))
        )

        self.image = self.frames[self.state][self.frame_index]
        self.rect = self.image.get_rect(center=pos)
        self.hitbox_rect = self.rect.inflate(-30, -50)

        self.direction = pygame.Vector2()
        self.speed = 150

        self.health = self.max_health = 100
        self.player_alive = True
        self.damage_delay_timer = Timer(1000, False, False)

        self.step_cooldown = False
        def _step_reset(): self.step_cooldown = False
        self.step_timer = Timer(400, False, False, _step_reset)

    def get_state(self):
        x, y = self.direction.x, self.direction.y
        if x == 0 and y == 0:
            return self.last_state
        if x > 0 and y < 0: return 'right_up'
        if x > 0 and y > 0: return 'right_down'
        if x < 0 and y < 0: return 'left_up'
        if x < 0 and y > 0: return 'left_down'
        if x > 0: return 'right'
        if x < 0: return 'left'
        if y > 0: return 'down'
        if y < 0: return 'up'
        return self.last_state

    def animate(self, dt):
        state = self.get_state()
        moving = self.direction.length_squared() > 0
        if moving:
            self.frame_index += 10 * dt
            self.last_state = state
        else:
            self.frame_index = 1
            state = self.last_state
        frame_list = self.frames[state]
        self.image = frame_list[int(self.frame_index) % len(frame_list)]
        self.state = state

    def input(self):
        keys = pygame.key.get_pressed()
        self.direction.x = int(keys[pygame.K_d]) - int(keys[pygame.K_a])
        self.direction.y = int(keys[pygame.K_s]) - int(keys[pygame.K_w])
        if self.direction.length_squared() > 0:
            self.direction = self.direction.normalize()

        if (not self.step_cooldown and self.direction.length_squared() > 0
                and hasattr(self.game, 'sound') and self.game.sound.step_sounds):
            random.choice(self.game.sound.step_sounds).play()
            self.step_cooldown = True
            self.step_timer.activate()

    def _collision(self, axis):
        for sprite in self.game.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if axis == 'horizontal':
                    if self.direction.x > 0: self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0: self.hitbox_rect.left  = sprite.rect.right
                else:
                    if self.direction.y > 0: self.hitbox_rect.bottom = sprite.rect.top
                    if self.direction.y < 0: self.hitbox_rect.top    = sprite.rect.bottom

    def move(self, dt):
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self._collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self._collision('vertical')
        self.rect.center = self.hitbox_rect.center

    def take_damage(self, enemy=None, damage=None):
        if not self.damage_delay_timer:
            if enemy:
                damage = enemy.damage
            self.health -= int(damage)
            self.damage_delay_timer.activate()
            self.game.all_sprites.shake(10)
            self.game.play_sound('player_damage')

    def death(self):
        self.player_alive = False
        self.image = self.death_frame

    def update(self, dt):
        if self.player_alive:
            self.input()
            self.move(dt)
            self.animate(dt)
            self.damage_delay_timer.update()
            self.step_timer.update()


# =============== enemies ====================

class Enemy(AnimatedSprite):
    boss = False

    def __init__(self, groups, pos, frames, player, health_multiplier=1, speed_multiplier=1, damage_multiplier=1):
        super().__init__(groups, pos, frames)
        self.player = player
        self.collision_active = True
        self.direction = pygame.Vector2()
        self.hitbox_rect = self.rect.copy()

        self.speed_multiplier = speed_multiplier

        info = load_json(join('settings', 'enemy_settings.json'))[self.name]
        self.speed = info['speed'] * speed_multiplier
        self.max_health = self.health = info['health'] * health_multiplier
        self.base_damage = self.damage = info['damage'] * damage_multiplier

        def reset_damage():
            self.damage = self.base_damage
            self.speed = info['speed'] * speed_multiplier
        self.deal_damage_timer = Timer(1000, func=reset_damage)
        self.death_timer = Timer(200, func=self.kill)
        self.bump_timer = Timer(0)

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
        self.player.game.play_sound('enemy_kill')

    def _collision(self, axis):
        for sprite in self.player.game.collision_sprites:
            if sprite.rect.colliderect(self.hitbox_rect):
                if axis == 'horizontal':
                    if self.direction.x > 0: self.hitbox_rect.right = sprite.rect.left
                    if self.direction.x < 0: self.hitbox_rect.left  = sprite.rect.right
                else:
                    if self.direction.y > 0: self.hitbox_rect.bottom = sprite.rect.top
                    if self.direction.y < 0: self.hitbox_rect.top    = sprite.rect.bottom

                if not self.bump_timer:
                    offset = pygame.Vector2(self.player.rect.center) - pygame.Vector2(self.rect.center)
                    if axis == 'horizontal':
                        self.direction = pygame.Vector2(0, -1 if offset.y < 0 else 1)
                        duration = int(sprite.rect.height * 11)
                    else:
                        self.direction = pygame.Vector2(-1 if offset.x < 0 else 1, 0)
                        duration = int(sprite.rect.width * 11)
                    self.bump_timer = Timer(duration)
                    self.bump_timer.activate()

    def move(self, dt):
        if not self.bump_timer:
            direction = pygame.Vector2(self.player.rect.center) - pygame.Vector2(self.rect.center)
            if direction.length() > 0:
                self.direction = direction.normalize()
        self.hitbox_rect.x += self.direction.x * self.speed * dt
        self._collision('horizontal')
        self.hitbox_rect.y += self.direction.y * self.speed * dt
        self._collision('vertical')
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
        self.bump_timer.update()
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


class FirstBoss(Enemy):
    name = 'first_boss'
    boss = True

    def __init__(self, groups, pos, frames, player, health_multiplier=1, speed_multiplier=1, damage_multiplier=1):
        super().__init__(groups, pos, frames, player, health_multiplier, speed_multiplier, damage_multiplier)
        self.game = player.game
        self.attack_timer = Timer(5000, True, True, self.attack)
        self.bullet_surf = pygame.image.load(join('images', 'guns', 'bullet.png')).convert_alpha()
        self.attack_timers_list = []

    def attack(self):
        attack_list = [
            self.star_attack,
            self.laser_attack,
            self.triple_shot_attack,
            self.wave_attack,
            self.spiral_attack,
        ]
        self.attack_timers_list = []
        number_of_attacks = 6
        attacks_delay = 400
        current_attack = random.choice(attack_list)
        for i in range(1, number_of_attacks + 1):
            self.attack_timers_list.append(Timer(attacks_delay * i, False, True, current_attack))

    def spiral_attack(self):
        num_bullets = 8
        self.spiral_angle = getattr(self, 'spiral_angle', 0) + 10
        self.game.play_sound('laser_shot')
        for i in range(num_bullets):
            angle = radians(self.spiral_angle + (360 / num_bullets) * i)
            direction = pygame.Vector2(cos(angle), sin(angle))
            Bullet(
                (self.game.all_sprites, self.game.enemies_bullet_sprites),
                self.rect.center, self.bullet_surf, direction,
                self.damage, lifetime=6000, speed=int(250 * self.speed_multiplier)
            )

    def wave_attack(self):
        bullets_per_ring = 12
        self.game.play_sound('laser_shot')
        for i in range(bullets_per_ring):
            angle = radians((360 / bullets_per_ring) * i)
            direction = pygame.Vector2(cos(angle), sin(angle))
            Bullet(
                (self.game.all_sprites, self.game.enemies_bullet_sprites),
                self.rect.center, self.bullet_surf, direction,
                self.damage, lifetime=7000, speed=int(190 * self.speed_multiplier)
            )

    def laser_attack(self):
        self.game.play_sound('laser_shot')
        direction = (pygame.Vector2(self.game.player.rect.center) - pygame.Vector2(self.rect.center)).normalize()
        Bullet(
            (self.game.all_sprites, self.game.enemies_bullet_sprites),
            self.rect.center, self.bullet_surf, direction,
            self.damage, lifetime=3000, speed=int(460 * self.speed_multiplier)
        )

    def triple_shot_attack(self):
        self.game.play_sound('laser_shot')
        direction = (pygame.Vector2(self.game.player.rect.center) - pygame.Vector2(self.rect.center)).normalize()
        for a in [-15, 0, 15]:
            rotated = direction.rotate(a)
            Bullet(
                (self.game.all_sprites, self.game.enemies_bullet_sprites),
                self.rect.center, self.bullet_surf, rotated,
                self.damage, lifetime=5000, speed=int(270 * self.speed_multiplier)
            )

    def star_attack(self):
        self.game.play_sound('laser_shot')
        for d in [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]:
            direction = pygame.Vector2(*d).normalize()
            Bullet(
                (self.game.all_sprites, self.game.enemies_bullet_sprites),
                self.rect.center, self.bullet_surf, direction,
                self.damage, lifetime=10000, speed=int(300 * self.speed_multiplier)
            )

    def draw_health(self, surface, *args):
        bar_width, bar_height = 500, 30
        x = (WINDOW_WIDTH - bar_width) // 2
        y = 20
        health_ratio = max(self.health / self.max_health, 0)
        current_width = int(bar_width * health_ratio)
        pygame.draw.rect(surface, (60, 60, 60), (x, y, bar_width, bar_height), border_radius=8)
        pygame.draw.rect(surface, (220, 30, 30), (x, y, current_width, bar_height), border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255), (x, y, bar_width, bar_height), 2, border_radius=8)
        font = pygame.font.SysFont('monospace', 20, bold=True)
        text = font.render('BOSS', True, (255, 255, 255))
        surface.blit(text, text.get_rect(center=(WINDOW_WIDTH // 2, y + bar_height // 2)))

    def update(self, dt):
        super().update(dt)
        self.attack_timer.update()
        for timer in self.attack_timers_list:
            timer.update()


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

        self.gun_surf = self.load_surf()
        self.gun_surf = pygame.transform.smoothscale(
            self.gun_surf,
            (int(self.gun_surf.get_width() * 0.7), int(self.gun_surf.get_height() * 0.7))
        )
        self.bullet_surf = pygame.image.load(join('images', 'guns', 'bullet.png')).convert_alpha()

        super().__init__(self.all_sprites)
        self.z_index = 1
        self.image = self.gun_surf
        self.rect = self.image.get_rect(center=self.player.rect.center)

        info = load_json(join('settings', 'gun_settings.json'))
        self.base_damage = info['base_damage']
        self.damage = self.base_damage * info[self.gun_name]['damage_multiplier']
        self.cooldown = info[self.gun_name]['cooldown']

    def load_surf(self):
        surf = pygame.Surface((16, 6), pygame.SRCALPHA)
        surf.fill((200, 200, 50))
        return surf

    def get_direction(self):
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        player_screen = pygame.Vector2(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        diff = mouse_pos - player_screen
        self.player_direction = diff.normalize() if diff.length() > 0 else pygame.Vector2(1, 0)

    def rotate_gun(self):
        angle = -degrees(atan2(self.player_direction.y, self.player_direction.x))
        flip = self.player_direction.x < 0
        gun_image = pygame.transform.flip(self.gun_surf, False, flip)
        self.image = pygame.transform.rotate(gun_image, angle)
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
        if hasattr(self.player.game, 'game_stats'):
            self.base_damage = self.player.game.game_stats.damage_upgrade
        self.get_direction()
        self.rotate_gun()
        self.input()


class Pistol(Gun):
    gun_name = 'pistol'
    price = 0

    def __init__(self, groups, player):
        super().__init__(groups, player)
        self.cooldown_timer = Timer(self.cooldown)

    def load_surf(self):
        return pygame.image.load(join('images', 'guns', 'pistol.png')).convert_alpha()

    def create_bulet(self):
        if not self.cooldown_timer:
            self.player.game.play_sound('pistol_shot')
            Bullet(
                (self.all_sprites, self.bullet_sprites),
                self.rect.center, self.bullet_surf,
                self.player_direction, self.base_damage
            )
            self.cooldown_timer.activate()

    def update(self, dt):
        super().update(dt)
        self.cooldown_timer.update()


class Shotgun(Gun):
    gun_name = 'shotgun'
    price = 150

    def __init__(self, groups, player):
        super().__init__(groups, player)
        self.cooldown_timer = Timer(self.cooldown)

    def load_surf(self):
        return pygame.image.load(join('images', 'guns', 'shotgun.png')).convert_alpha()

    def create_bulet(self):
        if not self.cooldown_timer:
            self.player.game.play_sound('shotgun_shot')
            self.player.game.play_sound('shotgun_reload')
            base_angle = atan2(self.player_direction.y, self.player_direction.x)
            for _ in range(7):
                angle = base_angle + radians(random.uniform(-17.5, 17.5))
                direction = pygame.Vector2(cos(angle), sin(angle))
                Bullet(
                    (self.all_sprites, self.bullet_sprites),
                    self.rect.center, self.bullet_surf,
                    direction, self.damage, lifetime=380, speed=1000
                )
            self.cooldown_timer.activate()

    def update(self, dt):
        super().update(dt)
        self.cooldown_timer.update()


class SniperRifle(Gun):
    gun_name = 'sniper'
    price = 200

    def __init__(self, groups, player):
        super().__init__(groups, player)
        self.cooldown_timer = Timer(self.cooldown)

    def load_surf(self):
        return pygame.image.load(join('images', 'guns', 'sniper.png')).convert_alpha()

    def create_bulet(self):
        if not self.cooldown_timer:
            self.player.game.play_sound('sniper_shot')
            self.reload_timer = Timer(400, False, True, lambda: self.player.game.play_sound('sniper_reload'))
            Bullet(
                (self.all_sprites, self.bullet_sprites),
                self.rect.center, self.bullet_surf,
                self.player_direction, self.damage, lifetime=2000, speed=3000
            )
            self.cooldown_timer.activate()

    def update(self, dt):
        super().update(dt)
        self.cooldown_timer.update()
        if hasattr(self, 'reload_timer'):
            self.reload_timer.update()


class MachineGun(Gun):
    gun_name = 'machine-gun'
    price = 180

    def __init__(self, groups, player):
        super().__init__(groups, player)
        self.cooldown_timer = Timer(self.cooldown)

    def load_surf(self):
        return pygame.image.load(join('images', 'guns', 'machine-gun.png')).convert_alpha()

    def create_bulet(self):
        if not self.cooldown_timer:
            self.player.game.play_sound('machine-gun_shot')
            Bullet(
                (self.all_sprites, self.bullet_sprites),
                self.rect.center, self.bullet_surf,
                self.player_direction, self.damage, lifetime=1000, speed=600
            )
            self.cooldown_timer.activate()

    def update(self, dt):
        super().update(dt)
        self.cooldown_timer.update()
