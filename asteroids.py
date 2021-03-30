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
    
    def __init__(self, player_pos, player_dir, thrust_power, brake_power, mass,
                 turn_speed, fluid_density):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('player.png', -1)
        self.original = self.image
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.initial_position = pygame.math.Vector2(player_pos)
        self.rect.center = self.initial_position
        self.direction = pygame.math.Vector2(player_dir).normalize()
        self.thrust_power = thrust_power
        self.brake_power = brake_power
        self.mass = mass
        self.turn_speed = turn_speed
        self.fluid_density = fluid_density
        self.velocity = pygame.math.Vector2(0,0)
        self.acceleration_force = pygame.math.Vector2(0,0)
        self.turn_amount = 0
        self.rotate_amount = 0
        self.drag = 0

    """  
    def reinit(self):
        self.state = 'still'
        self.movepos = [0,0]
        self.rect.center = self.area.center
        self.image = self.original
        self.turn = 0
    """
    def update(self):
        self.calc_direction()
        self.calc_velocity()
        self.calc_drag()
        newpos = (self.rect.move(self.velocity.x, self.velocity.y))
        newpos = self.check_collide(newpos)
        self.rect = newpos
        self.acceleration_force = pygame.math.Vector2(0,0)
        self.turn_amount = 0
        self.rotate_amount = 0

    def calc_velocity(self):
        self.total_forces = (self.acceleration_force + 
                             (self.drag * -self.direction))
        self.acceleration = self.total_forces / self.mass
        self.velocity += self.acceleration

    def calc_drag(self):
        self.drag = 0.5 * self.fluid_density * (self.velocity.magnitude_squared())

    def check_collide(self, newpos):
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
                
        return newpos

    def thrust(self):
        self.calc_direction()
        self.acceleration_force = self.thrust_power * self.direction

    def brake(self):
        self.acceleration_force = -self.brake_power * self.direction

    def turn(self, turn_dir):
        if turn_dir == 'left':
            self.turn_amount = self.turn_speed
            self.rotate_amount = self.turn_speed
        elif turn_dir == 'right':
            self.turn_amount = -self.turn_speed
            self.rotate_amount = -self.turn_speed
        
    def calc_direction(self):
        # get current direction angle in radians
        current_direction_angle = math.atan2(self.direction.y, self.direction.x)

        # apply turn to angle
        current_direction_angle = math.radians(self.turn_amount)
        current_direction_angle = max(-math.tau, min(current_direction_angle, math.tau))

        # update direction
        self.direction.x = math.cos(current_direction_angle)
        self.direction.y = math.sin(current_direction_angle)
        self.rotate_image()

    def rotate_image(self):
        spin = math.degrees(math.atan2(self.direction.y, self.direction.x))
        self.image = pygame.transform.rotate(self.original, spin)
        self.rect = self.image.get_rect(center=self.rect.center)
        
    def fire(self):
        print('Bang!')

        
class Asteroid(pygame.sprite.Sprite):
    def __init__(self, x_speed, y_speed):
        pygame.sprite.Sprite.__init__(self)
        image_number = random.randint(1,3)
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
    allsprites = pygame.sprite.RenderUpdates()
    player = Player(player_pos=screen.get_rect().center, player_dir=(1,0),
                    thrust_power=40, brake_power=10, mass=20, turn_speed=35,
                    fluid_density=0.5)
    allsprites.add(player)
    number_of_asteroids = 0#random.randint(1, 10)
    while number_of_asteroids > 0:
        x_speed = 0
        y_speed = 0
        while x_speed == 0:
            x_speed = random.randint(-4,4)
        while y_speed == 0:
            y_speed = random.randint(-4,4)
        allsprites.add(Asteroid(x_speed, y_speed))
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
                    player.thrust()
                if event.key == pygame.K_DOWN:
                    player.brake()
                if event.key == pygame.K_LEFT:
                    player.turn('left')
                if event.key == pygame.K_RIGHT:
                    player.turn('right')
                if event.key == pygame.K_SPACE:
                    player.fire()
            
        # erase player, asteroids and scoreboard
        screen.blit(background, score_text_rect, score_text_rect)
        for sprite in allsprites.sprites():
            screen.blit(background, sprite.rect, sprite.rect)

        # update asteroids and scoreboard
        allsprites.update()

        # draw everything
        dirty_rects = allsprites.draw(screen)
        dirty_rects.append(screen.blit(score_text, score_text_rect))


        # show updates
        pygame.display.update(dirty_rects)
        
if __name__ == '__main__':
    main()
