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
    """Movable 'spaceship' that represents the player.
    """
    
    def __init__(self, player_pos, player_dir, thrust_power, 
                 brake_power, mass, turn_speed, fluid_density):
        pygame.sprite.Sprite.__init__(self)
        self.image, self.rect = load_image('player.png', -1)
        self.original = self.image  # for applying rotation to
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.initial_position = pygame.math.Vector2(player_pos)
        self.rect.center = self.initial_position
        self.gun = Gun()

        self.thrust_power = thrust_power
        self.thrust_power = thrust_power
        self.brake_power = brake_power
        self.mass = mass
        self.turn_speed = turn_speed
        self.fluid_density = fluid_density
        self.acceleration_magnitude = 0
        self.brake_magnitude = 0
        self.turn_amount = 0
        self.drag = 0

        # directions: 
        # facing_direction is where thrust is applied
        # velocity_direction is the direction the player was
        # travelling in the previous frame, and determines how
        # drag will be applied
        self.facing_direction = pygame.math.Vector2(player_dir).normalize()
        self.velocity = pygame.math.Vector2(0,0)
        self.velocity_direction = self.calc_velocity_direction()

      
    def reinit(self):
        pass

    def calc_velocity_direction(self):
        if self.velocity.magnitude() == 0:
            self.velocity_direction = pygame.math.Vector2(0,0)
        else:
            self.velocity_direction = self.velocity.normalize()

    def update(self):
        self.calc_facing_direction()
        self.calc_velocity()
        newpos = (self.rect.move(self.velocity.x, self.velocity.y))
        newpos = self.check_collide(newpos)
        self.rect = newpos

        # reset
        self.acceleration_magnitude = 0
        self.brake_magnitude = 0
        self.turn_amount = 0

    def calc_facing_direction(self):
        # get current direction angle in radians
        current_direction_angle = math.atan2(self.facing_direction.y, 
                                             self.facing_direction.x)

        # apply turn to angle
        current_direction_angle -= math.radians(self.turn_amount)

        # update direction
        self.facing_direction.x = math.cos(current_direction_angle)
        self.facing_direction.y = math.sin(current_direction_angle)

        self.facing_direction = self.facing_direction.normalize()
        self.rotate_image()

    def calc_velocity(self):
        self.calc_drag()
        self.calc_velocity_direction()
        self.total_forces = (self.acceleration_magnitude * self.facing_direction + 
                             (self.drag * -self.velocity_direction) +
                             (self.brake_magnitude * -self.velocity_direction))
        self.acceleration = self.total_forces / self.mass
        self.velocity += self.acceleration

    def calc_drag(self):
        self.drag = 0.5 * self.fluid_density * (self.velocity.magnitude_squared())

    def check_collide(self, newpos):
        if newpos.bottom < 0:
            newpos.top = self.area.height
                                
        elif newpos.top > self.area.height:
            newpos.bottom = 0
                
        elif newpos.right < 0:
            newpos.left = self.area.width
                
        elif newpos.left > self.area.width:
            newpos.right = 0
        
        return newpos

    def thrust(self):
        self.acceleration_magnitude = self.thrust_power

    def brake(self):
        self.brake_magnitude = self.brake_power

    def turn(self, turn_dir):
        if turn_dir == 'left':
            self.turn_amount = self.turn_speed
        elif turn_dir == 'right':
            self.turn_amount = -self.turn_speed

    def rotate_image(self):
        spin = -math.degrees(math.atan2(self.facing_direction.y, 
                                        self.facing_direction.x))
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
            self.spin_amount = random.randint(-2,2)

    def update(self):
        newpos = self.rect.move(self.movepos)
        self.check_collide(newpos)
        self.rect = newpos
        self.rotate_image()

    def check_collide(self, newpos):
        if newpos.bottom < 0:
            newpos.top = self.area.height
                                
        elif newpos.top > self.area.height:
            newpos.bottom = 0
                
        elif newpos.right < 0:
            newpos.left = self.area.width
                
        elif newpos.left > self.area.width:
            newpos.right = 0
        
        return newpos
        
    def rotate_image(self):
        self.spin += self.spin_amount
        if self.spin >= 360 or self.spin <= -360:
            self.spin = 0
            self.image = self.original
        else:
            self.image = pygame.transform.rotate(self.original, self.spin)
        self.rect = self.image.get_rect(center=self.rect.center)
        

class Shot(pygame.sprite.Sprite):
    pass


def main():
    pygame.init()

    if not pygame.font:
        pygame.quit()

    height = 600
    width = 800

    screen = pygame.display.set_mode((width, height))
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
    player = Player(player_pos=screen.get_rect().center, player_dir=(0,-1),
                    thrust_power=50, brake_power=15, mass=25, turn_speed=15,
                    fluid_density=0.2)
    allsprites.add(player)
    number_of_asteroids = random.randint(1, 5)
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
