from os import path
from sprites import *
from tilemap import *
from pprint import pprint


def draw_player_health(surf, x, y, pct):
    if pct < 0:
        pct = 0
    BAR_LENGTH = 100
    BAR_HEIGHT = 20
    fill = pct * BAR_LENGTH
    outline_rect = pg.Rect(x, y, BAR_LENGTH, BAR_HEIGHT)
    fill_rect = pg.Rect(x, y, fill, BAR_HEIGHT)
    if pct > 0.6:
        col = GREEN
    elif pct > 0.3:
        col = YELLOW
    else:
        col = RED
    pg.draw.rect(surf, col, fill_rect)
    pg.draw.rect(surf, WHITE, outline_rect, 2)


class Game:

    def __init__(self):
        # initialize game window
        pg.init()
        pg.mixer.init()
        self.screen = pg.display.set_mode((WIDTH, HEIGHT))
        pg.display.set_caption(TITLE)
        self.clock = pg.time.Clock()
        self.running = True
        self.font_name = pg.font.match_font(FONT)
        self.load_data()

    def load_data(self):
        # setup directories
        game_dir = path.dirname(__file__)
        img_dir = path.join(game_dir, 'img')
        map_dir = path.join(game_dir, 'maps')
        # Load map
        self.map = Map(path.join(map_dir, 'Map.txt'))
        # Load imgs
        self.player_img = pg.image.load(path.join(img_dir, 'player.png')).convert_alpha()
        self.player_img = pg.transform.scale(self.player_img, (50, 25))
        self.bullet_imgs = {}
        self.bullet_imgs['GREEN'] = pg.image.load(path.join(img_dir, 'bullet1.png')).convert_alpha()
        self.bullet_imgs['RED'] = pg.image.load(path.join(img_dir, 'bullet2.png')).convert_alpha()
        self.mob_img = pg.image.load(path.join(img_dir, 'mob.png')).convert_alpha()
        self.mob_img = pg.transform.scale(self.mob_img, (50, 25))

    def new(self):
        # initiate sprite groups
        self.all_sprites = pg.sprite.LayeredUpdates()
        self.walls = pg.sprite.Group()
        self.bullets = pg.sprite.Group()
        self.mobs = pg.sprite.Group()
        self.wall_pos_vecs = []
        self.wall_pairs = []

        # create map from map_data
        for row, tiles in enumerate(self.map.data):
            for col, tile in enumerate(tiles):
                if tile == '1':
                    self.wall = Wall(self, col, row)
                    self.wall_pos_vecs.append(self.wall.pos)
                if tile == 'P':
                    self.player = Player(self, col, row)
                if tile == 'M':
                    self.mob = Mob(self, col, row)
        self.draw_rects = False

        for mob in self.mobs:
            mob.get_walls()

        for i, vector1 in enumerate(self.wall_pos_vecs):
            for vector2 in self.wall_pos_vecs[i + 1:]:
                distance = vector1.distance_to(vector2)
                if distance <= TILESIZE:
                    self.wall_pairs.append([vector1 + 2 * [TILESIZE // 2], vector2 + 2*[TILESIZE // 2]])

        pprint(self.wall_pairs)

        self.camera = Camera(self.map.width, self.map.height)
        self.run()

    def run(self):
        # game loop
        self.playing = True
        while self.playing:
            self.clock.tick(FPS)
            self.dt = self.clock.tick(FPS) / 1000
            self.events()
            self.update()
            self.draw()

    def events(self):
        # game loop events
        for event in pg.event.get():
            # Check for closing
            if event.type == pg.QUIT:
                if self.playing:
                    self.playing = False
                self.running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.playing = False
                    self.running = False
                if event.key == pg.K_h:
                    self.draw_rects = not self.draw_rects
        # bullet hits
        hits = pg.sprite.groupcollide(self.mobs, self.bullets, False, True, collide_hit_rect)
        for hit in hits:
            hit.health -= BULLET_DAMAGE * len(hits[hit])
        hits = pg.sprite.spritecollide(self.player, self.bullets, True, collide_hit_rect)
        for hit in hits:
            self.player.health -= BULLET_DAMAGE
            if self.player.health <= 0:
                self.playing = False
                self.running = False

    def update(self):
        # game loop update
        self.player_pos = self.camera.apply(self.player)
        self.offset = self.player_pos.center
        self.all_sprites.update()
        self.camera.update(self.player)

    def draw(self):
        # pg.display.set_caption("{:.2f}".format(self.offset.length()))
        # game loop draw
        self.screen.fill(BGCOLOR)
        for sprite in self.all_sprites:
            if isinstance(sprite, Mob):
                sprite.draw_health()
            self.screen.blit(sprite.image, self.camera.apply(sprite))

        if self.draw_rects:
            pg.draw.rect(self.screen, DARKGREY, self.camera.apply_rect(self.player.rect), 2)
            pg.draw.rect(self.screen, GREY, self.camera.apply_rect(self.player.hit_rect), 2)

            for wall in self.walls:
                pg.draw.rect(self.screen, GREEN, self.camera.apply_rect(wall.rect), 2)
                #pg.draw.circle(self.screen, GREEN, self.camera.apply(wall).center, 1, 1)

            for mob in self.mobs:
                pg.draw.rect(self.screen, RED, self.camera.apply_rect(mob.hit_rect), 2)
                pg.draw.circle(self.screen, BLUE, self.camera.apply(mob).center, DETECT_RADIUS, 2)

                if mob.target_dist.length_squared() < DETECT_RADIUS ** 2:
                    pg.draw.circle(self.screen, LIGHTBLUE, self.camera.apply(mob).center,
                                   int(mob.target_dist.length()), 1)
                    pg.draw.line(self.screen, GREEN, self.camera.apply(mob).center,
                                 self.camera.apply(mob.target).center)

            for pair in self.wall_pairs:
                pg.draw.line(self.screen, GREEN, pair[0], pair[1])


        draw_player_health(self.screen, 10, 10, self.player.health / PLAYER_HEALTH)
        # AFTER drawing
        pg.display.flip()

    def show_start_scr(self):
        # game start screen
        self.screen.fill(BGCOLOR)
        self.draw_text(TITLE, 48, WHITE, WIDTH / 2, HEIGHT / 4)
        self.draw_text("Arrows to move, Spacebar to jump", 22, WHITE, WIDTH / 2, HEIGHT / 2)
        self.draw_text("Press any key to begin", 22, WHITE, WIDTH / 2, HEIGHT * 3 / 4)
        pg.display.flip()
        self.wait_for_key()

    def show_go_scr(self):
        # game over screen
        if not self.running:
            return
            # self.screen.fill(BGCOLOR)
            # self.draw_text("Game Over", 48, WHITE, WIDTH / 2, HEIGHT / 4)
            # self.draw_text("Press any key to play again", 22, WHITE, WIDTH / 2, HEIGHT * 3 / 4)
            # pg.display.flip()
            # self.wait_for_key()

    def wait_for_key(self):
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    waiting = False
                    self.running = False
                if event.type == pg.KEYUP:
                    waiting = False

    def draw_text(self, text, size, color, x, y):
        font = pg.font.Font(self.font_name, size)
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        self.screen.blit(text_surface, text_rect)


g = Game()
# g.show_start_scr()
while g.running:
    g.new()
    g.show_go_scr()

pg.quit()
