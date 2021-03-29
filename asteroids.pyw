import os
import sys
import math
import random
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
    """Movable 'spaceship' that represents the player. Shoots at asteroids
    and dies if hit by one.
    Returns: Player object
    Functions: reinit, update, [move functions], fire, die
    Attributes: speed"""
    
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('player.png', -1)
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.speed = 5
        self.friction = 0.2
        self.state = 'still'
        self.reinit()

    def reinit(self):
        self.state = 'still'
        self.movepos = [0,0]
        self.rect.center = self.area.center

    def update(self):
        if self.state == 'decelerating':
            self.decelerate()
        newpos = self.rect.move(self.movepos)
        if self.area.contains(newpos):
            self.rect = newpos

    def accelerate(self):
        self.state = 'moving'

    def brake(self):
        self.state = 'braking'

    def turnright(self):
        pass

    def turnleft(self):
        pass

    def stop(self):
        self.state = 'decelerating'

    def decelerate(self):
        still = [False, False]
        if self.movepos[0] < 0:
            self.movepos[0] += self.friction
        elif self.movepos[0] > 0:
            self.movepos[0] -= self.friction
        elif self.movepos[0] == 0:
            still[0] = True
            
        if self.movepos[1] < 0:
            self.movepos[1] += self.friction
        elif self.movepos[1] > 0:
            self.movepos[1] -= self.friction
        elif self.movepos[1] == 0:
            still[1] = True

        if still[0] == True and still[1] == True:
            self.state = 'still'

    def fire(self):
        print('Bang!')

        
class Asteroid(pygame.sprite.Sprite):
    def __init__(self, x_speed, y_speed):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('asteroid.png', -1)
        self.movepos = [x_speed,y_speed]
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rect.center = (random.randint(0, self.area.width),
                            random.randint(0, self.area.height))

        
    def update(self):
        newpos = self.rect.move(self.movepos)
        container_area = self.area.inflate(self.rect.width * 2, self.rect.height * 2)
        if not container_area.contains(newpos):
            tl = not container_area.collidepoint(newpos.topleft)
            tr = not container_area.collidepoint(newpos.topright)
            bl = not container_area.collidepoint(newpos.bottomleft)
            br = not container_area.collidepoint(newpos.bottomright)

            if (tl and tr):
                newpos.y = self.area.height
                                
            elif (bl and br):
                newpos.y = 0 - (self.rect.height / 2)
                
            elif (tl and bl):
                newpos.x = self.area.width
                
            elif (tr and br):
                newpos.x = 0 - (self.rect.width / 2)
                
        self.rect = newpos

class Shot(pygame.sprite.Sprite):
    pass


def main():
    pygame.init()

    if not pygame.font:
        pygame.quit()
    
    screen = pygame.display.set_mode((600, 400))
    pygame.key.set_repeat(50)
    pygame.display.set_caption('Asteroids')
    clock = pygame.time.Clock()
    fps = 60
    bg_color = (250, 250, 250)
    font = pygame.font.Font(os.path.join('data','Nunito-Regular.ttf'), 36)
    random.seed()
    
    background = pygame.Surface(screen.get_size()).convert()
    player = Player()
    asteroids  = pygame.sprite.RenderPlain()
    number_of_asteroids = random.randint(1, 10)
    while number_of_asteroids > 0:
        asteroids.add(Asteroid(random.randint(-4,4), random.randint(-4,4)))
        number_of_asteroids -= 1
        
    score = 0
    score_tracker = 0
    score_text = font.render("Score: " + str(score), True, (0, 0, 0))
    score_text_rect = score_text.get_rect(topleft=(10, 10))

    while True:
        clock.tick(fps)
        background.fill
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return
                if event.key == pygame.K_UP:
                    player.accelerate()
                if event.key == pygame.K_DOWN:
                    player.brake()
                if event.key == pygame.K_LEFT:
                    player.turnleft()
                if event.key == pygame.K_RIGHT:
                    player.turnright()
                if event.key == pygame.K_SPACE:
                    player.fire()
            elif event.type == pygame.KEYUP:
                if (event.key == pygame.K_UP or event.key == pygame.K_DOWN or
                    event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT):
                    player.stop()

        background.fill(bg_color)
        background.blit(score_text, score_text_rect)
        asteroids.update()
        screen.blit(background, (0, 0))
        asteroids.draw(screen)
        pygame.display.update()

if __name__ == '__main__':
    main()
