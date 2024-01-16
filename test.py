import pygame
import sys

pygame.init()


class Button:
    def __init__(self, x, y, width, height, text, image_load):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text

        self.image = pygame.image.load(image_load)
        self.image = pygame.transform.scale(self.image,(self.width, self.height))
        self.rect = self.image.get_rect(topleft=(self.width, self.height))
        self.is_hovered = False

        pygame.draw.rect(screen, (255, 0, 0), self.rect, 1)

    def draw(self, screen):
        screen.blit(self.image, self.rect.topleft)

        font = pygame.font.Font(None, 36)
        text_s = font.render(self.text, True, (255, 255, 255))
        text_r = text_s.get_rect(center=self.rect.center)
        screen.blit(text_s, text_r)

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    #def handle_event(self, event):
        #if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:

pygame.init()
size = 660, 550
screen = pygame.display.set_mode(size)
but = Button(480, 200, 100, 50, "Привет", "data/button.png")
def main_menu():
    run = True
    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                sys.exit()

        but.draw(screen)
        pygame.display.flip()

main_menu()