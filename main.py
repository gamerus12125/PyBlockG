import json

import pygame
import os
import time
import random
import sys
import pytmx

WIDTH = 960
HEIGHT = 640
GRAVITY = 0.3

all_sprites = pygame.sprite.Group()
all_blocks = pygame.sprite.Group()
all_entities = pygame.sprite.Group()
all_items = pygame.sprite.Group()
player_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
portal_group = pygame.sprite.Group()
functional_rects = []
functional_list = []
screen_rect = (0, 0, WIDTH, HEIGHT)
level = 1
level_name = "map"
levels = ("map.tmx", "map1.tmx")
enemies = {"map": [(300, 300), (100, 200)], "map1": [(400, 200), (200, 300)], "trade_zone": []}
player_hp = 100
player_ammo = 10
player_damage = 25
is_level_generating = False
is_player_death = False


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


def clear_sprites():
    for sprite in all_sprites:
        if "Player" not in sprite.__str__():
            sprite.kill()
    global functional_rects
    global functional_list
    functional_rects = []
    functional_list = []


def create_particles(position, image_name):
    particle_count = 20
    numbers = range(-5, 6)
    for _ in range(particle_count):
        Particle(position, random.choice(numbers), random.choice(numbers), image_name)


def cut_sheet(sheet, columns, rows, mult=2, flip=False):
    old_frames = []
    x = sheet.get_width() // columns
    y = sheet.get_height() // rows
    for a in range(rows):
        for i in range(columns):
            old_frames.append(
                pygame.transform.flip(
                    pygame.transform.scale_by(sheet.subsurface(pygame.Rect(i * x, y * a, x, y)), mult), flip, False))
    return old_frames


def spawn_coins(x, y, amount):
    coins = [random.randint(1, 10) for _ in range(amount)]
    for i in coins:
        dx = random.randint(-40, 40)
        Coin(x + dx, y, i)


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
                tile_gid = game_map.tiledgidmap[tile_id]
                if tile_gid == 626:
                    Chest(x * 32, y * 32, 64, 64, load_image("Chests.png"), 5, 2)
                elif tile_gid in [627, 641, 642, 720, 751, 752, 783, 784, 724, 755, 756, 787, 788]:
                    pass
                elif tile_gid in [0, 1, 2, 3, 4, 5,
                                  130]:  # проверка, что тайлы являются проходимыми блоками
                    Tile(x * 32, y * 32, pygame.transform.scale_by(image, 2), all_sprites)
                elif tile_gid == 541:
                    Coin(x * 32, y * 32, 1)
                elif tile_gid == 719:
                    Portal(x * 32, y * 32, 64, 96, load_image("Green Portal Sprite Sheet.png"), 8, 1,
                           portal_group)
                elif tile_gid == 723:
                    AnimatedObject(x * 32, y * 32, 64, 96, load_image("Green Portal Sprite Sheet.png"), 8, 1,
                                   portal_group)
                    for i in player_group:
                        i.rect.x = x * 32 + 64
                        i.rect.y = y * 32
                        i.functional_rect.x = x * 32 + 32
                        i.functional_rect.y = y * 32 - 32
                else:
                    Tile(x * 32, y * 32, pygame.transform.scale_by(image, 2), all_sprites, all_blocks)
    if level_name == "trade_zone":
        Shop(12 * 32, 15 * 32, pygame.transform.scale_by(load_image("Heart.png"), 2), 20, "hp")
        Shop(15 * 32, 15 * 32, pygame.transform.scale_by(load_image("Sword.png"), 2), 20, "damage")
    for coords in enemies[level_name]:
        Enemy(coords[0], coords[1], 64, 64)


def next_level():
    global is_level_generating
    if not is_level_generating:
        is_level_generating = True
        clear_sprites()
        global level
        global level_name
        level += 1
        if level % 3 == 0:
            lvl_name = "trade_zone.tmx"
            lvl = load_level(lvl_name)
        else:
            lvl_name = random.choice(levels)
            lvl = load_level(lvl_name)
        level_name = lvl_name.split(".")[0]
        generate_level(lvl)
        is_level_generating = False


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


class Effect(pygame.sprite.Sprite):
    def __init__(self, x, y, img):
        super().__init__(all_sprites)
        self.x = x
        self.y = y
        self.image = img
        self.rect = img.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.duration = 2
        self.clock = Timer()
        self.clock.start()

    def update(self):
        if self.clock.get_time() >= self.duration:
            self.kill()
        else:
            screen.blit(self.image, self.rect)


class AnimatedEffect(Effect):
    def __init__(self, x, y, sheet):
        self.frames = cut_sheet(sheet, 6, 1)
        self.index = 0
        self.image = self.frames[self.index]
        self.animation_time = 0.1
        self.animation_clock = Timer()
        self.animation_clock.start()
        super().__init__(x, y, self.image)

    def update(self):
        if self.animation_clock.get_time() > self.animation_time:
            self.animation_clock.stop()
            self.animation_clock.start()
            self.index += 1
            if self.index >= len(self.frames):
                self.kill()
        else:
            screen.blit(self.frames[self.index], self.rect)


class Interface:
    def __init__(self, player):
        self.x = 10
        self.y = 10
        self.width = 100
        self.height = 50
        self.font = pygame.font.Font(None, 48)
        self.red = (255, 0, 0)
        self.green = (0, 255, 0)
        self.blue = (0, 0, 255)
        self.black = (0, 0, 0)
        self.player = player

        self.gem_frames = cut_sheet(load_image("GEM UI Spritesheet.png"), 16, 1, 1)
        self.index = 0
        self.animation_time = 0.05
        self.animation_clock = Timer()
        self.animation_clock.start()

    def render(self):
        ammo = self.font.render(str(self.player.ammo), True, self.red)
        health = self.font.render(str(self.player.hp), True, self.green)
        points = self.font.render(str(self.player.points), True, self.blue)
        lvl = self.font.render(f"Уровень: {level}", True, self.black)
        screen.blit(ammo, (self.x, self.y))
        screen.blit(health, (self.x + self.width, self.y))
        screen.blit(points, (self.x + self.width * 2, self.y))
        screen.blit(lvl, (WIDTH // 2, self.y))
        pygame.draw.rect(screen, self.green, (self.x + self.width - 10, self.y - 10, self.width, self.height), 5)
        pygame.draw.rect(screen, self.red, (self.x - 10, self.y - 10, 100, 50), 5)
        pygame.draw.rect(screen, self.blue, (self.x + self.width * 2 - 10, self.y - 10, self.width, self.height), 5)

        if self.animation_clock.get_time() >= self.animation_time:
            self.index += 1
            if self.index >= len(self.gem_frames):
                self.index = 0
            self.animation_clock.stop()
            self.animation_clock.start()
        screen.blit(self.gem_frames[self.index],
                    (self.x + self.width * 2 + self.gem_frames[self.index].get_width() * len(str(self.player.points)),
                     self.y))


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
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        screen.blit(self.image, self.rect)


class Shop(pygame.sprite.Sprite):
    def __init__(self, x, y, img, cost, param):
        super().__init__(all_sprites)
        self.rect = img.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.cost = cost
        self.image = img
        self.arrow = pygame.transform.scale_by(load_image("green_arrow_up.png"), 2)
        self.param = param
        self.font = pygame.font.Font(None, 48)
        self.gem = load_image("GEM.png")
        functional_rects.append(self.rect)
        functional_list.append(self)

    def update(self):
        cost = self.font.render(str(self.cost), True, (255, 0, 0))
        screen.blit(self.image, self.rect)
        screen.blit(self.arrow, self.rect)
        screen.blit(cost, (self.rect.x, self.rect.y - 32))
        screen.blit(self.gem, (self.rect.x + 48, self.rect.y - 32))


class AnimatedObject(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h, img_sprites, cols, rows, *args):
        super().__init__(all_sprites, *args)
        self.x = x
        self.y = y
        self.rect = pygame.rect.Rect(x, y, w, h)
        self.frames = cut_sheet(img_sprites, cols, rows, mult=2)
        self.index = 0
        self.image = self.frames[0]
        self.animation_time = 0.15
        self.animation_clock = Timer()
        self.animation_clock.start()

    def update(self):
        if self.animation_clock.get_time() >= self.animation_time:
            self.animation_clock.stop()
            self.animation_clock.start()
            self.index += 1
            if self.index >= len(self.frames):
                self.index = 0
        screen.blit(self.frames[self.index], self.rect)
        pygame.draw.rect(screen, (255, 0, 0), self.rect, 1)


class Portal(AnimatedObject):
    def update(self):
        if self.animation_clock.get_time() >= self.animation_time:
            self.animation_clock.stop()
            self.animation_clock.start()
            self.index += 1
            if self.index >= len(self.frames):
                self.index = 0
        screen.blit(self.frames[self.index], self.rect)
        pygame.draw.rect(screen, (255, 0, 0), self.rect, 1)
        colliders = pygame.sprite.spritecollideany(self, player_group)
        if colliders:
            next_level()


class FunctionalAnimatedObject(AnimatedObject):
    def __init__(self, x, y, w, h, img_sprites, cols, rows):
        super().__init__(x, y, w, h, img_sprites, cols, rows)
        functional_rects.append(self.rect)
        self.is_used = False
        self.is_using = False
        functional_list.append(self)

    def update(self):
        if not self.is_used and self.is_using:
            if self.animation_clock.get_time() >= self.animation_time:
                self.animation_clock.stop()
                self.animation_clock.start()
                self.index += 1
                if self.index >= len(self.frames):
                    self.index = -1
                    self.is_used = True
                    all_blocks.remove(self)
                    self.action()
        screen.blit(self.frames[self.index], self.rect)
        pygame.draw.rect(screen, (255, 0, 0), self.rect, 1)

    def use(self):
        self.animation_clock.start()
        self.is_using = True

    def action(self):
        pass


class Chest(FunctionalAnimatedObject):
    def action(self):
        spawn_coins(self.x, self.y - 30, 5)


class Item(pygame.sprite.Sprite):
    def __init__(self, x, y, img):
        super().__init__(all_sprites, all_items)
        self.x = x
        self.y = y
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        screen.blit(self.image, self.rect)


class Coin(Item):
    def __init__(self, x, y, points):
        self.image = pygame.transform.scale_by(load_image("coin.png"), 2)
        self.points = points
        super().__init__(x, y, self.image)

    def update(self):
        collider = pygame.sprite.spritecollideany(self, player_group)
        if collider:
            collider.points += self.points
            self.kill()
        screen.blit(self.image, self.rect)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__(all_sprites, all_entities)
        self.is_player_collide = False
        self.direction = direction
        self.damage_value = player_damage
        self.vx = -5 if direction == "L" else 5
        self.frames = cut_sheet(load_image("All_Fire_Bullet_Pixel_16x16_00.png"), 4, 1,
                                flip=True if direction == "L" else False)
        self.cur_frame = 0
        self.image = self.frames[self.cur_frame]
        self.rect = pygame.Rect(x, y, 64, 32)
        self.animation_timer = Timer()
        self.animation_timer.start()
        self.animation_time = 0.1

    def update(self):
        colliders = pygame.sprite.spritecollideany(self, all_blocks)
        if colliders:
            AnimatedEffect(self.rect.x, self.rect.y - 10, load_image("boom_effect.png"))
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

    def damage(self, enemy):
        enemy.hp -= self.damage_value
        AnimatedEffect(self.rect.x, self.rect.y - 10, load_image("boom_effect.png"))
        self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__(all_sprites, player_group)
        self.hp = player_hp
        self.points = 0
        self.count = 0

        self.is_down = False
        self.is_walk = False
        self.is_idle = True
        self.is_attack = False
        self.is_damage_resist = False
        self.fall_speed = 0
        self.dx = 0
        self.dy = 0
        self.walk_speed = 3
        self.damage_resist_clock = Timer()
        self.damge_indicator_clock = Timer()
        self.is_using = False
        self.use_clock = Timer()

        self.ammo = player_ammo
        self.is_reload = False
        self.direction = "R"
        self.reload_clock = Timer()
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

        self.rect = pygame.rect.Rect(x, y, w, h)
        self.functional_rect = pygame.rect.Rect(x - w // 2, y - h // 2, w * 2, h * 2)

        self.jumps = 0

    def init_images(self, animation):
        for key in self.images.keys():
            for i in range(0, self.images_size[key], 32):
                self.images[key].append(
                    pygame.transform.scale_by(animation[key].subsurface(pygame.Rect(i, 0, 32, 32)), 3))

    def update(self):
        if self.is_reload:
            if self.reload_clock.get_time() > 2:
                self.is_reload = False
                self.ammo = 10
                self.reload_clock.stop()
        if self.is_using:
            if self.use_clock.get_time() > 0.2:
                self.is_using = False
                self.use_clock.stop()
        if self.is_damage_resist:
            if self.damge_indicator_clock.get_time() > 0.3:
                self.draw()
                self.damge_indicator_clock.stop()
                self.damge_indicator_clock.start()
            if self.damage_resist_clock.get_time() > 3:
                self.is_damage_resist = False
                self.damge_indicator_clock.stop()
        else:
            self.draw()
        self.move()
        pygame.draw.rect(screen, (0, 255, 0), self.functional_rect, 1)

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
                Bullet(self.rect.x + self.rect.w, int(self.rect.y + 5), self.direction)
                self.is_attack = False
            self.index = 0
        self.image = self.images[name][self.index]
        screen.blit(pygame.transform.flip(self.images[name][self.index], flip, False),
                    (self.rect.x - 16, self.rect.y - 32))
        pygame.draw.rect(screen, (255, 0, 0), self.rect, 1)

    def fall(self):
        self.fall_speed += GRAVITY
        self.dy = round(self.fall_speed)
        self.rect.y += self.dy
        self.functional_rect.y += self.dy
        self.is_down = True

    def move(self):
        self.fall()
        colliders = pygame.sprite.spritecollide(self, all_blocks, False)
        if colliders:
            self.rect.y -= self.dy
            self.functional_rect.y -= self.dy
            if self.dy > 0:
                self.is_down = False
                self.jumps = 0
                self.fall_speed = 0
            elif self.dy < 0:
                self.fall_speed = 0
        if not self.is_attack:
            if keys[pygame.K_SPACE] and self.jumps < 1:
                self.jumps += 1
                self.fall_speed = -8
            if keys[pygame.K_d]:
                self.dx = self.walk_speed
                self.rect.x += self.dx
                self.functional_rect.x += self.dx
                self.is_walk = True
                self.direction = "R"
            elif keys[pygame.K_a]:
                self.dx = -self.walk_speed
                self.rect.x += self.dx
                self.functional_rect.x += self.dx
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
            self.functional_rect.x -= self.dx
        self.dx = 0
        self.dy = 0
        index = self.functional_rect.collidelist(functional_rects)
        if index != -1:
            if keys[pygame.K_e] and not self.is_using:
                item = functional_list[index]
                self.is_using = True
                self.use_clock.start()
                if item.__class__ == Shop and self.points >= item.cost:
                    if item.param == "hp":
                        self.hp += 10
                    else:
                        global player_damage
                        player_damage += 5
                    self.points -= 20
                elif item.__class__ == Chest:
                    functional_list[index].use()
        colliders = pygame.sprite.spritecollideany(self, enemy_group)
        if colliders and not self.is_damage_resist:
            self.hp -= int(25 * (level * 0.2 + 1))
            if self.hp <= 0:
                global is_player_death
                is_player_death = True
            self.is_damage_resist = True
            self.damage_resist_clock.start()
            self.damge_indicator_clock.start()

    def shoot(self):
        if self.shoot_clock.get_time() > 0.5 and not self.is_reload:
            self.is_attack = True
            self.index = 0
            if not self.ammo:
                self.is_reload = True
                self.reload_clock.start()
                self.shoot_clock.stop()
                self.shoot_clock.start()
            else:
                self.ammo -= 1
                self.shoot_clock.stop()
                self.shoot_clock.start()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, w, h):
        super().__init__(all_sprites, enemy_group)
        self.image = pygame.transform.scale_by(pygame.image.load("data/eyelander.png"), 2)
        self.rect = pygame.rect.Rect(x, y, w, h)
        self.hp = 50 * (int(level * 0.5) + 1)
        self.mx_hp = 50 * (int(level * 0.5) + 1)
        self.mx_dx = 200
        self.dx = 0
        self.vx = 1
        self.direction = "L"

    def update(self):
        screen.blit(self.image, self.rect)
        pygame.draw.rect(screen, (255, 0, 0), (self.rect.x, self.rect.y - 20, self.rect.w * (self.hp / self.mx_hp), 10))
        pygame.draw.rect(screen, (0, 0, 0), (self.rect.x - 2, self.rect.y - 22, self.rect.w + 4, 14), 2)
        pygame.draw.rect(screen, (255, 0, 0), self.rect, 1)
        self.move()
        damage = pygame.sprite.spritecollideany(self, all_entities)
        if damage:
            damage.damage(self)
            if self.hp <= 0:
                spawn_coins(self.rect.x + self.rect.w // 2, self.rect.y + self.rect.h, 2)
                self.kill()

    def move(self):
        if self.direction == "L":
            self.dx -= self.vx
            self.rect.x -= self.vx
        elif self.direction == "R":
            self.dx += self.vx
            self.rect.x += self.vx
        if self.dx >= self.mx_dx or self.dx < 0:
            self.direction = "R" if self.direction == "L" else "L"


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption('Доска')
        self.size = WIDTH, HEIGHT
        self.fps = 60
        self.clock = pygame.time.Clock()
        with open("data/records.json", "r") as record_file:
            level = json.load(record_file)["max_level"]
        self.max_level = level
        global screen
        screen = pygame.display.set_mode(self.size)

        self.running = True
        self.start_screen()
        self.start_game()
        while True:
            self.end_screen()

    def start_screen(self):
        intro_text = ["PyGame", "",
                      "Правила игры", "", "",
                      f"Лучший результат: {self.max_level}"]
        fon = pygame.transform.scale(load_image('fon.png'), (WIDTH, HEIGHT))
        screen.blit(fon, (0, 0))
        font = pygame.font.Font(None, 30)
        text_coord = 50
        for line in intro_text:
            string_rendered = font.render(line, 1, pygame.Color('black'))
            intro_rect = string_rendered.get_rect()
            text_coord += 10
            intro_rect.top = text_coord
            intro_rect.x = WIDTH // 3
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
        self.player = Player(0, 300, 60, 64)
        interface = Interface(self.player)
        lvl = load_level("map.tmx")
        generate_level(lvl)
        while self.running:
            global keys
            keys = pygame.key.get_pressed()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.player.shoot()

            if is_player_death:
                return

            screen.fill((58, 204, 250))
            all_sprites.update()
            interface.render()
            pygame.display.flip()
            self.clock.tick(self.fps)

    def end_screen(self):
        global is_player_death
        global level
        clear_sprites()
        self.player.kill()

        end_text = ["ВЫ ПРОИГРАЛИ", "",
                    f"Ваш результат:", "",
                    f"Уровень: {level}",
                    f"Лучший результат: {self.max_level}", "",
                    f"Нажмите, чтобы начать начать с начала."]
        fon = pygame.transform.scale(load_image('fon.png'), (WIDTH, HEIGHT))
        screen.blit(fon, (0, 0))
        font = pygame.font.Font(None, 30)
        text_coord = 50
        for line in end_text:
            string_rendered = font.render(line, 1, pygame.Color('black'))
            intro_rect = string_rendered.get_rect()
            text_coord += 10
            intro_rect.top = text_coord
            intro_rect.x = WIDTH // 3
            text_coord += intro_rect.height
            screen.blit(string_rendered, intro_rect)
        pygame.display.flip()
        is_player_death = False
        level = 1
        run = True
        while run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    terminate()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    run = False
                    break
        self.start_game()


if __name__ == '__main__':
    pygame.init()
    game = Game()
