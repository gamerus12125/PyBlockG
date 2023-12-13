import pygame

import time

objects = []
WIDTH = 1000
HEIGHT = 1000


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

    def render(self, screen):
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


def check_intersect(obj1):
    for itm in objects:
        if type(obj1).__name__ == "Player":
            if itm.is_player_collide:
                if set(obj1.get_coords()[0]).intersection(itm.get_coords()[0]) and set(
                        obj1.get_coords()[1]).intersection(
                    itm.get_coords()[1]):
                    return True
        else:
            if itm != obj1:
                if set(obj1.get_coords()[0]).intersection(itm.get_coords()[0]) and set(
                        obj1.get_coords()[1]).intersection(
                    itm.get_coords()[1]):
                    return True
    return False


class Wall:
    def __init__(self, w, h, x, y):
        self.height = h
        self.width = w
        self.x = x
        self.y = y
        self.is_player_collide = True

    def render(self, screen):
        pygame.draw.rect(screen, (255, 255, 255), (self.x, self.y, self.width, self.height))

    def get_coords(self):
        return range(self.x, self.x + self.width), range(self.y, self.y + self.height)


class Bullet:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.height = 10
        self.width = 20
        self.is_player_collide = False
        self.direction = direction

    def render(self, screen):
        if check_intersect(self):
            objects.remove(self)
            del self
        else:
            pygame.draw.rect(screen, pygame.color.Color("red"), (self.x, self.y, self.width, self.height))
            if self.direction == "L":
                self.x -= 4
            else:
                self.x += 4
            if self.x > WIDTH:
                del self

    def get_coords(self):
        return range(self.x, self.x + self.width), range(self.y, self.y + self.height)


class Player:
    def __init__(self, w, h, x, y, animation):
        self.height = h
        self.width = w
        self.x = x
        self.y = y
        self.hp = 100

        self.is_jump = False
        self.max_jump = 200
        self.jump_height = 0
        self.is_down = False
        self.is_walk_r = False
        self.is_walk_l = False
        self.is_idle = True
        self.g = 0.2
        self.jump_speed = 0
        self.fall_speed = 0

        self.ammo = 10
        self.is_reload = False
        self.direction = "R"
        self.shoot_clock = Timer()
        self.shoot_clock.start()
        self.animations = animation

        self.images = {"idle_r": [], "idle_l": [], "run_r": [], "run_l": []}
        for i in range(0, 97, 32):
            self.images["idle_r"].append(
                pygame.transform.scale(animation["idle"].subsurface(pygame.Rect(i, 0, 32, 32)),
                                       (self.width, self.height)))
            self.images["idle_l"].append(
                pygame.transform.flip(pygame.transform.scale(animation["idle"].subsurface(pygame.Rect(i, 0, 32, 32)),
                                                             (self.width, self.height)), True, False))

        for i in range(0, 160, 32):
            self.images["run_r"].append(
                pygame.transform.scale(animation["run"].subsurface(pygame.Rect(i, 0, 32, 32)),
                                       (self.width, self.height)))
            self.images["run_l"].append(
                pygame.transform.flip(pygame.transform.scale(animation["run"].subsurface(pygame.Rect(i, 0, 32, 32)),
                                                             (self.width, self.height)), True, False))
        self.index = 0
        self.image = self.images["idle_r"][self.index]
        self.animation_time = 0.1
        self.anim_cur_time = Timer()
        self.anim_cur_time.start()

    def get_coords(self):
        return range(self.x, self.x + self.width), range(int(self.y) - int(self.jump_height),
                                                         int(self.y) + self.height - int(self.jump_height))

    def stop_jump(self):
        self.y -= self.jump_height
        self.jump_height = 0
        self.is_down = True
        self.is_jump = False

    def render(self, screen, keys):
        if self.is_jump:
            if self.jump_height >= self.max_jump:
                self.stop_jump()
            else:
                self.jump_speed -= self.g
                if self.jump_speed < 0:
                    self.stop_jump()
                else:
                    self.jump_height += self.jump_speed
        else:
            self.fall_speed += self.g
            self.y += self.fall_speed

        if check_intersect(self):
            if self.is_jump:
                self.jump_height -= 6
                self.is_jump = False
                self.is_down = True
            else:
                self.y -= self.fall_speed
                self.fall_speed = 0
                self.is_down = False
        else:
            self.is_down = True

        if self.is_reload:
            if self.shoot_clock.get_time() > 1:
                self.is_reload = False
                self.ammo = 10

        self.move(keys, screen)

    def animation(self, type, screen):
        if self.anim_cur_time.get_time() > self.animation_time:
            self.anim_cur_time.stop()
            self.anim_cur_time.start()
            self.index += 1
            if self.index >= len(self.images[type]):
                self.index = 0
            self.image = self.images[type][self.index]
        screen.blit(self.images[type][self.index], (self.x, self.y - self.jump_height))

    def jump(self):
        if not self.is_down:
            self.jump_speed = 10
            self.is_jump = True

    def move(self, keys, screen):
        if keys[pygame.K_d]:
            self.x += 2
            self.direction = "R"
            if check_intersect(self):
                self.x -= 2
                if self.is_walk_l or self.is_walk_r:
                    self.index = 0
                self.animation("idle_r", screen)
                self.is_walk_r = False
                self.is_walk_l = False
                return False
            else:
                self.is_walk_l = False
                self.is_walk_r = True
                if self.is_idle:
                    self.index = 0
                self.animation("run_r", screen)
                self.is_idle = False
                return True
        elif keys[pygame.K_a]:
            self.x -= 2
            self.direction = "L"
            if check_intersect(self):
                self.x += 2
                if self.is_walk_l or self.is_walk_r:
                    self.index = 0
                self.animation("idle_l", screen)
                self.is_walk_r = False
                self.is_walk_l = False
                return False
            else:
                self.is_walk_l = True
                self.is_walk_r = False
                if self.is_idle:
                    self.index = 0
                self.animation("run_l", screen)
                self.is_idle = False
                return True
        else:
            if self.is_walk_l or self.is_walk_r:
                self.index = 0
            if self.direction == "R":
                self.animation("idle_r", screen)
            else:
                self.animation("idle_l", screen)
            self.is_walk_r = False
            self.is_walk_l = False

    def shoot(self):
        if self.shoot_clock.get_time() > 0.5 and not self.is_reload:
            if not self.ammo:
                self.is_reload = True
                self.shoot_clock.stop()
                self.shoot_clock.start()
            else:
                if self.direction == "L":
                    objects.append(Bullet(self.x - 1, int(self.y + 5) - int(self.jump_height), self.direction))
                else:
                    objects.append(
                        Bullet(self.x + self.width + 1, int(self.y + 5) - int(self.jump_height), self.direction))
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

    player_animations = {"idle": pygame.image.load("data/Pink_Monster_Idle_4.png"),
                         "run": pygame.image.load("data/Pink_Monster_Run_6.png")}

    player = Player(50, 50, 0, 500, player_animations)
    floor = Wall(width, 30, 0, height - 30)
    block = Wall(100, 30, 300, 450)
    s_floor = Wall(300, 50, 0, 300)
    block_2 = Wall(300, 50, 300, 800)
    block_3 = Wall(300, 50, 400, 700)
    block_4 = Wall(300, 50, 500, 600)

    objects.append(block)
    objects.append(floor)
    objects.append(s_floor)
    objects.append(block_2)
    objects.append(block_3)
    objects.append(block_4)

    interface = Interface(player)

    running = True

    while running:
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    player.jump()
            if event.type == pygame.MOUSEBUTTONDOWN:
                player.shoot()

        screen.fill((0, 0, 0))

        for el in objects:
            el.render(screen)

        interface.render(screen)

        player.render(screen, keys)

        pygame.display.flip()
        clock.tick(fps)
