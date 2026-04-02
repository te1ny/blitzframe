import pygame
import sys

pygame.init()

screen_info = pygame.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h

screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("Заглушка гаддэм sixseven")

PURPLE = (255, 0, 255)
BLACK = (0, 0, 0)

square_color = PURPLE

clock = pygame.time.Clock()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                running = False

    screen.fill(BLACK)

    pygame.draw.rect(screen, square_color, (0, 0, screen_width, screen_height))

    pygame.display.flip()

    clock.tick(60)

pygame.quit()
sys.exit()