import pygame
import random
import os
import re
import math
import utility

class Player(pygame.sprite.Sprite):
    """A class to represent a controllable spaceship. 
    
    The player is a spaceship with a gun and a hyperspace drive. 
    Subclass of pygame.sprite.Sprite.
    """
    def __init__(self, player_pos, player_dir, thrust_power, 
                 mass, turn_speed, fluid_density, fire_rate, 
                 shot_power, thrust_animation_speed, folder_name, 
                 remains_alive):
        """Constructs a Player object.

        Args:
            player_pos (tuple): initial position for the player
            player_dir (tuple): initial direction that the player is 
            facing
            thrust_power (int): amount of force that thrusting adds
            mass (int): mass of the spaceship, used for physics 
            calculations
            turn_speed (int): degrees the spaceship turns by per frame
            fluid_density (float): used for calculating friction
            fire_rate (int): max amount of shots per second
            shot_power (int): speed of the bullets created by the gun
            animation_speed (float): how fast the thrusting animation 
            plays
            folder_name (str): name of folder containing animation 
            frames
            remains_alive (bool): whether a hyperspace jumps killed 
            the player
        """
        super().__init__()
        self._images = []
        folder = os.path.join('data', 'sprites', folder_name)
        self._number_of_images = len(os.listdir(folder))
        for i in range(self._number_of_images):
            image_name = folder_name + '-' + str(i) + '.png'
            self._images.append(utility.load_image(image_name, folder,
                                                   colorkey=(255,255,255)))
        self.image = self._images[0]
        self._image_counter = 0
        self._thrust_animation_speed = thrust_animation_speed
        self._original = self.image  # for applying rotation
        self._area = pygame.display.get_surface().get_rect()
        self.mask = pygame.mask.from_surface(self.image)

        self.rect = self.image.get_rect(
            center=pygame.math.Vector2(player_pos)
        )
        
        self._thrust_power = thrust_power
        self.thrusting = False
        self.mass = mass
        self._turn_speed = turn_speed
        self._fluid_density = fluid_density
        self._acceleration_magnitude = 0
        self._turn_amount = 0
        self._fire_rate = 1000 / fire_rate
        self._last_shot_time = 0
        self._shot_power = shot_power
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
            self._image_counter = 0
        else:
            self._image_counter += self._thrust_animation_speed
            if self._image_counter >= self._number_of_images:
                self._image_counter = 0
        self._original = self._images[int(self._image_counter)]
        
        # rotate and move
        self._apply_turn(delta_time)
        self._calc_velocity(delta_time)
        change_position = self.velocity * delta_time
        self.rect = _check_collide(
            self.rect.move(change_position.x, change_position.y), self._area
        )

        # reset
        self._acceleration_magnitude = 0
        self._turn_amount = 0

    def _calc_velocity(self, delta_time):
        """Calculate velocity based on thrust and drag

        Args:
            delta_time (float): time since the last frame
        """
        # calculate drag
        drag = (0.5 
                * self._fluid_density 
                * self.velocity.magnitude_squared())

        # calculate velocity direction
        if self.velocity.magnitude() != 0:
            self.velocity_direction = self.velocity.normalize()
        else:
            self.velocity_direction = pygame.math.Vector2(0, 0)

        # calculate total forces and acceleration
        total_forces = ((self._acceleration_magnitude 
                         * self.facing_direction) 
                        + (drag * -self.velocity_direction))
        acceleration = total_forces / self.mass

        # apply acceleration to velocity
        self.velocity += acceleration * delta_time

    def _apply_turn(self, delta_time):
        """Change direction and rotate the image accordingly

        Args:
            delta_time (float): time since the last frame
        """
        self.facing_direction = self.facing_direction.rotate(
            -self._turn_amount * delta_time
        )

        # rotate image
        direction_angle = -math.degrees(math.atan2(self.facing_direction.y, 
                                                  self.facing_direction.x))
        self.image = pygame.transform.rotate(self._original, direction_angle)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect(center=self.rect.center)

    # functions for responding to input
    def thrust(self):
        """Causes thrust to be applied on this frame
        """
        self._acceleration_magnitude = self._thrust_power

    def turn(self, turn_dir):
        """Causes the player to turn a particular amount this frame.

        Args:
            turn_dir (int): positive 1 for left turn, 
            negative 1 for right turn
        """
        self._turn_amount = self._turn_speed * turn_dir

    def fire(self, current_time, lifespan):
        """Creates a Shot if allowed by the player's fire rate. 
        
        The shot travels in the direction the player is currently 
        facing.

        Args:
            current_time (int): 
            lifespan (float): 

        Returns:
            None: not enough time has passed since the last shot
            Shot: a shot is fired
        """
        if current_time < self._last_shot_time + self._fire_rate:
            return
        elif current_time >= self._last_shot_time + self._fire_rate:
            self.last_shot_time = current_time
            spawn_point = self.rect.center + (self.facing_direction 
                                              * (self.rect.height / 2))
            return Shot(self.facing_direction, spawn_point, 
                        self._shot_power, lifespan)

    def hyperspace(self, number_of_asteroids):
        """Moves the player to a random location. 
        
        Sometimes kills the player; this is more likely if there are 
        fewer asteroids on screen.

        Args:
            number_of_asteroids (int): the amount of asteroids 
            currently on screen
        """
        self.rect.center = (random.randint(0, self._area.width),
                            random.randint(0, self._area.height))

        max_percentage = 0.98
        min_percentage = 0.75
        asteroid_max = 60
        asteroid_min = 1
        
        asteroids_normalized = utility.normalize(number_of_asteroids, 
                                                 asteroid_min,
                                                 asteroid_max)
        
        if random.random() > utility.lerp(min_percentage, max_percentage,
                                  asteroids_normalized):
            self.remains_alive = False
        else:
            self.remains_alive = True


class DeadPlayer(pygame.sprite.Sprite):
    """Class to represent the Player after they have been killed."""
    def __init__(self, folder_name, animation_speed, pos, direction, 
                 velocity, velocity_direction, fluid_density, mass):
        super().__init__()
        self._images = []
        folder = os.path.join('data', 'sprites', folder_name)
        self._number_of_images = len(os.listdir(folder))
        for i in range(self._number_of_images):
            image_name = folder_name + '-' + str(i) + '.png'
            self._images.append(utility.load_image(image_name, folder,
                                                   colorkey=(255,255,255)))
        self.image = self._images[0]
        self._original = self.image
        self._direction = direction
        self.rect = self.image.get_rect(center=pos)
        self._rotate_image()
        self._animation_speed = animation_speed
        self._image_counter = 0
        self.velocity = velocity
        self.velocity_direction = velocity_direction
        self._fluid_density = fluid_density
        self.mass = mass
        self._area = pygame.display.get_surface().get_rect()
        
    def update(self, delta_time, *args):
        self._image_counter += self._animation_speed
        if self._image_counter >= self._number_of_images:
            self.kill()
        else:
            self._original = self._images[int(self._image_counter)]
            self._rotate_image()
            self._calc_velocity(delta_time)
            change_position = self.velocity * delta_time
            self.rect = _check_collide(self.rect.move(change_position.x, 
                                                     change_position.y),
                                      self._area)
            
    def _rotate_image(self):
        direction_angle = -math.degrees(math.atan2(self._direction.y, 
                                                   self._direction.x))
        self.image = pygame.transform.rotate(self._original, direction_angle)
        self.rect = self.image.get_rect(center=self.rect.center)
    
    def _calc_velocity(self, delta_time):
        drag = (0.5 
                * self._fluid_density 
                * self.velocity.magnitude_squared())
        
        if self.velocity.magnitude() != 0:
            self.velocity_direction = self.velocity.normalize()
        else:
            self.velocity_direction = pygame.math.Vector2(0, 0)
            
        total_forces = drag * - self.velocity_direction
        acceleration = total_forces / self.mass

        self.velocity += acceleration * delta_time
    

class Shot(pygame.sprite.Sprite):
    """Class to represent a shot fired by the Player. 
    
    Subclass of pygame.sprite.Sprite.
    """
    def __init__(self, direction, initial_position, power, lifespan):
        """Constructs a Shot object.

        Args:
            direction (pygame.math.Vector2): direction the shot will 
            travel
            initial_position (pygame.math.Vector2): where the shot 
            starts
            power (int): the speed of the shot
            lifespan (float): how long in seconds the shot will last
        """
        super().__init__()
        folder = os.path.join('data', 'sprites', 'shot')
        self.image = utility.load_image('shot.png', folder, -1)
        self.rect = self.image.get_rect(
            center=pygame.math.Vector2(initial_position)
        )
        self.mask = pygame.mask.from_surface(self.image)
        self._area = pygame.display.get_surface().get_rect()
        
        self._direction = direction
        self.velocity = power * self._direction
        self._rotate_image()

        self._lifetime = 0.0
        self._lifespan = lifespan

    def update(self, delta_time, *args):
        """Called every frame to move the shot

        Args:
            delta_time (float): time since the last frame
        """
        self._lifetime += delta_time
        if self._lifetime >= self._lifespan:
            self.kill()
        change_position = self.velocity * delta_time
        self.rect = _check_collide(self.rect.move(change_position.x, 
                                                 change_position.y), 
                                  self._area)

    def _rotate_image(self):
        """Ensures the shot faces the direction it travels
        """
        rotation = -math.degrees(math.atan2(self._direction.y, 
                                            self._direction.x))
        self.image = pygame.transform.rotate(self.image, rotation)
        self.rect = self.image.get_rect(center=self.rect.center)
        

class Asteroid(pygame.sprite.Sprite):
    """Class to represent an Asteroid. 
    
    Subclass of pygame.sprite.Sprite.
    """
    def __init__(self, velocity, direction, image_number, 
                 spin_amount, pos=None, state=3):
        super().__init__()
        self.state = state
        folder = os.path.join('data', 'sprites', 'asteroid')
        self.image_number = image_number
        self.image = utility.load_image(
            f'asteroid-{self.state}-{self.image_number}.png',
            folder, -1
        )
        self.rect = self.image.get_rect(center=pos)
        self._original = self.image
        self._area = pygame.display.get_surface().get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        
        self._spin = 0
        self._spin_amount = spin_amount
            
        self.velocity = velocity
        self._direction = direction.normalize()

    def update(self, delta_time, *args):
        """Called every frame to move the asteroid.

        Args:
            delta_time (float): time since the last frame
        """
        velocity_vector = self.velocity * self._direction * delta_time
        self.rect = _check_collide(self.rect.move(velocity_vector), self._area)
        self._rotate_image(delta_time)
        
    def _rotate_image(self, delta_time):
        """Rotates the image by a set amount every frame.

        Args:
            delta_time (float): time since the last frame
        """
        self._spin += self._spin_amount * delta_time
        if self._spin >= 360 or self._spin <= -360:
            self._spin = 0
            self.image = self._original
        else:
            self.image = pygame.transform.rotate(self._original, self._spin)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.mask = pygame.mask.from_surface(self.image)

    def hit(self, velocity_scale, number_to_spawn):
        """Returns new asteroids if required. 
        
        Spawns two new asteroids if the asteroid that got hit is large
        enough. If not, returns None.

        Args:
            velocity_scale (float): how much faster the new asteroids 
            move than the parent asteroid.

        Returns:
            list[Asteroid]: the two new asteroids, if the parent is 
            large enough
            None: this is already the smallest asteroid size, so no 
            child asteroids are created.
        """        
        if self.state > 1:
            new_list = []
            rotation = 0
            spawn_cycles = 0
            state = self.state - 1
            new_velocity = self.velocity * velocity_scale
            
            if number_to_spawn == 2:
                rotation = 180 / number_to_spawn
                spawn_cycles = int(number_to_spawn / 2)            
                even = True
            elif number_to_spawn % 2 == 0:
                rotation = 180 / (number_to_spawn - 1)
                spawn_cycles = int(number_to_spawn / 2)
                even = True
            else:
                rotation = 180 / number_to_spawn
                spawn_cycles = int((number_to_spawn - 1) / 2)
                even = False
                
            for i in range(spawn_cycles):
                first_image_number = random.randint(0,2)
                second_image_number = first_image_number
                while second_image_number == first_image_number:
                    second_image_number = random.randint(0,2)
                
                reflect = rotation * (i + 1)
                
                new_asteroid_1 = Asteroid(
                    new_velocity, 
                    self._direction.rotate(reflect), first_image_number, 
                    self._spin_amount, self.rect.center, state
                )
                               
                new_asteroid_2 = Asteroid(
                    new_velocity,
                    self._direction.rotate(-reflect), second_image_number, 
                    self._spin_amount, self.rect.center, state
                )
                    
                new_list.extend([new_asteroid_1, new_asteroid_2])
                
            if not even:
                if len(new_list) > 0:
                    old_image_number = new_list[-1].image_number
                    image_number = old_image_number
                    while image_number == old_image_number:
                        image_number = random.randint(0,2)

                else: # only 1 to spawn
                    image_number = random.randint(0, 2)
                
                odd_asteroid = Asteroid(new_velocity,
                                        self._direction.rotate(180),
                                        image_number, self._spin_amount,
                                        self.rect.center, state)
                
                new_list.append(odd_asteroid)
            
            return new_list
        
        else: 
            return

    @staticmethod
    def spawn(number_of_asteroids, min_speed, max_speed, min_angle, 
              player_pos, min_player_distance, width, height):
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
            speed = random.randint(min_speed, max_speed)

            # get a random acceptable direction for this asteroid
            direction = pygame.math.Vector2(0, 0)
            while (math.fabs(direction.x) < min_angle or 
                   math.fabs(direction.y) < min_angle):
                direction.x = random.uniform(-1.0, 1.0)
                direction.y = random.uniform(-1.0, 1.0)
            
            spin_amount = 0
            while math.fabs(spin_amount) < 100:
                spin_amount = random.randint(-200, 200)
            
            # get a random acceptable position for this asteroid
            position_x = player_pos.centerx
            position_y = player_pos.centery
            while (math.fabs(position_x - player_pos.centerx) 
                   < min_player_distance or
                   math.fabs(position_y - player_pos.centery) 
                   < min_player_distance):
                position_x = random.randint(0, width)
                position_y = random.randint(0, height)
            position = pygame.math.Vector2(position_x, position_y)
            
            image_number = random.randint(0,2)
            
            asteroid_list.append(Asteroid(speed, direction, image_number, 
                                          spin_amount, position))
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
    """Class that represents a scoreboard to be drawn. Shows level, 
    score and remaining lives.
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
        self._font = pygame.ftfont.Font(font_file, size)
        self._font_color = font_color
        self.pos = pos
        self.level = level
        self.score = score

        self.level_text = self._font.render(f'Level {self.level}',
                                           True, self._font_color)
        self.level_text_rect = self.level_text.get_rect(topleft=self.pos)
        self.score_text = self._font.render(f'Score: {str(self.score)}',
                                           True, self._font_color)
        self.score_pos = (self.pos[0], 
                          (self.pos[1] 
                           + self.level_text_rect.height))
        self.score_text_rect = self.score_text.get_rect(
            topleft=self.score_pos
        )
                            
    def update(self, delta_time, level, score):
        """Updates level or score.
        
        Called every frame. Updates level or score if they are 
        different to those stored in the scoreboard.

        Args:
            level (int): the new level to be checked
            score (int): the new score to be checked
        """
        if level != self.level:
            self.level = level
            self.level_text = self._font.render(
                f'Level {self.level}',
                True, self._font_color
            )
            self.level_text_rect = self.level_text.get_rect(
                topleft=self.pos
            )

        if score != self.score:
            self.score = score
            self.score_text = self._font.render(
                f'Score: {str(utility.thousands(self.score))}', 
                True, self._font_color
            )
            self.score_text_rect = self.score_text.get_rect(
                topleft=self.score_pos
            )

    def clear(self, screen, background):
        """Erases the scoreboard so it can be redrawn.
        
        Called every frame.

        Args:
            screen (pygame.Surface): the screen the scoreboard is on
            background (pygame.Surface): the background to draw over 
            the scoreboard to erase it

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
    """A class to represent a list of highscores 
    
    Drawn to the screen after the game is over. 
    """
    def __init__(self, new_score, font_file, font_size, font_color, 
                 x_pos, y_pos, padding, highlight_color):
        highscores = []
        new_highscore_position = -1
        try:
            with open('highscores.txt') as f:
                highscores_raw = f.readlines()
                scores_pattern = re.compile(r'([0-9]\. )([0-9]*)')
                for raw_score in highscores_raw:
                    scores_match = scores_pattern.search(raw_score)
                    if scores_match:
                        highscores.append(int(scores_match.group(2)))

            if len(highscores) >= 5:
                # highscore list is already at max length. we need to 
                # check whether the new_score is higher than any 
                # already in the list and remove the lowest
                for i, score in enumerate(sorted(highscores, reverse=True)):
                    if new_score > 0 and new_score > score:
                        highscores.insert(i, new_score)
                        new_highscore_position = i
                        highscores.pop()
                        new_highscore = True
                        break
                else:
                    # the new_score isn't higher than any already in 
                    # the list
                    new_highscore = False

            elif new_score > 0:
                # the higscores list is able to accept a new score, 
                # but we don't want scores of 0 to appear. First check 
                # whether the new_score is higher than any currently 
                # in the list
                new_highscore = True
                for i, score in enumerate(sorted(highscores, reverse=True)):
                    if new_score > 0 and new_score >= score:
                        highscores.insert(i, new_score)
                        new_highscore_position = i
                        break
                else:
                    # the new_score isn't higher than any current 
                    # scores, but since there's space in the list 
                    # we add it
                    highscores.append(new_score)
                    new_highscore_position = len(highscores) - 1
            else:
                # the new_score is 0
                new_highscore = False
                        
        except FileNotFoundError:
            with open('highscores.txt', 'x') as f:
                new_highscore_position = 0
                highscores.append(new_score)
                new_highscore = True

        highscores.sort(reverse=True)
        
        font = pygame.ftfont.Font(font_file, font_size)
        font_color
        self._scores_list = []
        self.x_pos = x_pos
        self.y_pos = y_pos

        if new_highscore:
            title_text = 'NEW HIGHSCORE'
        else:
            title_text = 'HIGHSCORES'
            
        new_highscore_parts = {}
        new_highscore_text = font.render(title_text, True, font_color)
        new_highscore_text_rect = new_highscore_text.get_rect()
        new_highscore_parts['text'] = new_highscore_text
        new_highscore_parts['text_rect'] = new_highscore_text_rect
        
        text_height = new_highscore_text_rect.height
        self._scores_list.append(new_highscore_parts)
        
        for i, score in enumerate(highscores):
            score_parts = {}
            score_string = f'{str(i + 1)}. {str(utility.thousands(score))}'
            
            if i == new_highscore_position:
                score_text = font.render(score_string, True, font_color, 
                                         highlight_color)
                score_text.convert_alpha()
            else:
                score_text = font.render(score_string, True, font_color)

            score_text_rect = score_text.get_rect()

            score_parts['text'] = score_text
            score_parts['text_rect'] = score_text_rect
            self._scores_list.append(score_parts)
            
        # position rects
        for i in range(len(self._scores_list)):
            text_position = (self.x_pos,
                             (self.y_pos 
                              + (text_height * i) 
                              + (padding * i)))
            self._scores_list[i]['text_rect'].midtop = text_position
        
        self.height = (self._scores_list[-1]['text_rect'].bottom 
                       - self._scores_list[0]['text_rect'].top)
                       
        with open('highscores.txt', 'w') as f:
            for i, score in enumerate(highscores):
                f.write(f'{str(i + 1)}. {str(score)}\n')
                    
    def update(self, *args):
        pass
    
    def clear(self, screen, background):
        rects = []
        for score_text in self._scores_list:
            rects.append(screen.blit(background, 
                                     score_text['text_rect'], 
                                     score_text['text_rect']))
        return rects
    
    def draw(self, screen):
        rects = []
        for score_text in self._scores_list:
            rects.append(screen.blit(score_text['text'], 
                                     score_text['text_rect']))
        return rects

class Buttons():
    """A class to represent a panel of buttons for a menu. 
    
    Dynamically positions buttons based on number of labels requested.
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
        font = pygame.ftfont.Font(font_file, size)
        self.x_pos = x_pos
        self.y_pos = y_pos
        self._padding = padding
        self.buttons = []
        
        widest = 0
        highest = 0

        # render labels and get the maximum width and height. 
        for i, label in enumerate(labels):
            button_parts = {}
            button_text = font.render(label, True, font_color)
            button_text_rect = button_text.get_rect()
            if button_text_rect.width > widest:
                widest = button_text_rect.width
            if button_text_rect.height > highest:
                highest = button_text_rect.height
            button_parts['label'] = label
            button_parts['button_text'] = button_text
            button_parts['button_text_rect'] = button_text_rect
            self.buttons.append(button_parts)
        
        # render buttons
        self._button_width = widest + (self._padding * 2)
        self._button_height = highest + (self._padding * 2)
        for button_group in self.buttons:
            button_rect = pygame.Rect((0,0), (self._button_width, 
                                              self._button_height))
            button = pygame.Surface(button_rect.size, 
                                    flags=pygame.SRCALPHA).convert_alpha()
            button.fill(button_color)
            button_group['button'] = button
            button_group['button_rect'] = button_rect
        
        self.reposition()
            
        self.height = (self.buttons[-1]['button_rect'].bottom 
                       - self.buttons[0]['button_rect'].top)
    
    def reposition(self):
        for i in range(len(self.buttons)):
            button_position = (self.x_pos, 
                               self.y_pos 
                               + (self._button_height * i) 
                               + (self._padding * i))
            text_position = (self.x_pos, 
                             self.y_pos 
                             + (self._button_height * i) 
                             + self._padding 
                             + (self._padding * i))
                
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

def _check_collide(newpos, area):
    """Implements wraparound behaviour.

    Args:
        newpos (pygame.Rect): the rect of a player to be checked

    Returns:
        pygame.Rect: the rect after it's been checked
    """
    if newpos.bottom < 0:
        newpos.top = area.height
                            
    elif newpos.top > area.height:
        newpos.bottom = 0
            
    elif newpos.right < 0:
        newpos.left = area.width
            
    elif newpos.left > area.width:
        newpos.right = 0
    
    return newpos