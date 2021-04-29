import os
os.environ['PYGAME_FREETYPE'] = "1"
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
import sys
import random
import pygame
import game_state

def main(): 
    # initialise pygame
    pygame.init()
    width = 960
    height = 720
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Asteroids')
    clock = pygame.time.Clock()
    background = pygame.Surface(screen.get_size()).convert()
    random.seed()
    still_running = True

    # common variables
    bg_color = (255, 255, 255)
    button_color = (200, 200, 200, 150)
    font_file = os.path.join('data', 'fonts', 'Nunito-Regular.ttf')
    font_color = (20, 20, 20)
    fps = 60
    padding = 5

    state_machine = game_state.StateMachine(screen, background,
                                             bg_color, clock, fps, 
                                             font_color, font_file, 
                                             button_color, padding)
 
    while still_running:
        still_running = state_machine.main_loop()

    pygame.quit()
    sys.exit()
 

if __name__ == '__main__':
    main()
