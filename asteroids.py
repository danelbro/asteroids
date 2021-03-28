import os, sys, math
import pygame

if not pygame.font: print('Warning, fonts disabled.')
if not pygame.mixer: print('Warning, sound disabled.')


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname).convert()
    except pygame.error as message:
        print('Cannot load image: ', name)
        raise SystemExit(message)
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, pygame.RLEACCEL)
    return image, image.get_rect()


def load_sound(name):
    class NoneSound:
        def play(self): pass
    if not pygame.mixer:
        return NoneSound()
    fullname = os.path.join('data', name)
    try:
        sound = pygame.mixer.Sound(fullname)
    except pygame.error as message:
        print('Cannot load sound:', fullname)
        raise SystemExit(message)
    return sound


class Player(pygame.sprite.Sprite):
    pass

class Asteroid(pygame.sprite.Sprite):
    pass

class Shot(pygame.sprite.Sprite):
    pass


def main():
    pygame.init()
    screen = pygame.display.set_mode((600, 400))
    pygame.display.set_caption('Asteroids')
    clock = pygame.time.Clock()
    fps = 60
    bg_color = (250, 250, 250)

    background = pygame.Surface(screen.get_size()).convert()
    background.fill(bg_color)
    screen.blit(background, (0, 0))

    dirty_rects = []

    if not pygame.font:
        pygame.quit()
    
    font = pygame.font.Font(os.path.join('data','Nunito-Regular.ttf'), 36)

    player = Player()
    asteroid = Asteroid()
    score = 0
    score_tracker = 0

    score_text = font.render("Score: " + str(score), True, (0, 0, 0))
    score_text_rect = score_text.get_rect(topleft=(10, 10))

    background.blit(score_text, score_text_rect)
    screen.blit(background, (0, 0))

    pygame.display.update()

    while True:
        clock.tick(fps)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

        background.fill(bg_color)
        screen.blit(background, score_text_rect.topleft, score_text_rect)
        dirty_rects.append(score_text_rect)

        score_tracker = score_tracker + (1/fps)
        if math.floor(score_tracker) > score:
            score = score + 1

        score_text = font.render("Score: " + str(score), True, (0, 0, 0))
        score_text_rect = score_text.get_rect(topleft=(10,10))
        background.blit(score_text, score_text_rect)
        screen.blit(background, score_text_rect.topleft, score_text_rect)
        dirty_rects.append(score_text_rect)
        
        pygame.display.update(dirty_rects)
        dirty_rects.clear()


if __name__ == '__main__':
    main()
