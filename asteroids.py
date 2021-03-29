import os
import sys
import math
import random
import pygame

if not pygame.font: print('Warning, fonts disabled.')
if not pygame.mixer: print('Warning, sound disabled.')


def load_image(name, colorkey=None):
    if not os.path.dirname(os.getcwd()) == "asteroids":
        os.chdir(os.path.join('/', 'home', 'dan', 'python_scripts', 'asteroids', ''))
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
        image_number = random.randint(1,2)
        self.image, self.rect = load_image(f'asteroid-{image_number}.png', -1)
        self.movepos = [x_speed,y_speed]
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rect.center = (random.randint(0, self.area.width),
                            random.randint(0, self.area.height))
        self.original = self.image
        self.spin = 0
        self.spin_amount = 0
        while self.spin_amount == 0:
            self.spin_amount = random.randint(-1,1)

        
    def update(self):
        self.fly()
        self.spinner()

    def fly(self):
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
        
    def spinner(self):
        # apply some spin
        center = self.rect.center
        self.spin += self.spin_amount
        if self.spin >= 360:
            self.spin = 0
            self.image = self.original
        else:
            self.image = pygame.transform.rotate(self.original, self.spin)
        self.rect = self.image.get_rect(center=center)
        

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
    font_color = (20, 20, 20)
    if not os.path.basename(os.getcwd()) == "asteroids":
        os.chdir(os.path.join('/', 'home', 'dan', 'python_scripts', 'asteroids', ''))
    font = pygame.font.Font(os.path.join('data','Nunito-Regular.ttf'), 36)
    random.seed()
    
    background = pygame.Surface(screen.get_size()).convert()
    player = Player()
    asteroids  = pygame.sprite.RenderUpdates()
    number_of_asteroids = random.randint(1, 10)
    while number_of_asteroids > 0:
        x_speed = 0
        y_speed = 0
        while x_speed == 0:
            x_speed = random.randint(-4,4)
        while y_speed == 0:
            y_speed = random.randint(-4,4)
        asteroids.add(Asteroid(x_speed, y_speed))
        number_of_asteroids -= 1
        
    score = 0
    score_tracker = 0
    score_text = font.render("Score: " + str(score), True, font_color)
    score_text_rect = score_text.get_rect(topleft=(10, 10))

    background.fill(bg_color)
    screen.blit(background, (0,0))
    pygame.display.update()
    
    while True:
        clock.tick(fps)

        # handle input
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

        # erase asteroids and scoreboard
        screen.blit(background, score_text_rect, score_text_rect)
        for sprite in asteroids.sprites():
            screen.blit(background, sprite.rect, sprite.rect)

        # update asteroids and scoreboard
        asteroids.update()

        # draw everything
        dirty_rects = asteroids.draw(screen)
        dirty_rects.append(screen.blit(score_text, score_text_rect))

        # show updates
        pygame.display.update(dirty_rects)
        
if __name__ == '__main__':
    main()
