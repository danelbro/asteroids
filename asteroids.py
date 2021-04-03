import os
import sys
import math
import random
import pygame

if not pygame.font: print('Warning, fonts disabled.')
if not pygame.mixer: print('Warning, sound disabled.')

# RESOURCE FUNCTIONS
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
        

# CLASSES
class Player(pygame.sprite.Sprite):
    """Movable 'spaceship' that represents the player.
    """
    
    def __init__(self, player_pos, player_dir, thrust_power, 
                 brake_power, mass, turn_speed, fluid_density,
                 fire_rate, shot_power):
        super().__init__()
        self.image, self.rect = load_image('player.png', colorkey=(255,255,255))
        self.image = pygame.transform.scale(self.image, (round(self.rect.width / 2), 
                                                         round(self.rect.height / 2)))
        self.rect = self.image.get_rect()
                                                    
        self.original = self.image  # for applying rotation
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.initial_position = pygame.math.Vector2(player_pos)
        self.rect.center = self.initial_position

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
        self.shot_power = shot_power

        # directions: 
        # facing_direction is where thrust is applied
        # velocity_direction is the direction the player was
        # travelling in the previous frame, and determines how
        # drag will be applied
        self.facing_direction = pygame.math.Vector2(player_dir).normalize()
        self.velocity = pygame.math.Vector2(0,0)
        self.velocity_direction = pygame.math.Vector2(0,0)

    # movement functions
    def update(self):
        self.apply_turn()
        self.calc_velocity()
        self.rect = self.check_collide((self.rect.move(self.velocity.x, 
                                                       self.velocity.y)))

        # reset
        self.acceleration_magnitude = 0
        self.brake_magnitude = 0
        self.turn_amount = 0
    
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

    def calc_velocity(self):
        # calculate drag
        self.drag = 0.5 * self.fluid_density * (self.velocity.magnitude_squared())

        # calculate velocity direction
        if self.velocity.magnitude() != 0:
            self.velocity_direction = self.velocity.normalize()
        else:
            self.velocity_direction = pygame.math.Vector2(0,0)

        # calculate total forces and acceleration
        self.total_forces = (self.acceleration_magnitude * self.facing_direction + 
                             (self.drag * -self.velocity_direction) +
                             (self.brake_magnitude * -self.velocity_direction))
        self.acceleration = self.total_forces / self.mass

        # apply acceleration to velocity
        self.velocity += self.acceleration

    def apply_turn(self):
        direction_angle = math.atan2(self.facing_direction.y, 
                                     self.facing_direction.x)
        direction_angle -= math.radians(self.turn_amount)
        self.facing_direction.x = math.cos(direction_angle)
        self.facing_direction.y = math.sin(direction_angle)
        self.facing_direction = self.facing_direction.normalize()

        # rotate image
        self.image = pygame.transform.rotate(self.original, 
                                             math.degrees(-direction_angle))
        self.rect = self.image.get_rect(center=self.rect.center)

    # functions in response to input
    def thrust(self):
        self.acceleration_magnitude = self.thrust_power

    def brake(self):
        self.brake_magnitude = self.brake_power

    def turn(self, turn_dir):
        if turn_dir == 'left':
            self.turn_amount = self.turn_speed
        elif turn_dir == 'right':
            self.turn_amount = -self.turn_speed

    def fire(self, current_time):
        if current_time < self.last_shot_time + self.fire_rate:
            return
        elif current_time >= self.last_shot_time + self.fire_rate:
            self.last_shot_time = current_time
            return Shot(self.facing_direction, self.rect.center, 
                        speed=self.shot_power)


class Shot(pygame.sprite.Sprite):
    def __init__(self, direction, initial_position, speed=15):
        super().__init__()
        self.speed = speed
        self.direction = direction
        self.velocity = self.speed * self.direction
        self.image, self.rect = load_image('shot.png', -1)
        self.rect.center = initial_position
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.rotate_image()

    def update(self):
        self.rect = self.check_collide(self.rect.move(self.velocity.x, 
                                                      self.velocity.y))

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


class Asteroid(pygame.sprite.Sprite):
    def __init__(self, velocity, direction, state=3, pos=None):
        super().__init__()
        self.state = state
        self.image, self.rect = load_image(f'asteroid-{self.state}.png', -1)
        self.original = self.image
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        
        self.spin = 0
        self.spin_amount = 0
        while self.spin_amount == 0:
            self.spin_amount = random.randint(-2,2)
            
        self.velocity = velocity
        self.direction = direction.normalize()

        if pos is None:
            # new asteroids
            self.rect.center = (random.randint(0, self.area.width),
                                random.randint(0, self.area.height))
        else:
            # this asteroid came from another being destroyed
            # so: use position from previous asteroid
            self.rect.center = pos

    def update(self):
        velocity_vector = self.velocity * self.direction
        self.rect = self.check_collide(self.rect.move(velocity_vector))
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

    def hit(self):
        if self.state > 1:
            new_asteroids_state = self.state - 1
            new_asteroid_1 = Asteroid(self.velocity * 1.3, 
                                      self.direction.reflect((0,-1)), 
                                      new_asteroids_state, 
                                      pos=self.rect.center)
            new_asteroid_2 = Asteroid(self.velocity * 1.3,
                                      self.direction.reflect((1,0)),
                                      new_asteroids_state,
                                      pos=self.rect.center)
            return [new_asteroid_1, new_asteroid_2]
        else: 
            return


def update_score(score, font, font_color, pos):
    score_text = font.render("Score: " + str(int(score)), True, font_color)
    score_text_rect = score_text.get_rect(topleft=pos)
    return score_text, score_text_rect


def main():
    pygame.init()

    # initial variables
    height = 600
    width = 800
    fps = 60
    bg_color = (250, 250, 250)
    font_color = (20, 20, 20)
    base_score = 150
    scoreboard_pos = (10,10)

    # initialise pygame stuff
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Asteroids')
    clock = pygame.time.Clock()
    random.seed()
    background = pygame.Surface(screen.get_size()).convert()
    font = pygame.font.Font(os.path.join('data','Nunito-Regular.ttf'), 36)
        
    players = pygame.sprite.RenderUpdates()
    asteroids = pygame.sprite.RenderUpdates()
    shots = pygame.sprite.RenderUpdates()
    allsprites = [players, asteroids, shots]

    player = Player(player_pos=screen.get_rect().center, player_dir=(0,-1),
                    thrust_power=35, brake_power=15, mass=50, turn_speed=8,
                    fluid_density=0.7, fire_rate=5, shot_power=15)
    players.add(player)

    number_of_asteroids = 10
    while number_of_asteroids > 0:
        asteroid_velocity = 0
        while math.fabs(asteroid_velocity) < 2:
            asteroid_velocity = random.randint(-5,5)
        
        asteroid_direction = pygame.math.Vector2(0,0)
        while asteroid_direction.magnitude() == 0:
            asteroid_direction.x = random.uniform(-1.0, 1.0)
            asteroid_direction.y = random.uniform(-1.0, 1.0)

        asteroids.add(Asteroid(asteroid_velocity, asteroid_direction))
        number_of_asteroids -= 1
        
    score = 0
    score_text = font.render("Score: " + str(score), True, font_color)
    score_text_rect = score_text.get_rect(topleft=(10, 10))

    background.fill(bg_color)
    screen.blit(background, (0,0))
    pygame.display.update()
    
    while True:
        dirty_rects = []
        clock.tick(fps)

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
        for sprite_group in allsprites:
            sprite_group.clear(screen, background)
            sprite_group.update()

        shot_asteroids = pygame.sprite.groupcollide(asteroids, shots, True, True,
                                                    collided=pygame.sprite.collide_rect_ratio(0.75))
                                                  
        for asteroid, shot_list in shot_asteroids.items():
            score += base_score / asteroid.state
            new_asteroids = asteroid.hit()
            if new_asteroids is not None:
                asteroids.add(new_asteroids)

        score_text, score_text_rect = update_score(score, font, font_color, 
                                                   scoreboard_pos)
        dirty_rects.append(screen.blit(score_text, score_text_rect))
        for sprite_group in allsprites:
            group_dirty_rects = sprite_group.draw(screen)
            for dirty_rect in group_dirty_rects:
                dirty_rects.append(dirty_rect)

        pygame.display.update(dirty_rects)


if __name__ == '__main__':
    main()
