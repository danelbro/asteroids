import pygame
import sys
from onscreen_classes import (Player, 
                              DeadPlayer, 
                              Shot, 
                              Asteroid, 
                              Scoreboard, 
                              Buttons, 
                              Title,
                              Highscores)
from resource_functions import draw_all, thousands_separator

class GameState():
    """A class to control the game state, containing functions for 
    different game states.
    """
    def __init__(self, screen, background, bg_color, 
                 clock, fps, font_color, font_file, button_color):
        """Construct a GameState object.

        Args:
            screen (pygame.Surface): the surface where the game takes place
            background (pygame.Surface): the background of the game, used for
            clearing the screen
            bg_color (tuple): default background colour, used for clearing 
            the screen
            clock (pygame.time.Clock): the game clock
            fps (int): maximum framerate
            font_color (tuple): colour for text
            font_file (str): a path to a .ttf font file
            button_color (tuple): colour for buttons
        """
        self.state_dict = {'intro': self.intro, 
                           'main': self.main, 
                           'options': self.options,
                           'end': self.end}
        self.state = 'intro'
        self.score = 0
        self.level = 1
        self.screen = screen
        self.background = background
        self.bg_color = bg_color
        self.clock = clock
        self.fps = fps
        self.font_color = font_color
        self.font_file = font_file
        self.button_color = button_color
        self.allsprites = []

    def state_controller(self):
        """Runs the appropriate function based on the current game state

        Returns:
            bool: represents whether the game is finished.
        """
        self.state = self.state_dict[self.state]()
        if self.state is None:
            return True
        else:
            return False

    def intro(self):
        """Main menu/intro screen. Presents a title and menu to the user.
        The menu consists of buttons which start a new game, go to the 
        options menu, and quit the game.

        Returns:
            str: a new game state
            None: the player quit the game
        """
        title_y_pos = self.screen.get_rect().centery
        padding = 5
        
        title = Title('Asteroids', self.font_file, 52, self.font_color,
                      (self.screen.get_rect().centerx, title_y_pos))

        buttons_panel = Buttons(self.font_file, 28, self.font_color, 
                                self.button_color, 
                                self.screen.get_rect().centerx, 0, 
                                padding, 'New Game', 'Options', 'Quit')
        buttons_y_pos = (self.screen.get_height() - 
                         (padding * 4) - 
                         buttons_panel.height)
        buttons_panel.y_pos = buttons_y_pos
        buttons_panel.reposition()
        
        self.allsprites.extend([title, buttons_panel])
        self.background.fill(self.bg_color)
        self.screen.blit(self.background, (0,0))
        pygame.display.update()

        while True:
            self.clock.tick(self.fps)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    if event.key == pygame.K_RETURN:
                        self.allsprites.clear()
                        return 'main'
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    for button in buttons_panel.buttons:
                        if button['label'] == 'New Game':
                            if button['button_rect'].collidepoint(mouse_pos):
                                self.allsprites.clear()
                                return 'main'
                        elif button['label'] == 'Options':
                            if button['button_rect'].collidepoint(mouse_pos):
                                self.allsprites.clear()
                                return 'options'
                        elif button['label'] == 'Quit':
                            if button['button_rect'].collidepoint(mouse_pos):
                                return None

            dirty_rects = draw_all(self.allsprites, self.screen, self.background)
            pygame.display.update(dirty_rects)

    def options(self):
        """An options menu. Presents the user with a number of game options 
        to change.

        Returns:
            str: a new game state
            None: the player quit the game
        """
        return None

    def main(self):
        """The main game loop. The player controls a spaceship and shoots at
        asteroids. If the player is hit by an asteroid, they lose a life.
        Once they are out of lives, the game ends. The player can also use
        a hyperspace jump to get out of a tight spot, at the risk of 
        immediately dying or landing on an asteroid. Large asteroids break
        apart to form new asteroids. The player earns more points for 
        destroying smaller asteroids. When all asteroids are cleared, a new
        level starts. Each level spawns more asteroids than the previous 
        level. Eventually enemy flying saucers which shoot at the player 
        appear.

        Returns:
            str: a new game state
            None: the player quit the game
        """
        # initial variables
        time_to_start = 500
        asteroids_spawned = False
        base_score = 150
        self.score = 0
        scoreboard_pos = (15, 10)
        player_pos = self.screen.get_rect().center
        player_dir = (0, -1)
        player_thrust = 16000
        player_mass = 32
        player_turn_speed = 500
        player_fire_rate = 500 # higher numbers mean slower rate
        player_shot_power = 700
        player_animation_speed = 0.5
        player_folder_name = 'player'
        dead_player_folder_name = 'dead_player'
        dead_player_animation_speed = 0.4
        player_remains_alive = True
        level_friction = 0.1
        self.level = 1
        level_asteroids_offset = 3
        min_asteroid_speed = 100
        max_asteroid_speed = 150
        min_asteroid_direction_angle = 0.3
        min_asteroid_spawn_dist_to_player = 100
        breakaway_asteroid_velocity_scale = 1.2
        bullet_lifespan = 1.0
                    
        # initialise scoreboard, sprite groups, player and asteroids
        scoreboard = Scoreboard(self.font_file, 24, self.font_color, 
                                scoreboard_pos, self.level, self.score)

        players = pygame.sprite.RenderUpdates()
        asteroids = pygame.sprite.RenderUpdates()
        shots = pygame.sprite.RenderUpdates()
        self.allsprites.extend([players, asteroids, shots, scoreboard])

        player = Player(player_pos, player_dir, player_thrust, player_mass,
                        player_turn_speed, level_friction, player_fire_rate,
                        player_shot_power, player_animation_speed, 
                        player_folder_name, player_remains_alive)
        players.add(player)

        # initial blit/update
        self.background.fill(self.bg_color)
        self.screen.blit(self.background, (0, 0))
        pygame.display.update()
        start_time = pygame.time.get_ticks()

        while True:
            dirty_rects = []
            self.clock.tick(self.fps)
            t = pygame.time.get_ticks()            
            delta_time = self.clock.get_time() / 1000 # converted to seconds
            current_time = pygame.time.get_ticks()
            
            if (not asteroids_spawned and 
                current_time - start_time >= time_to_start):
                asteroids.add(Asteroid.spawn_asteroids(self.level + level_asteroids_offset,
                                                       min_asteroid_speed,
                                                       max_asteroid_speed,
                                                       min_asteroid_direction_angle,
                                                       player.rect,
                                                       min_asteroid_spawn_dist_to_player,
                                                       self.screen.get_width(),
                                                       self.screen.get_height()))
                asteroids_spawned = True

            # check if the player got hit by an asteroid
            colliding_asteroids = pygame.sprite.spritecollide(player, asteroids, False,
                                                              collided=pygame.sprite.collide_mask)
            
            if len(colliding_asteroids) > 0 or not player.remains_alive:
                dead_player = DeadPlayer(dead_player_folder_name, 
                                         dead_player_animation_speed,
                                         player.rect.center,
                                         player.facing_direction,
                                         player.velocity,
                                         player.velocity_direction,
                                         level_friction,
                                         player.mass,
                                         self.screen)
                # self.final_board = scoreboard
                players.remove(player)
                players.add(dead_player)
                return 'end'

            # check if any asteroids got hit
            shot_asteroids = pygame.sprite.groupcollide(asteroids, shots, True, True,
                                                        collided=pygame.sprite.collide_mask)
            
            for asteroid, shot_list in shot_asteroids.items():
                self.score += int(base_score / asteroid.state)
                new_asteroids = asteroid.hit(breakaway_asteroid_velocity_scale)
                if new_asteroids is not None:
                    asteroids.add(new_asteroids)

            if len(asteroids) == 0 and asteroids_spawned:
                self.level += 1
                shots.clear(self.screen, self.background)
                shots.empty()
                asteroids.add(Asteroid.spawn_asteroids(self.level + level_asteroids_offset,
                                                       min_asteroid_speed,
                                                       max_asteroid_speed,
                                                       min_asteroid_direction_angle,
                                                       player.rect, 
                                                       min_asteroid_spawn_dist_to_player,
                                                       self.screen.get_width(), 
                                                       self.screen.get_height()))
            
            # handle input
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.allsprites.clear()
                        return 'intro'
                    if event.key == pygame.K_LSHIFT:
                        player.hyperspace(len(asteroids))
                    if event.key == pygame.K_SPACE:
                        shot = player.fire(current_time, bullet_lifespan)
                        if shot is not None:
                            shots.add(shot)
                elif event.type == pygame.KEYUP:
                    if event.key == pygame.K_UP:
                        player.thrusting = False

            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                player.thrust()
                player.thrusting = True
            if keys[pygame.K_LEFT]:
                player.turn(1)
            if keys[pygame.K_RIGHT]:
                player.turn(-1)
            
            dirty_rects = draw_all(self.allsprites, self.screen, self.background,
                                   delta_time, self.level, self.score)

            pygame.display.update(dirty_rects)

    def end(self):
        """The game over screen. Presents a message, score, list of 
        top 5 highscores, and a menu to the player. If the score is higher
        than one of the presented highscores, ask the player to enter their
        name to save their highscore. The menu has buttons to start a new 
        game, return to the main menu, or quit.

        Returns:
            str: a new game state
            None: the player quit the game.
        """
        text_pos = 50
        padding = 5
        
        heading_y_pos = text_pos
        heading = Title('Game Over', self.font_file, 42, 
                        self.font_color, 
                        (self.screen.get_rect().centerx, heading_y_pos))

        score_heading_y_pos = heading_y_pos + heading.height + padding
        score_heading = Title('Score: ' + str(thousands_separator(self.score)), 
                              self.font_file, 36, self.font_color, 
                              (self.screen.get_rect().centerx,
                               score_heading_y_pos))
        
        highscores_y_pos = (score_heading_y_pos + 
                            score_heading.height + 
                            (padding * 4))
        highscores = Highscores(self.score, self.font_file, 36, 
                                self.font_color,
                                self.screen.get_rect().centerx, 
                                highscores_y_pos, padding, self.button_color)

        buttons_panel = Buttons(self.font_file, 28, self.font_color, 
                                self.button_color, 
                                self.screen.get_rect().centerx, 0,
                                padding, 'New Game', 'Main Menu', 'Quit')
        buttons_y_pos = (self.screen.get_height() - 
                         (padding * 4) - 
                         buttons_panel.height)
        buttons_panel.y_pos = buttons_y_pos
        buttons_panel.reposition()
        
        time_to_start = 1000
        menu_showing = False
        start_time = pygame.time.get_ticks()

        while True:
            self.clock.tick(self.fps)
            current_time = pygame.time.get_ticks()
            delta_time = self.clock.get_time() / 1000
            
            dirty_rects = draw_all(self.allsprites, self.screen,
                                   self.background, delta_time, 
                                   self.level, self.score)
            
            if (not menu_showing and
                current_time - start_time >= time_to_start):
                    menu_showing = True
                    scoreboard = self.allsprites.pop()
                    dirty_rects.extend(scoreboard.clear(self.screen, 
                                                        self.background))
                    self.allsprites.extend([heading, score_heading, 
                                            highscores, buttons_panel])
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.allsprites.clear()
                        return None
                    if event.key == pygame.K_RETURN:
                        self.allsprites.clear()
                        return 'main'
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    for button in buttons_panel.buttons:
                        if button['label'] == 'New Game':
                            if button['button_rect'].collidepoint(mouse_pos):
                                self.allsprites.clear()
                                return 'main'
                        elif button['label'] == 'Main Menu':
                            if button['button_rect'].collidepoint(mouse_pos):
                                self.allsprites.clear()
                                return 'intro'
                        elif button['label'] == 'Quit':
                            if button['button_rect'].collidepoint(mouse_pos):
                                return None

            pygame.display.update(dirty_rects)
