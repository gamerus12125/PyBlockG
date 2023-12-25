import pygame
import os
import time

all_sprites = pygame.sprite.Group()
WIDTH = 1000
HEIGHT = 1000


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname).convert()
    except pygame.error as message:
        print('Cannot load image:', name)
        raise SystemExit(message)

    if color_key is not None:
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


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


class Wall(pygame.sprite.Sprite):
    def __init__(self, w, h, x, y):
        super().__init__(all_sprites)
        self.height = h
        self.width = w
        self.x = x
        self.y = y
        self.is_player_collide = True
        self.rect = pygame.Rect(x, y, w, h)

    def update(self):
        pygame.draw.rect(screen, (255, 255, 255), (self.x, self.y, self.width, self.height))


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__(all_sprites)
        self.rect = pygame.Rect(x, y, 20, 10)
        self.is_player_collide = False
        self.vx = -4 if direction == "L" else 4

    def update(self):
        colliders = pygame.sprite.spritecollide(self, all_sprites, False)
        if colliders and Wall.__name__ in colliders.__str__():
            del self
        else:
            pygame.draw.rect(screen, pygame.color.Color("red"), self.rect)
            self.rect = self.rect.move(self.vx, 0)
            if self.rect.x > WIDTH:
                del self


class Player(pygame.sprite.Sprite):
    def __init__(self, w, h, x, y, animation):
        super().__init__(all_sprites)
        self.hp = 100
        self.rect = pygame.rect.Rect(x, y, w, h)

        self.is_down = False
        self.is_walk_r = False
        self.is_walk_l = False
        self.is_idle = True
        self.is_attack = False
        self.g = 0.2
        self.fall_speed = 0

        self.ammo = 10
        self.is_reload = False
        self.direction = "R"
        self.shoot_clock = Timer()
        self.shoot_clock.start()
        self.animations = animation

        self.images = {"idle_r": [], "idle_l": [], "run_r": [], "run_l": [], "attack_r": [], "attack_l": []}

        self.init_images(animation)

        self.index = 0
        self.image = self.images["idle_r"][self.index]
        self.animation_time = 0.15

        self.anim_cur_time = Timer()
        self.anim_cur_time.start()

    def init_images(self, animation):
        for i in range(0, 128, 32):
            self.images["idle_r"].append(
                pygame.transform.scale_by(animation["idle"].subsurface(pygame.Rect(i, 0, 32, 32)), 3))
            self.images["idle_l"].append(
                pygame.transform.flip(
                    pygame.transform.scale_by(animation["idle"].subsurface(pygame.Rect(i, 0, 32, 32)), 3), True, False))

        for i in range(0, 181, 32):
            self.images["run_r"].append(
                pygame.transform.scale_by(animation["run"].subsurface(pygame.Rect(i, 0, 32, 32)), 3))
            self.images["run_l"].append(
                pygame.transform.flip(pygame.transform.scale_by(animation["run"].subsurface(pygame.Rect(i, 0, 32, 32)),
                                                                3), True, False))
        for i in range(0, 97, 32):
            self.images["attack_r"].append(
                pygame.transform.scale_by(animation["attack"].subsurface(pygame.Rect(i, 0, 32, 32)), 3))
            self.images["attack_l"].append(
                pygame.transform.flip(
                    pygame.transform.scale_by(animation["attack"].subsurface(pygame.Rect(i, 0, 32, 32)), 3), True,
                    False))

    def update(self):
        self.fall_speed += self.g
        self.rect = self.rect.move(0, self.fall_speed)
        colliders = pygame.sprite.spritecollide(self, all_sprites, False)
        colliders.remove(self)
        if colliders and Wall.__name__ in colliders.__str__():
            self.rect = self.rect.move(0, -self.fall_speed)
            self.fall_speed = 0
            self.is_down = False
        else:
            self.is_down = True

        if self.is_reload:
            if self.shoot_clock.get_time() > 1:
                self.is_reload = False
                self.ammo = 10

        self.move()

    def animation(self, name):
        anim = name
        if self.anim_cur_time.get_time() > self.animation_time:
            self.anim_cur_time.stop()
            self.anim_cur_time.start()
            self.index += 1

            if self.index >= len(self.images[anim]):
                if self.is_attack:
                    self.is_attack = False
                self.index = 0
            self.image = self.images[anim][self.index]
        if self.is_attack:
            anim = "attack_r"
        screen.blit(self.images[anim][self.index], (self.rect.x - 16, self.rect.y - 32))
        pygame.draw.rect(screen, (255, 0, 0), self.rect, 1)

    def jump(self):
        if not self.is_down:
            self.fall_speed = -10

    def move(self):
        if keys[pygame.K_SPACE]:
            self.jump()
        if keys[pygame.K_d]:
            self.rect = self.rect.move(2, 0)
            self.direction = "R"
            is_collide = pygame.sprite.spritecollideany(self, all_sprites)
            if is_collide and is_collide != self:
                self.rect = self.rect.move(-2, 0)
                if self.is_walk_l or self.is_walk_r:
                    self.index = 0
                self.animation("idle_r")
                self.is_walk_r = False
                self.is_walk_l = False
                return False
            else:
                self.is_walk_l = False
                self.is_walk_r = True
                if self.is_idle:
                    self.index = 0
                self.animation("run_r")
                self.is_idle = False
                return True
        elif keys[pygame.K_a]:
            self.rect = self.rect.move(-2, 0)
            self.direction = "L"
            is_collide = pygame.sprite.spritecollideany(self, all_sprites)
            if is_collide and is_collide != self:
                self.rect = self.rect.move(2, 0)
                if self.is_walk_l or self.is_walk_r:
                    self.index = 0
                self.animation("idle_l")
                self.is_walk_r = False
                self.is_walk_l = False
                return False
            else:
                self.is_walk_l = True
                self.is_walk_r = False
                if self.is_idle:
                    self.index = 0
                self.animation("run_l")
                self.is_idle = False
                return True
        else:
            if self.is_walk_l or self.is_walk_r:
                self.index = 0
            if self.direction == "R":
                self.animation("idle_r")
            else:
                self.animation("idle_l")
            self.is_walk_r = False
            self.is_walk_l = False

    def shoot(self):
        if self.shoot_clock.get_time() > 0.5 and not self.is_reload:
            self.is_attack = True
            self.index = -1
            if not self.ammo:
                self.is_reload = True
                self.shoot_clock.stop()
                self.shoot_clock.start()
            else:
                if self.direction == "L":
                    Bullet(self.rect.x - 1, int(self.rect.y + 5), self.direction)
                else:
                    Bullet(self.rect.x + self.rect.w + 1, int(self.rect.y + 5), self.direction)
                self.ammo -= 1
                self.shoot_clock.stop()
                self.shoot_clock.start()


if __name__ == '__main__':
    pygame.init()
    pygame.display.set_caption('Доска')
    size = width, height = WIDTH, HEIGHT
    fps = 60
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode(size)

    player_animations = {"idle": load_image("Pink_Monster_Idle_4.png", -1),
                         "run": load_image("Pink_Monster_Run_6.png", -1),
                         "attack": load_image("Pink_Monster_Attack1_4.png", -1)}

    floor = Wall(width, 30, 0, height - 30)
    block = Wall(300, 30, 200, 800)
    player = Player(64, 64, 0, 300, player_animations)

    interface = Interface(player)

    running = True

    while running:
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                player.shoot()

        screen.fill((100, 0, 0))

        all_sprites.update()

        interface.render()

        pygame.display.flip()
        clock.tick(fps)
