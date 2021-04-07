import os
import sys
import math
import random
import pygame

# CLASSES
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
                 shot_power, animation_speed):
        super().__init__()
        self.image, self.rect = load_image('player-0.png', 
                                           colorkey=(255,255,255))
        self.alt_image, self.rect = load_image('player-1.png', 
                                               colorkey=(255,255,255))
        self.images = [self.image, self.alt_image]
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
            if self.image_counter >= 2:
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
        self.thrusting = True

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
        self.image, self.rect = load_image('shot.png', -1)
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
        self.image, self.rect = load_image(f'asteroid-{self.state}.png', -1)
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


class GameState():
    def __init__(self):
        self.state_dict = {'intro': self.intro, 
                           'main': self.main, 
                           'end': self.end}
        self.state = 'intro'
        self.score = 0

    def state_controller(self, screen, background, 
                         bg_color, clock, fps, font_color):
        self.state, self.score = self.state_dict[self.state](screen, 
                                                             background,
                                                             bg_color, 
                                                             clock, fps, 
                                                             font_color, 
                                                             self.score)
        if self.state is None:
            return True

    def intro(self, screen, background, bg_color, clock, fps, font_color, score):
        title_font = pygame.font.Font(os.path.join('data', 'Nunito-Regular.ttf'), 52)
        title_text = title_font.render('Asteroids', True, font_color)
        title_rect = title_text.get_rect()
        title_rect.center = (screen.get_rect().centerx, 200)

        button_font = pygame.font.Font(os.path.join('data', 'Nunito-Regular.ttf'), 28)
        button_text = button_font.render('New Game', True, font_color)
        button_text_rect = button_text.get_rect()
        button_text_rect.center = (screen.get_rect().centerx, 400)

        while True:
            clock.tick(fps)
            background.fill(bg_color)
            screen.blit(background, (0,0))
            screen.blit(title_text, title_rect)
            screen.blit(button_text, button_text_rect)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if button_text_rect.collidepoint(pygame.mouse.get_pos()):
                        return 'main', 0

            pygame.display.update()
        

    def main(self, screen, background, bg_color, clock, fps, font_color, score):
        # initial variables
        padding = 10
        base_score = 150
        scoreboard_pos = (padding, padding)
        score = 0
        player_pos = screen.get_rect().center
        player_dir = (0, -1)
        player_thrust = 16000
        player_mass = 32
        player_turn_speed = 500
        player_fire_rate = 10
        player_shot_power = 800
        player_animation_speed = 0.5
        level_friction = 0.1
        level = 1
        level_asteroids_offset = 2
        min_asteroid_velocity = 150
        max_asteroid_velocity = 200
        min_asteroid_direction_angle = 0.7
        min_asteroid_spawn_dist_to_player = 150
        breakaway_asteroid_velocity_scale = 1.1
        bullet_lifespan = 0.75
        space_pressed = False
        shift_pressed = False
        remains_alive = True
    
        # text setup
        score_font = pygame.font.Font(os.path.join('data', 'Nunito-Regular.ttf'), 24)
        score_text = score_font.render("Score: " + str(score), True, font_color)
        score_text_rect = score_text.get_rect(topleft=scoreboard_pos)
            
        # initialise sprite groups, player and asteroids
        players = pygame.sprite.RenderUpdates()
        asteroids = pygame.sprite.RenderUpdates()
        shots = pygame.sprite.RenderUpdates()
        allsprites = [players, asteroids, shots]

        player = Player(player_pos, player_dir, player_thrust, player_mass,
                        player_turn_speed, level_friction, player_fire_rate,
                        player_shot_power, player_animation_speed)
        players.add(player)

        asteroids.add(spawn_asteroids(level + level_asteroids_offset, 
                                    min_asteroid_velocity, 
                                    max_asteroid_velocity,
                                    min_asteroid_direction_angle, player.rect, 
                                    min_asteroid_spawn_dist_to_player, 
                                    screen.get_width(), screen.get_height()))

        # initial blit/update
        background.fill(bg_color)
        screen.blit(background, (0, 0))
        pygame.display.update()

        while True:
            dirty_rects = []
            dirty_rects.append(score_text_rect)
            fps_number = 1000 / clock.tick(fps)
            delta_time = clock.get_time() / 1000 # converted to seconds


            # check if the player got hit by an asteroid
            colliding_asteroids = pygame.sprite.spritecollide(player, asteroids, False,
                                                              collided=pygame.sprite.collide_mask)
            
            if len(colliding_asteroids) > 0 or not remains_alive:
                return 'end', score

            # check if any asteroids got hit
            shot_asteroids = pygame.sprite.groupcollide(asteroids, shots, True, True,
                                                        collided=pygame.sprite.collide_rect_ratio(0.75))
            
            for asteroid, shot_list in shot_asteroids.items():
                score += base_score / asteroid.state
                new_asteroids = asteroid.hit(breakaway_asteroid_velocity_scale)
                if new_asteroids is not None:
                    asteroids.add(new_asteroids)

            if len(asteroids) == 0:
                level += 1
                shots.clear(screen, background)
                shots.empty()
                asteroids.add(spawn_asteroids(level + level_asteroids_offset, 
                                            min_asteroid_velocity, 
                                            max_asteroid_velocity,
                                            min_asteroid_direction_angle, 
                                            player.rect, 
                                            min_asteroid_spawn_dist_to_player,
                                            screen.get_width(), screen.get_height()))

            # handle input
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_SPACE:
                        space_pressed = False
                    if event.key == pygame.K_LSHIFT:
                        shift_pressed = False
                    if event.key == pygame.K_UP:
                        player.thrusting = False

            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                player.thrust()
            if keys[pygame.K_LEFT]:
                player.turn('left')
            if keys[pygame.K_RIGHT]:
                player.turn('right')
            if keys[pygame.K_LSHIFT] and not shift_pressed:
                shift_pressed = True
                remains_alive = player.hyperspace(len(asteroids))
            if keys[pygame.K_SPACE] and not space_pressed:
                t = pygame.time.get_ticks()
                space_pressed = True
                shot = player.fire(t, bullet_lifespan)
                if shot is not None:
                    shots.add(shot)
                
            # erase and update
            screen.blit(background, score_text_rect, score_text_rect)
            for sprite_group in allsprites:
                sprite_group.clear(screen, background)
                sprite_group.update(delta_time)

            for shot in shots.sprites():
                if shot.lifetime >= shot.lifespan:
                    shots.remove(shot)

            # draw to screen
            score_text, score_text_rect = update_text(score, "Score: ", score_font, 
                                                      font_color, scoreboard_pos)
            dirty_rects.append(screen.blit(score_text, score_text_rect))
            for sprite_group in allsprites:
                group_dirty_rects = sprite_group.draw(screen)
                for dirty_rect in group_dirty_rects:
                    dirty_rects.append(dirty_rect)

            pygame.display.update(dirty_rects)

    def end(self, screen, background, bg_color, clock, fps, font_color, score):
        print(str(int(score)))
        return None, 0


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


def update_text(number, title_string, font, font_color, pos):
    text = font.render(title_string + str(int(number)), True, font_color)
    text_rect = text.get_rect(topleft=pos)
    return text, text_rect


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


def main():
    pygame.init()

    # initialise pygame stuff
    width = 1280
    height = 720
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption('Asteroids')
    clock = pygame.time.Clock()
    random.seed()
    done = False

    bg_color = (255, 255, 255)
    font_color = (20, 20, 20)
    fps = 60

    background = pygame.Surface(screen.get_size()).convert()
    game_state = GameState()

    while not done:
        done = game_state.state_controller(screen, background, bg_color, 
                                           clock, fps, font_color)

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()
