from random import randrange
import numpy as np
from tilemap import *

vec = pg.math.Vector2


class Player(pg.sprite.Sprite):

    def __init__(self, game, x, y):
        self.mouse_dir = None
        self.mouse_pos = None
        self.mouse_dist = None

        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = self.game.player_img
        self.rect = self.image.get_rect()
        self.pos = vec(x, y) * TILESIZE
        self.vel = vec(0, 0)
        self.rot = 0
        self.hit_rect = pg.Rect(0, 0, 40, 40)
        self.hit_rect.center = self.rect.center
        self.last_shot = 0
        self.health = len(self.game.mobs) * PLAYER_HEALTH

    def update(self):
        self.mouse_pos = vec(pg.mouse.get_pos())
        self.mouse_dist = self.mouse_pos - self.game.offset
        self.mouse_dir = self.mouse_dist.angle_to(vec(1, 0))
        if self.mouse_dist.length_squared() < 125 ** 2:
            self.rot = self.mouse_dir % 360
            self.vel = vec(0, 0)
        else:
            self.move()
            self.pos += self.vel * self.game.dt
        self.image = pg.transform.rotate(self.game.player_img, self.rot)
        self.rect = self.image.get_rect()
        self.rect.center = self.pos
        self.hit_rect.centerx = self.pos.x
        collide_with_walls(self, self.game.walls, 'x')
        self.hit_rect.centery = self.pos.y
        collide_with_walls(self, self.game.walls, 'y')
        self.rect.center = self.hit_rect.center
        keys = pg.key.get_pressed()
        if keys[pg.K_SPACE]:
            shoot(self, 'GREEN')

    def move(self):
        self.vel = vec(PLAYER_SPEED, 0)
        if -30 < self.mouse_dir < 30:
            self.rot = 0
        elif 30 < self.mouse_dir < 60:
            self.rot = 45
        elif 60 < self.mouse_dir < 120:
            self.rot = 90
        elif 120 < self.mouse_dir < 150:
            self.rot = 135
        elif 150 < self.mouse_dir < 210:
            self.rot = 180
        elif -150 < self.mouse_dir < -120:
            self.rot = -135
        elif -120 < self.mouse_dir < -60:
            self.rot = -90
        elif -60 < self.mouse_dir < -30:
            self.rot = -45
        self.vel = self.vel.rotate((-self.rot))


class Wall(pg.sprite.Sprite):

    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.walls
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pg.Surface((TILESIZE, TILESIZE))
        self.image.fill(BLACK)
        self.rect = self.image.get_rect()
        self.pos = vec(x, y) * TILESIZE
        self.rect.x = self.pos.x
        self.rect.y = self.pos.y


class Bullet(pg.sprite.Sprite):

    def __init__(self, game, pos, direction, color):
        self.groups = game.all_sprites, game.bullets
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = game.bullet_imgs[color]
        self.rect = self.image.get_rect()
        self.pos = vec(pos)
        self.rect.center = pos
        self.vel = direction * BULLET_SPEED
        self.spawn_time = pg.time.get_ticks()

    def update(self):
        self.pos += self.vel * self.game.dt
        self.rect.center = self.pos
        if pg.sprite.spritecollideany(self, self.game.walls):
            self.kill()
        if pg.time.get_ticks() - self.spawn_time > 2000:
            self.kill()


class Mob(pg.sprite.Sprite):

    def __init__(self, game, x, y, mob_type='normal'):
        self.target = None
        self.rot_choice = None
        self.hit = None
        self.wall_angle = None
        self.dist = None
        self.walls = None

        self.groups = game.all_sprites, game.mobs
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = self.game.mob_img
        self.rect = self.image.get_rect()
        self.pos = vec(x, y) * TILESIZE
        self.rect.center = self.pos
        self.vel = vec(0, 0)
        self.rot = 0
        self.hit_rect = pg.Rect(0, 0, TILESIZE, TILESIZE)
        self.hit_rect.center = self.rect.center
        self.last_shot = 0
        self.health = MOB_HEALTH
        self.hit_pos = vec(0, 0)
        self.type = mob_type

    def get_walls(self):
        self.walls = self.game.wall_pos_vecs

    def check_dist(self, pos):
        self.dist = (pos - self.pos).length_squared()
        if self.dist < self.dist_limit:
            return True
        else:
            return False

    def check_dir(self, pos):
        self.wall_angle = (pos - self.pos).angle_to(vec(1, 0))
        if -self.fov < (self.target_dir - self.wall_angle) < self.fov:
            return True
        else:
            return False

    def move(self):
        self.rot_choice = randrange(0, 100)
        if 2.5 < self.rot_choice < 97.5:
            self.rot += 0
        elif 2.5 < self.rot_choice:
            self.rot += 90
        elif 97.5 > self.rot_choice:
            self.rot += -90

        self.rot -= (self.rot % 90)
        self.vel = vec(MOB_SPEED, 0)

    def update(self):
        self.hit = 0
        self.target = self.game.player
        self.target_dist = self.target.pos - self.pos

        if self.target_dist.length_squared() < DETECT_RADIUS ** 2:
            self.dist_limit = self.target_dist.length_squared()
            self.fov = FOV
            self.target_dir = self.target_dist.angle_to(vec(1, 0))
            self.obst = list(filter(self.check_dist, self.walls))
            self.obst2 = list(filter(self.check_dir, self.obst))
            if len(self.obst2) == 0:
                self.dist_limit = cRAD ** 2
                self.fov = cFOV
                self.obst3 = list(filter(self.check_dir, list(filter(self.check_dist, self.walls))))
                if len(self.obst3) == 0:

                else:
                    self.move()
            else:
                self.move()
        else:
            self.move()
        self.image = pg.transform.rotate(self.game.mob_img, self.rot)
        self.rect = self.image.get_rect()
        self.rect.center = self.pos
        self.vel = self.vel.rotate((-self.rot))
        self.pos += self.vel * self.game.dt
        self.hit_rect.centerx = self.pos.x
        collide_with_walls(self, self.game.walls, 'x')
        self.hit_rect.centery = self.pos.y
        collide_with_walls(self, self.game.walls, 'y')
        self.rect.center = self.hit_rect.center
        if self.health <= 0:
            self.kill()

    def draw_health(self):
        if self.health > 6:
            col = GREEN
        elif self.health > 3:
            col = YELLOW
        else:
            col = RED
        width = int(50 * self.health / MOB_HEALTH)
        self.health_bar = pg.Rect(0, 0, width, 7)
        if self.health < MOB_HEALTH:
            pg.draw.rect(self.image, col, self.health_bar)


def shoot(sprite, color):
    now = pg.time.get_ticks()
    if now - sprite.last_shot > RATE:
        sprite.last_shot = now
        dir = vec(1, 0).rotate(-sprite.rot)
        pos = sprite.pos + BARREL_OFFSET.rotate(-sprite.rot)
        Bullet(sprite.game, pos, dir.rotate(randrange(-1, 1)), color)


def collide_hit_rect(one, two):
    return one.hit_rect.colliderect(two.rect)


def collide_with_walls(sprite, group, dir):
    if dir == 'x':
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        if hits:
            if hits[0].rect.centerx > sprite.hit_rect.centerx:
                sprite.pos.x = hits[0].rect.left - sprite.hit_rect.width / 2
            if hits[0].rect.centerx < sprite.hit_rect.centerx:
                sprite.pos.x = hits[0].rect.right + sprite.hit_rect.width / 2
            sprite.vel.x = 0
            sprite.hit_rect.centerx = sprite.pos.x
    if dir == 'y':
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        if hits:
            if hits[0].rect.centery > sprite.hit_rect.centery:
                sprite.pos.y = hits[0].rect.top - sprite.hit_rect.height / 2
            if hits[0].rect.centery < sprite.hit_rect.centery:
                sprite.pos.y = hits[0].rect.bottom + sprite.hit_rect.height / 2
            sprite.vel.y = 0
            sprite.hit_rect.centery = sprite.pos.y
