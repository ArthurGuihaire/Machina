import pygame
pygame.init()
screen = pygame.display.set_mode((400,400))
running = True
while running:
    rgb=(int(input("red: ")),int(input("green: ")),int(input("blue: ")))
    screen.fill(rgb)
    pygame.display.flip()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()