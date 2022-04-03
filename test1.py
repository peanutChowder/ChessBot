import pygame, sys

pygame.init()

screen = pygame.display.set_mode((1000, 1000))
end = False
clock = pygame.time.Clock()
position = (200, 200)

while not end:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            end = True
        if pygame.mouse.get_pressed()[0]:
            print("Click")
            position = pygame.mouse.get_pos()

    pygame.display.update()
    screen.fill((0, 0, 0))
    pygame.draw.circle(screen, pygame.Color(240, 230, 230), position, 30)
    clock.tick(60)

pygame.quit()
quit()
