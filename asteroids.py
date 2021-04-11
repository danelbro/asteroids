import os
import sys
import random
import pygame
from game_state import GameState

def main():
    # initialise pygame
    pygame.init()
    width = 1280
    height = 720
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Asteroids')
    clock = pygame.time.Clock()
    background = pygame.Surface(screen.get_size()).convert()
    random.seed()
    done = False

    # common variables
    bg_color = (255, 255, 255)
    button_color = (200, 200, 200)
    font_file = os.path.join('data', 'fonts', 'Nunito-Regular.ttf')
    font_color = (20, 20, 20)
    fps = 60

    game_state = GameState(screen, background, bg_color, clock,
                           fps, font_color, font_file, button_color)

    while not done:
        done = game_state.state_controller()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
