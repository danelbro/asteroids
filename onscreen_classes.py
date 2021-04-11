import pygame
import random
import os
import math
from resource_functions import load_image, load_sound

class Player(pygame.sprite.Sprite):
    """A class to represent a controllable spaceship.

    Attributes: image, alt_image, images, image_counter, mask
                thrust_animation_speed, original, rect, area,
                initial_position, thrust_power, thrusting, mass, turn_speed,
                fluid_density, acceleration_magnitude, turn_amount, drag, 
                fire_rate, last_shot_time, shot_power, facing_direction, 
                velocity, velocity_direction

    Methods: update, check_collide, calc_velocity, apply_turn, thrust,
             turn, fire, hyperspace
    """

    def __init__(self, player_pos, player_dir, thrust_power, 
                 mass, turn_speed, fluid_density, fire_rate, 
                 shot_power, animation_speed, folder_name):
        super().__init__()
        self.images = []
        self.folder_name = os.path.join('data', 'sprites', folder_name)
        self.number_of_images = len(os.listdir(self.folder_name))
        for i in range(self.number_of_images):
            image_name = folder_name + '-' + str(i) + '.png'
            self.images.append(load_image(image_name, self.folder_name,
                                          colorkey=(255,255,255)))
        self.image = self.images[0]
        self.rect = self.image.get_rect()
        self.image_counter = 0
        self.thrust_animation_speed = animation_speed
                                                    
        self.original = self.image  # for applying rotation
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.initial_position = pygame.math.Vector2(player_pos)
        self.rect.center = self.initial_position
        self.mask = pygame.mask.from_surface(self.image)

        self.thrust_power = thrust_power
        self.thrusting = False
        self.mass = mass
        self.turn_speed = turn_speed
        self.fluid_density = fluid_density
        self.acceleration_magnitude = 0
        self.turn_amount = 0
        self.drag = 0
        self.fire_rate = 1000 / fire_rate
        self.last_shot_time = 0
        self.shot_power = shot_power
 
        # facing_direction is where thrust is applied
        # velocity_direction determines how drag will be applied
        self.facing_direction = pygame.math.Vector2(player_dir)
        self.velocity = pygame.math.Vector2(0, 0)
        self.velocity_direction = pygame.math.Vector2(0, 0)

    # movement functions
    def update(self, delta_time):
        # animate thrust
        if not self.thrusting:
            self.image_counter = 0
        else:
            self.image_counter += self.thrust_animation_speed
            if self.image_counter >= self.number_of_images:
                self.image_counter = 0
        self.image = self.images[int(self.image_counter)]
        self.original = self.image
        
        # rotate and move
        self.apply_turn(delta_time)
        self.calc_velocity(delta_time)
        change_position = self.velocity * delta_time
        self.rect = self.check_collide((self.rect.move(change_position.x, 
                                                       change_position.y)))

        # reset
        self.acceleration_magnitude = 0
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

    def calc_velocity(self, delta_time):
        # calculate drag
        self.drag = (0.5 * self.fluid_density * 
                      self.velocity.magnitude_squared())

        # calculate velocity direction
        if self.velocity.magnitude() != 0:
            self.velocity_direction = self.velocity.normalize()
        else:
            self.velocity_direction = pygame.math.Vector2(0, 0)

        # calculate total forces and acceleration
        self.total_forces = ((self.acceleration_magnitude * 
                              self.facing_direction) + 
                             (self.drag * -self.velocity_direction))
        self.acceleration = self.total_forces / self.mass

        # apply acceleration to velocity
        self.velocity += self.acceleration * delta_time

    def apply_turn(self, delta_time):
        self.facing_direction = self.facing_direction.rotate(-self.turn_amount * delta_time)

        # rotate image
        direction_angle = -math.degrees(math.atan2(self.facing_direction.y, 
                                                  self.facing_direction.x))
        self.image = pygame.transform.rotate(self.original, direction_angle)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=self.rect.center)

    # functions for responding to input
    def thrust(self):
        self.acceleration_magnitude = self.thrust_power

    def turn(self, turn_dir):
        if turn_dir == 'left':
            self.turn_amount = self.turn_speed
        elif turn_dir == 'right':
            self.turn_amount = -self.turn_speed

    def fire(self, current_time, lifespan):
        if current_time < self.last_shot_time + self.fire_rate:
            return
        elif current_time >= self.last_shot_time + self.fire_rate:
            self.last_shot_time = current_time
            spawn_point = self.rect.center + (self.facing_direction * self.rect.height / 2 )
            return Shot(self.facing_direction, spawn_point, self.shot_power, lifespan)

    def hyperspace(self, number_of_asteroids):
        self.rect.center = (random.randint(0, self.area.width),
                            random.randint(0, self.area.height))
        
        if random.random() > 0.95:
            return False
        else:
            return True


class Shot(pygame.sprite.Sprite):
    def __init__(self, direction, initial_position, power, lifespan):
        super().__init__()
        self.folder_name = os.path.join('data', 'sprites', 'shot')
        self.image = load_image('shot.png', self.folder_name, -1)
        self.rect = self.image.get_rect()
        self.initial_position = pygame.math.Vector2(initial_position)
        self.rect.center = initial_position
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        
        self.direction = direction
        self.velocity = power * self.direction
        self.rotate_image()

        self.lifetime = 0.0
        self.lifespan = lifespan

    def update(self, delta_time):
        self.lifetime += delta_time
        change_position = self.velocity * delta_time
        self.rect = self.check_collide(self.rect.move(change_position.x, 
                                                      change_position.y))

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
    def __init__(self, velocity, direction, pos=None, state=3):
        super().__init__()
        self.state = state
        self.folder_name = os.path.join('data', 'sprites', 'asteroid')
        self.image = load_image(f'asteroid-{self.state}.png', 
                                self.folder_name, -1)
        self.rect = self.image.get_rect()
        self.original = self.image
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        
        self.spin = 0
        self.spin_amount = 0
        while math.fabs(self.spin_amount < 100):
            self.spin_amount = random.randint(-200, 200)
            
        self.velocity = velocity
        self.direction = direction.normalize()
        self.rect.center = pos

    def update(self, delta_time):
        velocity_vector = self.velocity * self.direction * delta_time
        self.rect = self.check_collide(self.rect.move(velocity_vector))
        self.rotate_image(delta_time)

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
        
    def rotate_image(self, delta_time):
        self.spin += self.spin_amount * delta_time
        if self.spin >= 360 or self.spin <= -360:
            self.spin = 0
            self.image = self.original
        else:
            self.image = pygame.transform.rotate(self.original, self.spin)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)

    def hit(self, velocity_scale):
        if self.state > 1:
            new_asteroids_state = self.state - 1
            new_asteroid_1 = Asteroid(self.velocity * velocity_scale, 
                                      self.direction.rotate(90),
                                      self.rect.center,
                                      new_asteroids_state)
            new_asteroid_2 = Asteroid(self.velocity * velocity_scale,
                                      self.direction.rotate(-90),
                                      self.rect.center,
                                      new_asteroids_state)
            return [new_asteroid_1, new_asteroid_2]
        else: 
            return

    @staticmethod
    def spawn_asteroids(number_of_asteroids, min_velocity, 
                    max_velocity, min_angle, player_pos, 
                    min_player_distance, width, height):
        asteroid_list = []
        while number_of_asteroids > 0:
            # get a random acceptable velocity for this asteroid
            asteroid_velocity = random.randint(min_velocity, max_velocity)

            # get a random acceptable direction for this asteroid
            asteroid_direction = pygame.math.Vector2(0, 0)
            while (math.fabs(asteroid_direction.x) < min_angle or
                math.fabs(asteroid_direction.y) < min_angle):
                asteroid_direction.x = random.uniform(-1.0, 1.0)
                asteroid_direction.y = random.uniform(-1.0, 1.0)

            # get a random acceptable position for this asteroid
            position_x = player_pos.centerx
            position_y = player_pos.centery
            while (math.fabs(position_x - player_pos.centerx) < min_player_distance or
                math.fabs(position_y - player_pos.centery) < min_player_distance):
                position_x = random.randint(0, width)
                position_y = random.randint(0, height)
            position = pygame.math.Vector2(position_x, position_y)

            asteroid_list.append(Asteroid(asteroid_velocity, 
                                        asteroid_direction, 
                                        position))
            number_of_asteroids -= 1

        return asteroid_list


class Scoreboard():
    pass


class Buttons():
    pass