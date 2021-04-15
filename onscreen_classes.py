import pygame
import random
import os
import re
import math
from resource_functions import load_image, load_sound, thousands_separator

class Player(pygame.sprite.Sprite):
    """A class to represent a controllable spaceship, with a gun and
    a hyperspace drive. Subclass of pygame.sprite.Sprite.
    """
    def __init__(self, player_pos, player_dir, thrust_power, 
                 mass, turn_speed, fluid_density, fire_rate, 
                 shot_power, animation_speed, folder_name, remains_alive):
        """Constructs a Player object.

        Args:
            player_pos (tuple): initial position for the player
            player_dir (tuple): initial direction that the player is facing
            thrust_power (int): amount of force that thrusting adds
            mass (int): mass of the spaceship, used for physics calculations
            turn_speed (int): degrees the spaceship turns by per frame
            fluid_density (float): used for calculating friction
            fire_rate (int): max amount of shots per second
            shot_power (int): speed of the bullets created by the gun
            animation_speed (float): how fast the thrusting animation plays
            folder_name (str): name of folder containing animation frames
            remains_alive (bool): whether a hyperspace jumps killed the player
        """
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
        self.remains_alive = remains_alive
 
        # facing_direction is where thrust is applied
        # velocity_direction determines how drag will be applied
        self.facing_direction = pygame.math.Vector2(player_dir)
        self.velocity = pygame.math.Vector2(0, 0)
        self.velocity_direction = pygame.math.Vector2(0, 0)

    # movement functions
    def update(self, delta_time, *args):
        """Called every frame to move the player.

        Args:
            delta_time (float): the time since the last update
        """
        # animate thrust
        if not self.thrusting:
            self.image_counter = 0
        else:
            self.image_counter += self.thrust_animation_speed
            if self.image_counter >= self.number_of_images:
                self.image_counter = 0
        self.original = self.images[int(self.image_counter)]
        
        # rotate and move
        self.apply_turn(delta_time)
        self.calc_velocity(delta_time)
        change_position = self.velocity * delta_time
        self.rect = self.check_collide(self.rect.move(change_position.x, 
                                                      change_position.y))

        # reset
        self.acceleration_magnitude = 0
        self.turn_amount = 0
    
    def check_collide(self, newpos):
        """Implements wraparound behaviour.

        Args:
            newpos (pygame.Rect): the rect of a player to be checked

        Returns:
            pygame.Rect: the rect after it's been checked
        """
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
        """Calculate velocity based on thrust and drag

        Args:
            delta_time (float): time since the last frame
        """
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
        """Change direction and rotate the image accordingly

        Args:
            delta_time (float): time since the last frame
        """
        self.facing_direction = self.facing_direction.rotate(-self.turn_amount * delta_time)

        # rotate image
        direction_angle = -math.degrees(math.atan2(self.facing_direction.y, 
                                                  self.facing_direction.x))
        self.image = pygame.transform.rotate(self.original, direction_angle)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=self.rect.center)

    # functions for responding to input
    def thrust(self):
        """Causes thrust to be applied on this frame
        """
        self.acceleration_magnitude = self.thrust_power

    def turn(self, turn_dir):
        """Causes the player to turn a particular amount this frame.

        Args:
            turn_dir (int): positive 1 for left turn, 
            negative 1 for right turn
        """
        self.turn_amount = self.turn_speed * turn_dir

    def fire(self, current_time, lifespan):
        """Creates a Shot if allowed by the player's fire rate. The shot 
        travels in the direction the player is currently facing.

        Args:
            current_time (int): 
            lifespan (float): 

        Returns:
            None: not enough time has passed since the last shot
            Shot: a shot is fired
        """
        if current_time < self.last_shot_time + self.fire_rate:
            return
        elif current_time >= self.last_shot_time + self.fire_rate:
            self.last_shot_time = current_time
            spawn_point = self.rect.center + (self.facing_direction * self.rect.height / 2 )
            return Shot(self.facing_direction, spawn_point, self.shot_power, lifespan)

    def hyperspace(self, number_of_asteroids):
        """Moves the player to a random location. Sometimes kills the 
        player; this is more likely if there are fewer asteroids on screen.

        Args:
            number_of_asteroids (int): the amount of asteroids currently 
            on screen
        """
        self.rect.center = (random.randint(0, self.area.width),
                            random.randint(0, self.area.height))

        max_percentage = 0.98
        min_percentage = 0.75
        asteroid_max = 60
        asteroid_min = 1
        
        def normalize(x, x_min, x_max):
            return x - x_min / x_max - x_min
        
        asteroids_normalized = normalize(number_of_asteroids, asteroid_min, 
                                         asteroid_max)
        
        def lerp(min, max, t):
            return (1 - t) * min + t * max
        
        if random.random() > lerp(min_percentage, max_percentage, 
                                  asteroids_normalized):
            self.remains_alive = False
        else:
            self.remains_alive = True


class DeadPlayer(pygame.sprite.Sprite):
    """Class to represent the Player after they have been killed."""
    def __init__(self, folder_name, animation_speed, pos, direction, 
                 velocity, vel_direction, fluid_density, mass, screen):
        super().__init__()
        self.images = []
        self.folder_name = os.path.join('data', 'sprites', folder_name)
        self.number_of_images = len(os.listdir(self.folder_name))
        for i in range(self.number_of_images):
            image_name = folder_name + '-' + str(i) + '.png'
            self.images.append(load_image(image_name, self.folder_name,
                                          colorkey=(255,255,255)))
        self.image = self.images[0]
        self.original = self.image
        self.direction = direction
        self.rect = self.image.get_rect(center=pos)
        self.rotate_image()
        self.animation_speed = animation_speed
        self.image_counter = 0
        self.velocity = velocity
        self.vel_direction = vel_direction
        self.fluid_density = fluid_density
        self.mass = mass
        self.area = screen.get_rect()
        
    def update(self, delta_time, *args):
        self.image_counter += self.animation_speed
        if self.image_counter >= self.number_of_images:
            self.kill()
        else:
            self.original = self.images[int(self.image_counter)]
            self.rotate_image()
            self.calc_velocity(delta_time)
            change_position = self.velocity * delta_time
            self.rect = self.check_collide(self.rect.move(change_position.x,
                                                          change_position.y))
            
    def rotate_image(self):
        direction_angle = -math.degrees(math.atan2(self.direction.y, 
                                                  self.direction.x))
        self.image = pygame.transform.rotate(self.original, direction_angle)
        self.rect = self.image.get_rect(center=self.rect.center)
    
    def calc_velocity(self, delta_time):
        drag = 0.5 * self.fluid_density * self.velocity.magnitude_squared()
        if self.velocity.magnitude() != 0:
            self.velocity_direction = self.velocity.normalize()
        else:
            self.velocity_direction = pygame.math.Vector2(0, 0)
            
        self.total_forces = drag * - self.velocity_direction
        self.acceleration = self.total_forces / self.mass
        
        self.velocity += self.acceleration * delta_time
    
    def check_collide(self, newpos):
        """Implements wraparound behaviour.

        Args:
            newpos (pygame.Rect): the rect of a player to be checked

        Returns:
            pygame.Rect: the rect after it's been checked
        """
        if newpos.bottom < 0:
            newpos.top = self.area.height
                                
        elif newpos.top > self.area.height:
            newpos.bottom = 0
                
        elif newpos.right < 0:
            newpos.left = self.area.width
                
        elif newpos.left > self.area.width:
            newpos.right = 0
        
        return newpos
    

class Shot(pygame.sprite.Sprite):
    """Class to represent a shot fired by the Player. Subclass of 
    pygame.sprite.Sprite.
    """
    def __init__(self, direction, initial_position, power, lifespan):
        """Constructs a Shot object.

        Args:
            direction (pygame.math.Vector2): direction the shot will travel
            initial_position (pygame.math.Vector2): where the shot starts
            power (int): the speed of the shot
            lifespan (float): how long in seconds the shot will last
        """
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

    def update(self, delta_time, *args):
        """Called every frame to move the shot

        Args:
            delta_time (float): time since the last frame
        """
        self.lifetime += delta_time
        if self.lifetime >= self.lifespan:
            self.kill()
        change_position = self.velocity * delta_time
        self.rect = self.check_collide(self.rect.move(change_position.x, 
                                                      change_position.y))

    def rotate_image(self):
        """Ensures the shot faces the direction it travels
        """
        spin = -math.degrees(math.atan2(self.direction.y, 
                                        self.direction.x))
        self.image = pygame.transform.rotate(self.image, spin)
        self.rect = self.image.get_rect(center=self.rect.center)
        
    def check_collide(self, newpos):
        """Implement wraparound behaviour.

        Args:
            newpos (pygame.Rect): the rect of a shot to be checked

        Returns:
            pygame.Rect: the rect after it's been checked
        """
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
    """Class to represent an Asteroid. Subclass of pygame.sprite.Sprite.
    """
    def __init__(self, velocity, direction, image_number, pos=None, state=3):
        super().__init__()
        self.state = state
        self.folder_name = os.path.join('data', 'sprites', 'asteroid')
        self.image = load_image(f'asteroid-{self.state}-{image_number}.png',
                                self.folder_name, -1)
        self.rect = self.image.get_rect()
        self.original = self.image
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        
        self.spin = 0
        self.spin_amount = 0
        while math.fabs(self.spin_amount) < 100:
            self.spin_amount = random.randint(-200, 200)
            
        self.velocity = velocity
        self.direction = direction.normalize()
        self.rect.center = pos

    def update(self, delta_time, *args):
        """Called every frame to move the asteroid.

        Args:
            delta_time (float): time since the last frame
        """
        velocity_vector = self.velocity * self.direction * delta_time
        self.rect = self.check_collide(self.rect.move(velocity_vector))
        self.rotate_image(delta_time)

    def check_collide(self, newpos):
        """Implement wraparound behaviour.

        Args:
            newpos (pygame.Rect): the rect of an asteroid to be checked

        Returns:
            pygame.Rect: the rect after it's been checked
        """
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
        """Rotates the image by a set amount every frame.

        Args:
            delta_time (float): time since the last frame
        """
        self.spin += self.spin_amount * delta_time
        if self.spin >= 360 or self.spin <= -360:
            self.spin = 0
            self.image = self.original
        else:
            self.image = pygame.transform.rotate(self.original, self.spin)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)

    def hit(self, velocity_scale):
        """Returns two new asteroids if the asteroid that got hit is large
        enough. If not, returns None.

        Args:
            velocity_scale (float): how much faster the new asteroids move
            than the parent asteroid.

        Returns:
            list[Asteroid]: the two new asteroids, if the parent is large 
            enough
            None: this is already the smallest asteroid size, so no child
            asteroids are created.
        """
        if self.state > 1:
            new_asteroids_state = self.state - 1
            first_image_number = random.randint(0, 2)
            second_image_number = first_image_number
            while second_image_number == first_image_number:
                second_image_number = random.randint(0, 2)
                
            new_asteroid_1 = Asteroid(self.velocity * velocity_scale, 
                                      self.direction.rotate(90),
                                      first_image_number,
                                      self.rect.center,
                                      new_asteroids_state)
            new_asteroid_2 = Asteroid(self.velocity * velocity_scale,
                                      self.direction.rotate(-90),
                                      second_image_number,
                                      self.rect.center,
                                      new_asteroids_state)
            return [new_asteroid_1, new_asteroid_2]             
        else: 
            return

    @staticmethod
    def spawn_asteroids(number_of_asteroids, min_speed, 
                        max_speed, min_angle, player_pos, 
                        min_player_distance, width, height):
        """Randomly generates new asteroids.

        Args:
            number_of_asteroids (int): how many asteroids to spawn
            min_speed (int): minimum speed for an asteroid
            max_speed (int): maximum speed for an asteroid
            min_angle (float): minimum magnitude for x and y on a unit
            circle to determine the angle of the asteroid's velocity
            player_pos (pygame.Rect): the position of the player (to 
            avoid on spawn)
            min_player_distance (int): minimum distance from the 
            player's position
            width (int): width of the screen
            height (int): height of the screen

        Returns:
            list[Asteroid]: the asteroids that were spawned
        """
        asteroid_list = []
        while number_of_asteroids > 0:
            # get a random acceptable velocity for this asteroid
            asteroid_speed = random.randint(min_speed, max_speed)

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
            
            image_number = random.randint(0,2)
            
            asteroid_list.append(Asteroid(asteroid_speed, 
                                          asteroid_direction, 
                                          image_number,
                                          position))
            number_of_asteroids -= 1

        return asteroid_list


class Title():
    def __init__(self, text, font_file, size, font_color, pos):
        font = pygame.ftfont.Font(font_file, size)        
        self.text = font.render(text, True, font_color)
        self.text_rect = self.text.get_rect()
        self.text_rect.center = pos
        self.height = self.text_rect.height
    
    def update(self, *args):
        pass
    
    def clear(self, screen, background):
        return [screen.blit(background, self.text_rect, self.text_rect)]
    
    def draw(self, screen):
        return [screen.blit(self.text, self.text_rect)]
    

class Scoreboard():
    """Class that represents a scoreboard to be drawn. Shows level, score
    and remaining lives.
    """
    def __init__(self, font_file, size, font_color,
                 pos, level, score):
        """Constructs a Scoreboard object.

        Args:
            font_file (str): path to .ttf font file
            size (int): font size
            font_color (tuple): font colour
            pos (tuple): top left point of scoreboard
            level (int): starting level
            score (int): starting score
        """
        self.font = pygame.ftfont.Font(font_file, size)
        self.font_color = font_color
        self.pos = pos
        self.level = level
        self.score = score

        self.level_text = self.font.render(f'Level {self.level}',
                                           True, self.font_color)
        self.level_text_rect = self.level_text.get_rect(topleft=self.pos)
        self.score_text = self.font.render(f'Score: {str(self.score)}',
                                           True, self.font_color)
        self.score_pos = (self.pos[0], 
                          self.pos[1] + 
                          self.level_text_rect.height)
        self.score_text_rect = self.score_text.get_rect(topleft=self.score_pos)
                            

    def update(self, delta_time, level, score):
        """Called every frame. Updates level or score if they are different
        to those stored in the scoreboard.

        Args:
            level (int): the new level to be checked
            score (int): the new score to be checked
        """
        if level != self.level:
            self.level = level
            self.level_text = self.font.render(f'Level {self.level}', 
                                               True, self.font_color)
            self.level_text_rect = self.level_text.get_rect(topleft=self.pos)
        if score != self.score:
            self.score = score
            self.score_text = self.font.render(f'Score: {str(thousands_separator(self.score))}',
                                           True, self.font_color)
            self.score_text_rect = self.score_text.get_rect(topleft=self.score_pos)

    def clear(self, screen, background):
        """Called every frame. Erases the scoreboard so it can be redrawn.

        Args:
            screen (pygame.Surface): the screen the scoreboard is on
            background (pygame.Surface): the background to draw over the 
            scoreboard to erase it

        Returns:
            list[pygame.Rect]: a list of 'dirty rects'
        """
        rects = []
        rects.append(screen.blit(background, 
                                 self.level_text_rect, self.level_text_rect))
        rects.append(screen.blit(background, 
                                 self.score_text_rect, self.score_text_rect))
        return rects

    def draw(self, screen):
        """Called every frame. Draws the scoreboard to the screen

        Args:
            screen (pygame.Surface): the screen to be drawn on

        Returns:
            list[pygame.Rect]: a list of 'dirty rects'
        """
        rects = []
        rects.append(screen.blit(self.level_text, self.level_text_rect))
        rects.append(screen.blit(self.score_text, self.score_text_rect))
        return rects


class Highscores():
    """A class to represent a list of highscores to be drawn to the screen 
    after the game is over. 
    """
    def __init__(self, new_score, font_file, font_size, font_color, 
                 x_pos, y_pos, padding, highlight_color):
        highscores = []
        self.new_highscore_position = -1
        try:
            with open('highscores.txt') as f:
                highscores_raw = f.readlines()
                scores_pattern = re.compile(r'([0-9]\. )([0-9]*)')
                for raw_score in highscores_raw:
                    scores_match = scores_pattern.search(raw_score)
                    if scores_match:
                        highscores.append(int(scores_match.group(2)))

            if len(highscores) >= 5:
                for i, score in enumerate(sorted(highscores, reverse=True)):
                    if new_score > 0 and new_score >= score:
                        highscores.insert(i, new_score)
                        self.new_highscore_position = i
                        highscores.pop()
                        new_highscore = True
                        break
                else:
                    new_highscore = False
            else:
                highscores.append(new_score)
                highscores.sort(reverse=True)
                new_highscore = True
        except FileNotFoundError:
            with open('highscores.txt', 'x') as f:
                highscores.append(new_score)
                new_highscore = True
            
        self.font = pygame.ftfont.Font(font_file, font_size)
        self.font_color = font_color
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.padding = padding
        self.scores_list = []
        
        if new_highscore:
            new_highscore_parts = {}
            new_highscore_text = self.font.render('NEW HIGHSCORE', 
                                                  True, self.font_color)
            new_highscore_text_rect = new_highscore_text.get_rect()
            self.text_height = new_highscore_text_rect.height
            new_highscore_parts['text'] = new_highscore_text
            new_highscore_parts['text_rect'] = new_highscore_text_rect
            self.scores_list.append(new_highscore_parts)
        
        for i, score in enumerate(highscores):
            score_parts = {}
            score_string = f'{str(i + 1)}. {str(thousands_separator(score))}'
            if i == self.new_highscore_position:
                score_text = self.font.render(score_string, True,
                                              self.font_color,
                                              highlight_color)
                score_text.convert_alpha()
            else:
                score_text = self.font.render(score_string, True, 
                                              self.font_color)
            score_text_rect = score_text.get_rect()
            self.text_height = score_text_rect.height
            score_parts['text'] = score_text
            score_parts['text_rect'] = score_text_rect
            self.scores_list.append(score_parts)
            
        # position rects
        for i in range(len(self.scores_list)):
            text_position = (self.x_pos,
                             self.y_pos +
                             (self.text_height * i) + 
                             (self.padding * i))
            self.scores_list[i]['text_rect'].midtop = text_position
        
        self.height = (self.scores_list[-1]['text_rect'].bottom - 
                       self.scores_list[0]['text_rect'].top)
                       
        with open('highscores.txt', 'w') as f:
            for i, score in enumerate(highscores):
                f.write(f'{str(i + 1)}. {str(score)}\n')
                    
    def update(self, *args):
        pass
    
    def clear(self, screen, background):
        rects = []
        for score_text in self.scores_list:
            rects.append(screen.blit(background, 
                                     score_text['text_rect'], 
                                     score_text['text_rect']))
        return rects
    
    def draw(self, screen):
        rects = []
        for score_text in self.scores_list:
            rects.append(screen.blit(score_text['text'], 
                                     score_text['text_rect']))
        return rects

class Buttons():
    """A class to represent a panel of buttons for a menu. Dynamically
    positions buttons based on number of labels requested.
    """
    def __init__(self, font_file, size, font_color, button_color, 
                 x_pos, y_pos, padding, *labels):
        """Constructs a Buttons object.

        Args:
            font_file (str): path to .ttf font file
            size (int): font size
            font_color (tuple): font colour
            button_color (tuple): button colour
            x_pos (int): desired top left x position for the panel
            y_pos (int): desired top left y position for the panel
            padding (int): padding between buttons and between button
            edge and text
        """
        self.font = pygame.ftfont.Font(font_file, size)
        self.font_color = font_color
        self.button_color = button_color
        self.x_pos = x_pos
        self.y_pos = y_pos
        self.padding = padding

        self.buttons = []
        self.widest = 0
        self.highest = 0

        # render labels and get the maximum width and height. 
        for i, label in enumerate(labels):
            button_parts = {}
            button_text = self.font.render(label, True, self.font_color)
            button_text_rect = button_text.get_rect()
            if button_text_rect.width > self.widest:
                self.widest = button_text_rect.width
            if button_text_rect.height > self.highest:
                self.highest = button_text_rect.height
            button_parts['label'] = label
            button_parts['button_text'] = button_text
            button_parts['button_text_rect'] = button_text_rect
            self.buttons.append(button_parts)
        
        # render buttons
        self.button_width = self.widest + self.padding * 2
        self.button_height = self.highest + self.padding * 2
        for button_group in self.buttons:
            button_rect = pygame.Rect((0,0), (self.button_width, 
                                              self.button_height))
            button = pygame.Surface(button_rect.size, 
                                    flags=pygame.SRCALPHA).convert_alpha()
            button.fill(self.button_color)
            button_group['button'] = button
            button_group['button_rect'] = button_rect
        
        self.reposition()
            
        self.height = (self.buttons[-1]['button_rect'].bottom -
                       self.buttons[0]['button_rect'].top)
    
    def reposition(self):
        for i in range(len(self.buttons)):
            button_position = (self.x_pos, 
                               self.y_pos + 
                               (self.button_height * i) +
                               (self.padding * i))
            text_position = (self.x_pos, 
                             self.y_pos + 
                             (self.button_height * i) + 
                             self.padding + 
                             (self.padding * i))
                
            self.buttons[i]['button_rect'].midtop = button_position
            self.buttons[i]['button_text_rect'].midtop = text_position
    
    def clear(self, screen, background):
        rects = []
        for button_group in self.buttons:
            rects.append(screen.blit(background, button_group['button_rect'],
                        button_group['button_rect']))
            rects.append(screen.blit(background, 
                                     button_group['button_text_rect'],
                                     button_group['button_text_rect']))
        return rects
    
    def update(self, *args):
        pass

    def draw(self, screen):
        """Called every frame. Draws Buttons to screen.

        Args:
            screen (pygame.Surface): screen to draw buttons onto.
        """
        rects = []
        for button_group in self.buttons:
            rects.append(screen.blit(button_group['button'], 
                                     button_group['button_rect']))
            rects.append(screen.blit(button_group['button_text'], 
                                     button_group['button_text_rect']))
        return rects
