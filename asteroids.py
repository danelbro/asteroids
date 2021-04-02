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
                 brake_power, mass, turn_speed, fluid_density,
                 fire_rate):
        super().__init__()
        self.image, self.rect = load_image('player.png', -1)
        self.original = self.image  # for applying rotation to
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.initial_position = pygame.math.Vector2(player_pos)
        self.rect.center = self.initial_position

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
        self.fire_rate = 1000 / fire_rate
        self.last_shot_time = 0

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

    def fire(self, current_time):
        if current_time < self.last_shot_time + self.fire_rate:
            return
        elif current_time >= self.last_shot_time + self.fire_rate:
            self.last_shot_time = current_time
            return Shot(self.facing_direction, self.rect.center)

        
class Asteroid(pygame.sprite.Sprite):
    def __init__(self, x_speed, y_speed):
        super().__init__()
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
        newpos = self.check_collide(newpos)
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
    def __init__(self, direction, initial_position):
        super().__init__()
        self.speed = 25
        self.direction = direction
        self.velocity = self.speed * self.direction
        self.image, self.rect = load_image('shot.png', -1)
        self.rect.center = initial_position
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rotate_image()

    def update(self):
        newpos = self.rect.move(self.velocity.x, self.velocity.y)
        newpos = self.check_collide(newpos)
        self.rect = newpos

    def rotate_image(self):
        spin = -math.degrees(math.atan2(self.direction.y, 
                                        self.direction.x))
        self.image = pygame.transform.rotate(self.image, spin)
        self.rect = self.image.get_rect(center=self.rect.center)
        
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


def erase_group(group, blit_surface, erase_surface):
    for sprite in group.sprites():
        blit_surface.blit(erase_surface, sprite.rect, sprite.rect)


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
    
    players = pygame.sprite.RenderUpdates()
    asteroids = pygame.sprite.RenderUpdates()
    shots = pygame.sprite.RenderUpdates()
    allsprites = {'players': players, 
                  'asteroids': asteroids, 
                  'shots': shots}

    player = Player(player_pos=screen.get_rect().center, player_dir=(0,-1),
                    thrust_power=40, brake_power=15, mass=45, turn_speed=7,
                    fluid_density=0.5, fire_rate=5)
    allsprites['players'].add(player)

    number_of_asteroids = random.randint(1, 10)
    while number_of_asteroids > 0:
        x_speed = 0
        y_speed = 0
        while x_speed == 0:
            x_speed = random.randint(-4,4)
        while y_speed == 0:
            y_speed = random.randint(-4,4)
        allsprites['asteroids'].add(Asteroid(x_speed, y_speed))
        number_of_asteroids -= 1
        
    score = 0
    score_tracker = 0
    score_text = font.render("Score: " + str(score), True, font_color)
    score_text_rect = score_text.get_rect(topleft=(10, 10))

    background.fill(bg_color)
    screen.blit(background, (0,0))
    pygame.display.update()
    
    while True:
        dirty_rects = []
        clock.tick(fps)

        # handle input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            player.thrust()
        if keys[pygame.K_DOWN]:
            player.brake()
        if keys[pygame.K_LEFT]:
            player.turn('left')
        if keys[pygame.K_RIGHT]:
            player.turn('right')
        if keys[pygame.K_SPACE]:
            t = pygame.time.get_ticks()
            shot = player.fire(t)
            if shot is not None:
                shots.add(shot)
            
        screen.blit(background, score_text_rect, score_text_rect)
        for key, sprite_group in allsprites.items():
            sprite_group.clear(screen, background)
            sprite_group.update()

        score_text = font.render("Score: " + str(score), True, font_color)
        dirty_rects.append(screen.blit(score_text, score_text_rect))
        for key, sprite_group in allsprites.items():
            group_dirty_rects = sprite_group.draw(screen)
            for dirty_rect in group_dirty_rects:
                dirty_rects.append(dirty_rect)

        pygame.display.update(dirty_rects)

        shot_asteroids = pygame.sprite.groupcollide(allsprites['asteroids'],
                                                    allsprites['shots'], 
                                                    True, True,
                                                    collided=pygame.sprite.collide_rect_ratio(0.75))
                                                  
        for asteroid, shot_list in shot_asteroids.items():
            score += 1
        
if __name__ == '__main__':
    main()
