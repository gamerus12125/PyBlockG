import pygame
import os
import time
import random
import sys
import pytmx

WIDTH = 1000
HEIGHT = 800
GRAVITY = 0.2

all_sprites = pygame.sprite.Group()
all_blocks = pygame.sprite.Group()
all_entities = pygame.sprite.Group()
screen_rect = (0, 0, WIDTH, HEIGHT)


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        raise SystemExit(message)

    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


def terminate():
    pygame.quit()
    sys.exit()


def create_particles(position, image_name):
    particle_count = 20
    numbers = range(-5, 6)
    for _ in range(particle_count):
        Particle(position, random.choice(numbers), random.choice(numbers), image_name)


def load_level(filename):
    filename = "data/" + filename
    level_map = pytmx.util_pygame.load_pygame(filename)
    return level_map


def generate_level(game_map):
    for y in range(game_map.height):
        for x in range(game_map.width):
            tile_id = game_map.get_tile_gid(x, y, 0)
            if tile_id:
                image = game_map.get_tile_image_by_gid(tile_id)
                if game_map.tiledgidmap[tile_id] not in [0, 1, 2, 3, 4, 5,
                                                         130]:  # проверка, что тайлы не являются проходимыми блоками
                    Tile(x * 32, y * 32, pygame.transform.scale_by(image, 2), all_sprites, all_blocks)
                else:
                    Tile(x * 32, y * 32, pygame.transform.scale_by(image, 2), all_sprites)


class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, dx, dy, image_name):
        super().__init__(all_sprites)
        self.image = [load_image(image_name)]
        for scale in (5, 10, 20):
            self.image.append(pygame.transform.scale(self.image[0], (scale, scale)))
        self.image = random.choice(self.image)
        self.rect = self.image.get_rect()
        self.velocity = [dx, dy]
        self.rect.x, self.rect.y = pos
        self.gravity = GRAVITY

    def update(self):
        self.velocity[1] += self.gravity
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        if not self.rect.colliderect(screen_rect):
            self.kill()
        screen.blit(self.image, self.rect)


class Interface:
    def __init__(self, player):
        self.x = 10
        self.y = 10
        self.width = 100
        self.height = 50
        self.font = pygame.font.Font(None, 48)
        self.red = (255, 0, 0)
        self.grenn = (0, 255, 0)
        self.player = player

    def render(self):
        ammo = self.font.render(str(self.player.ammo), True, self.red)
        health = self.font.render(str(self.player.hp), True, self.grenn)
        screen.blit(ammo, (self.x, self.y))
        screen.blit(health, (self.x + self.width, self.y))
        pygame.draw.rect(screen, self.grenn, (self.x + self.width - 10, self.y - 10, self.width, self.height), 5)
        pygame.draw.rect(screen, self.red, (self.x - 10, self.y - 10, 100, 50), 5)


class Timer:
    def __init__(self):
        self.start_time = None

    def start(self):
        self.start_time = time.perf_counter()

    def stop(self):
        self.start_time = None

    def get_time(self):
        return time.perf_counter() - self.start_time


class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, img, *args):
        super().__init__(*args)
        self.height = 32
        self.width = 32
        self.x = x
        self.y = y
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        screen.blit(self.image, pygame.Rect(self.x, self.y, self.width, self.height))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__(all_sprites, all_entities)
        self.is_player_collide = False
        self.direction = direction
        self.vx = -4 if direction == "L" else 4
        self.frames = []
        self.cut_sheet(load_image("All_Fire_Bullet_Pixel_16x16_00.png"), 4)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = pygame.Rect(x, y, 64, 32)
        self.animation_timer = Timer()
        self.animation_timer.start()
        self.animation_time = 0.1

    def cut_sheet(self, sheet, columns):
        x = sheet.get_width() // columns
        y = 0
        if self.direction == "L":
            for i in range(columns):
                self.frames.append(
                    pygame.transform.flip(
                        pygame.transform.scale_by(sheet.subsurface(pygame.Rect(i * x, y, 32, 16)), 2), True,
                        False))
        else:
            for i in range(columns):
                self.frames.append(
                    pygame.transform.scale_by(sheet.subsurface(pygame.Rect(i * x, y, 32, 16)), 2))

    def update(self):
        colliders = pygame.sprite.spritecollide(self, all_blocks, False)
        if colliders and Tile.__name__ in colliders.__str__():
            create_particles((self.rect.x, self.rect.y), "star.png")
            self.kill()
        elif self.animation_timer.get_time() >= self.animation_time:
            self.cur_frame = 0 if self.cur_frame + 1 == len(self.frames) else self.cur_frame + 1
            self.image = self.frames[self.cur_frame]
            self.animation_timer.stop()
            self.animation_timer.start()
        if self:
            screen.blit(self.image, self.rect)
            pygame.draw.rect(screen, (255, 0, 0), self.rect, 1)
            self.rect = self.rect.move(self.vx, 0)
            if self.rect.x > WIDTH:
                self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__(all_sprites, all_entities)
        self.hp = 100
        self.rect = pygame.rect.Rect(x, y, w, h)

        self.is_down = False
        self.is_walk = False
        self.is_idle = True
        self.is_attack = False
        self.fall_speed = 0
        self.dx = 0
        self.dy = 0
        self.walk_speed = 3

        self.ammo = 10
        self.is_reload = False
        self.direction = "R"
        self.shoot_clock = Timer()
        self.shoot_clock.start()
        sprites = {"idle": load_image("Pink_Monster_Idle_4.png"), "run": load_image("Pink_Monster_Run_6.png"),
                   "attack": load_image("Pink_Monster_Attack1_4.png")}

        self.images = {"idle": [], "run": [], "attack": []}
        self.images_size = {"idle": 128, "run": 192, "attack": 128}

        self.init_images(sprites)

        self.index = 0
        self.image = self.images["idle"][0]
        self.animation_time = 0.1

        self.anim_time = Timer()
        self.anim_time.start()

        self.mask = pygame.mask.from_surface(self.image)

    def init_images(self, animation):
        for key in self.images.keys():
            for i in range(0, self.images_size[key], 32):
                self.images[key].append(
                    pygame.transform.scale_by(animation[key].subsurface(pygame.Rect(i, 0, 32, 32)), 3))

    def update(self):
        if self.is_reload:
            if self.shoot_clock.get_time() > 1:
                self.is_reload = False
                self.ammo = 10
        self.move()
        self.draw()

    def draw(self):
        if self.is_attack:
            if self.direction == "L":
                self.animation("attack", True)
            else:
                self.animation("attack", False)
        elif self.is_walk:
            if self.direction == "L":
                self.animation("run", True)
            else:
                self.animation("run", False)
        else:
            if self.direction == "L":
                self.animation("idle", True)
            else:
                self.animation("idle", False)

    def animation(self, name, flip):
        if self.anim_time.get_time() > self.animation_time:
            self.anim_time.stop()
            self.anim_time.start()
            self.index += 1
            if self.index >= len(self.images[name]):
                if name == "attack":
                    Bullet(self.rect.x - 1, int(self.rect.y + 5), self.direction)
                    self.is_attack = False
                self.index = 0
        if self.index >= len(self.images[name]):
            self.index = 0
        self.image = self.images[name][self.index]
        screen.blit(pygame.transform.flip(self.images[name][self.index], flip, False),
                    (self.rect.x - 16, self.rect.y - 32))
        pygame.draw.rect(screen, (255, 0, 0), self.rect, 1)

    def fall(self):
        self.fall_speed += GRAVITY
        self.dy = round(self.fall_speed)
        self.rect.y += self.dy
        self.is_down = True

    def move(self):
        self.fall()
        colliders = pygame.sprite.spritecollide(self, all_blocks, False)
        if colliders:
            self.rect.y -= self.dy
            if self.dy > 0:
                self.is_down = False
                self.fall_speed = 0
            elif self.dy < 0:
                self.fall_speed = 0
        if not self.is_attack:
            if keys[pygame.K_SPACE] and not self.is_down:
                self.fall_speed = -10
            if keys[pygame.K_d]:
                self.dx = self.walk_speed
                self.rect.x += self.dx
                self.is_walk = True
                self.direction = "R"
            elif keys[pygame.K_a]:
                self.dx = -self.walk_speed
                self.rect.x += self.dx
                self.is_walk = True
                self.direction = "L"
            else:
                if self.is_walk:
                    self.index = 0
                    self.is_walk = False
        colliders = pygame.sprite.spritecollide(self, all_blocks, False)
        if colliders:
            self.is_walk = False
            self.rect.x -= self.dx
        self.dx = 0
        self.dy = 0

    def shoot(self):
        if self.shoot_clock.get_time() > 0.5 and not self.is_reload:
            self.is_attack = True
            self.index = -1
            if not self.ammo:
                self.is_reload = True
                self.shoot_clock.stop()
                self.shoot_clock.start()
            else:
                self.ammo -= 1
                self.shoot_clock.stop()
                self.shoot_clock.start()


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Доска')
        self.size = WIDTH, HEIGHT
        self.fps = 60
        self.clock = pygame.time.Clock()
        global screen
        screen = pygame.display.set_mode(self.size)

        self.player = Player(0, 300, 60, 64)

        self.interface = Interface(self.player)

        self.running = True
        self.start_screen()
        self.start_game()

    def start_screen(self):
        intro_text = ["PyGame", "",
                      "Правила игры"]
        fon = pygame.transform.scale(load_image('fon.png'), (WIDTH, HEIGHT))
        screen.blit(fon, (0, 0))
        font = pygame.font.Font(None, 30)
        text_coord = 50
        for line in intro_text:
            string_rendered = font.render(line, 1, pygame.Color('black'))
            intro_rect = string_rendered.get_rect()
            text_coord += 10
            intro_rect.top = text_coord
            intro_rect.x = 10
            text_coord += intro_rect.height
            screen.blit(string_rendered, intro_rect)

        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate()
                elif event.type == pygame.KEYDOWN or \
                        event.type == pygame.MOUSEBUTTONDOWN:
                    return

    def start_game(self):
        level = load_level("map.tmx")
        generate_level(level)
        while self.running:
            global keys
            keys = pygame.key.get_pressed()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.player.shoot()

            screen.fill((100, 0, 0))
            all_sprites.update()

            self.interface.render()

            pygame.display.flip()
            self.clock.tick(self.fps)


if __name__ == '__main__':
    pygame.init()
    game = Game()
