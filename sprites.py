import math
from random import randrange, choice
from tilemap import *
import heapq


class Player(pg.sprite.Sprite):
    def __init__(self, game, x, y):
        self.mouse_dir = None
        self.mouse_pos = None
        self.mouse_dist = None
        self.health = None

        self.groups = game.all_sprites
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = self.game.player_img
        self.rect = self.image.get_rect()
        self.pos = vec(x, y) * TILESIZE
        self.vel = vec(0, 0)
        self.rot = 0
        self.hit_rect = pg.Rect(0, 0, 25, 25)
        self.hit_rect.center = self.rect.center
        self.last_shot = 0
        self.bullet_color = 'GREEN'
        self.mines = 1

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
        left, _, right = pg.mouse.get_pressed()
        if keys[pg.K_SPACE] or left:
            shoot(self)
        if right and self.mines > 0:
            Mine(self.game, self, self.pos.x, self.pos.y)
            self.mines -= 1

        if self.health <= 0:
            self.kill()

    def move(self):
        self.vel = vec(PLAYER_SPEED, 0)

        self.rot = round(self.mouse_dir / 45) * 45

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

    def __init__(self, game, x, y):
        self.target = None
        self.rot_choice = None
        self.groups = game.all_sprites, game.mobs
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game

        self.image = self.game.mob_img
        self.reset_image = self.image
        self.rect = self.image.get_rect()
        self.boom_frame = 0

        self.pos = vec(x, y) * TILESIZE
        self.rect.center = self.pos
        self.vel = vec(0, 0)
        self.rot = 0
        self.hit_rect = pg.Rect(0, 0, 25, 25)
        self.hit_rect.center = self.rect.center
        self.last_shot = 0
        self.health = MOB_HEALTH
        self.dead = False

        self.bullet_color = 'RED'

    def move(self):
        self.rot_choice = randrange(0, 30)
        if self.rot_choice < 29:
            pass
        else:
            self.rot += choice([-1, 1]) * 90

        self.rot = round(self.rot / 90) * 90
        self.vel = vec(MOB_SPEED, 0)

    def update(self):
        self.target = self.game.player
        self.target_dist = self.target.pos - self.pos

        if self.target_dist.length_squared() < DETECT_RADIUS ** 2:
            ray = [self.pos, self.target.pos]
            blind = False
            for pair in self.game.wall_pairs:
                blind = intersect(pair, ray)
                if blind:
                    break

            if not blind:
                self.target_dir = self.target_dist.angle_to(vec(1, 0))
                self.rot = self.target_dir
                self.vel = vec(0, 0)
                shoot(self)

            else:
                self.move()
        else:
            self.move()

        self.image = pg.transform.rotate(self.reset_image, self.rot)
        self.rect = self.image.get_rect()
        self.rect.center = self.pos

        self.vel = self.vel.rotate((-self.rot))
        self.pos += self.vel * self.game.dt

        self.hit_rect.centerx = self.pos.x
        collisionx = collide_with_walls(self, self.game.walls, 'x')
        self.hit_rect.centery = self.pos.y
        collisiony = collide_with_walls(self, self.game.walls, 'y')
        self.rect.center = self.hit_rect.center

        if collisionx or collisiony:
            self.rot += choice([-90, 90, 180, 180])

        if self.health <= 0:
            if self.dead:
                explosion(self)
            else:
                self.last_frame = pg.time.get_ticks()
                self.dead = True

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


class Boss(Mob):

    def __init__(self, game, x, y):
        super().__init__(game, x, y)
        self.path = []
        self.image = self.game.boss_img
        self.reset_image = self.image
        self.reset_path = 0
        self.path_finder = Pathfinder(self.game.graph, self.game.obstacles, manhattan_distance)
        self.bullet_color = 'PURPLE'
        self.mines = 1

    def update(self):
        super().update()
        self.reset_path += 1

        if self.reset_path > 3 * FPS:
            self.reset_path = 0
            self.find_path()

        # if self.health <= 0:
        #     super().kill()

        if self.mines > 0:
            lay_mine = randrange(0, 500)
            if lay_mine == 1:
                Mine(self.game, self, self.pos.x, self.pos.y)
                self.mines -= 1

    def move(self):
        if not len(self.path) == 0:
            point = vec(self.path[0]) * TILESIZE + vec(TILESIZE / 2, TILESIZE / 2)
            direction = point - self.pos
            direction = direction.angle_to(vec(1, 0))
            self.rot = round(direction / 45) * 45

            if (point - self.pos).length_squared() < (0.25 * TILESIZE) ** 2:
                self.path = self.path[1:]
        else:
            self.target_dir = self.target_dist.angle_to(vec(1, 0))
            self.rot = round(self.target_dir / 45) * 45

        self.vel = vec(MOB_SPEED, 0)

    def find_path(self):
        start = tuple(self.pos // TILESIZE)
        end = tuple(self.target.pos // TILESIZE)
        self.path = self.path_finder.search(start, end)


class Mine(pg.sprite.Sprite):

    def __init__(self, game, sprite, x, y):
        self.groups = game.all_sprites, game.mines
        pg.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.sprite = sprite

        self.mine_frames = game.mine_imgs
        self.image = self.mine_frames[0]
        self.img_index = 0
        self.flick = 0

        self.boom_frames = game.boom_imgs
        self.boom_frame = 0

        self.rect = self.image.get_rect()
        self.pos = vec(x, y)
        self.rect.center = self.pos

        self.armed = False
        self.detonated = False
        self.placed_time = pg.time.get_ticks()
        self.timer = randrange(20000, 120000)

    def update(self):
        now = pg.time.get_ticks()

        if not self.armed and (now - self.placed_time) > 3000:
            self.armed = True
            self.image = self.mine_frames[1]

        if self.detonated:
            explosion(self)

        elif self.armed:
            if now - self.placed_time >= (self.timer - 5000):
                self.flicker()
                if now - self.placed_time >= self.timer:
                    self.boom()

            hits = pg.sprite.spritecollide(self, self.game.all_sprites, False)
            if len(hits) > 1:
                self.boom()

        self.rect = self.image.get_rect()
        self.rect.center = self.pos

    def flicker(self):
        self.flick += 1
        if self.flick % 15 == 0:
            self.img_index += 1
            self.img_index = self.img_index % 2
            self.image = self.mine_frames[self.img_index]

    def boom(self):
        self.sprite.mines += 1
        self.detonated = True
        for hit in self.game.all_sprites:
            if isinstance(hit, Wall) or hit == self:
                continue

            distance = (self.pos - hit.pos).length()
            if distance <= BLAST_RADIUS:
                if isinstance(hit, Mine):
                    if not hit.detonated:
                        hit.boom()
                else:
                    hit.kill()

        self.last_frame = pg.time.get_ticks()


class Pathfinder:
    def __init__(self, graph, obstacles, heuristic):
        self.graph = graph
        self.obstacles = obstacles
        self.heuristic = heuristic

    def search(self, start, end):
        # initialize the priority queue with the start node
        queue = [(0, start, [start])]
        # keep track of which nodes have been visited
        visited = set()

        # continue searching while there are still nodes in the queue
        while queue:
            # get the next node to search
            cost, node, path = heapq.heappop(queue)
            # mark the node as visited
            visited.add(node)

            # check if we have reached the end
            if node == end:
                return path

            # add all unvisited, non-obstacle neighbors to the queue
            for neighbor in self.graph[node]:
                if neighbor not in visited and neighbor not in self.obstacles:
                    # compute the heuristic value for the neighbor
                    heuristic_value = self.heuristic(neighbor, end)
                    # add the neighbor to the queue with the cost, heuristic value, and path
                    heapq.heappush(queue, (heuristic_value + 0.5 * len(path), neighbor, path + [neighbor]))

        # if the end was not reached, return an empty path
        return []


def manhattan_distance(node, target):
    return abs(node[0] - target[0]) + abs(node[1] - target[1])


def create_graph(map_data):
    # create an empty graph
    graph = {}
    obstacles = []

    # add a key for each tile in the map
    for y in range(map_data.height):
        for x in range(map_data.width):
            graph[(x, y)] = []

    # add neighbors for each tile
    for y in range(map_data.height):
        for x in range(map_data.width):
            # skip obstacles
            if map_data.getpixel((x, y)) == (0, 0, 0):
                obstacles.append((x, y))
            # add neighbors to the right, left, above, and below
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < map_data.width and 0 <= y + dy < map_data.height:
                    neighbor = (x + dx, y + dy)
                    # only add non-obstacle neighbors to the graph
                    if map_data.getpixel(neighbor) != (0, 0, 0):
                        graph[(x, y)].append(neighbor)
    return graph, obstacles


def explosion(sprite):
    now = pg.time.get_ticks()
    sprite.image = sprite.game.boom_imgs[sprite.boom_frame]
    sprite.rect = sprite.image.get_rect()
    sprite.rect.center = sprite.pos
    if (now - sprite.last_frame) > 75:
        sprite.last_frame = pg.time.get_ticks()
        sprite.boom_frame += 1
        if sprite.boom_frame >= len(sprite.game.boom_imgs):
            sprite.kill()


def shoot(sprite):
    now = pg.time.get_ticks()
    if now - sprite.last_shot > RATE:
        sprite.last_shot = now
        dir = vec(1, 0).rotate(-sprite.rot)
        pos = sprite.pos + BARREL_OFFSET.rotate(-sprite.rot)
        Bullet(sprite.game, pos, dir.rotate(randrange(-1, 1)), sprite.bullet_color)


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
            return True

    if dir == 'y':
        hits = pg.sprite.spritecollide(sprite, group, False, collide_hit_rect)
        if hits:
            if hits[0].rect.centery > sprite.hit_rect.centery:
                sprite.pos.y = hits[0].rect.top - sprite.hit_rect.height / 2
            if hits[0].rect.centery < sprite.hit_rect.centery:
                sprite.pos.y = hits[0].rect.bottom + sprite.hit_rect.height / 2
            sprite.vel.y = 0
            sprite.hit_rect.centery = sprite.pos.y
            return True


def intersect(segment1, segment2):
    start1, end1 = segment1
    start2, end2 = segment2

    # Calculate the slope and intercept of the first line
    if end1[0] - start1[0] == 0:
        slope1 = float('inf')
        intercept1 = start1[0]
    else:
        slope1 = (end1[1] - start1[1]) / (end1[0] - start1[0])
        intercept1 = start1[1] - slope1 * start1[0]

    # Calculate the slope and intercept of the second line
    if end2[0] - start2[0] == 0:
        slope2 = float('inf')
        intercept2 = start2[0]
    else:
        slope2 = (end2[1] - start2[1]) / (end2[0] - start2[0])
        intercept2 = start2[1] - slope2 * start2[0]

    # Check whether the lines are parallel
    if slope1 == slope2:
        return False  # Line segments do not intersect

    # Calculate the point of intersection of the two lines
    if slope1 == float('inf'):
        x = intercept1
        y = slope2 * x + intercept2
    elif slope2 == float('inf'):
        x = intercept2
        y = slope1 * x + intercept1
    else:
        x = (intercept2 - intercept1) / (slope1 - slope2)
        y = slope1 * x + intercept1

    # Check whether the point of intersection is within the range of both line segments
    return (min(start1[0], end1[0]) <= x <= max(start1[0], end1[0])) and (
            min(start2[0], end2[0]) <= x <= max(start2[0], end2[0])) and (
            min(start1[1], end1[1]) <= y <= max(start1[1], end1[1])) and (
            min(start2[1], end2[1]) <= y <= max(start2[1], end2[1]))
