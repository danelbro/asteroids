import pygame
import sys
from onscreen_classes import Player, Shot, Asteroid, Scoreboard, Buttons

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
        self.screen = screen
        self.background = background
        self.bg_color = bg_color
        self.clock = clock
        self.fps = fps
        self.font_color = font_color
        self.font_file = font_file
        self.button_color = button_color

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
        title_font = pygame.font.Font(self.font_file, 52)        
        title_text = title_font.render('Asteroids', True, self.font_color)
        title_rect = title_text.get_rect()
        title_rect.center = (self.screen.get_rect().centerx, 200)

        buttons_panel = Buttons(self.font_file, 28, self.font_color, 
                                self.button_color, self.screen.get_width() / 2, 
                                400, 5, 'New Game', 'Options', 'Quit')

        while True:
            self.clock.tick(self.fps)
            self.background.fill(self.bg_color)
            self.screen.blit(self.background, (0,0))
            self.screen.blit(title_text, title_rect)
            buttons_panel.blit(self.screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    if event.key == pygame.K_RETURN:
                        return 'main'
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    for button in buttons_panel.buttons:
                        if button['label'] == 'New Game':
                            if button['button_rect'].collidepoint(mouse_pos):
                                return 'main'
                        elif button['label'] == 'Options':
                            if button['button_rect'].collidepoint(mouse_pos):
                                return 'options'
                        elif button['label'] == 'Quit':
                            if button['button_rect'].collidepoint(mouse_pos):
                                return None

            pygame.display.update()

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
        base_score = 150
        self.score = 0
        scoreboard_pos = (15, 10)
        player_pos = self.screen.get_rect().center
        player_dir = (0, -1)
        player_thrust = 16000
        player_mass = 32
        player_turn_speed = 500
        player_fire_rate = 10
        player_shot_power = 800
        player_animation_speed = 0.4
        player_folder_name = 'player'
        player_remains_alive = True
        level_friction = 0.1
        level = 1
        level_asteroids_offset = 3
        min_asteroid_velocity = 100
        max_asteroid_velocity = 150
        min_asteroid_direction_angle = 0.3
        min_asteroid_spawn_dist_to_player = 65
        breakaway_asteroid_velocity_scale = 1.2
        bullet_lifespan = 1.0
                    
        # initialise scoreboard, sprite groups, player and asteroids
        scoreboard = Scoreboard(self.font_file, 24, self.font_color, 
                                scoreboard_pos, level, self.score)

        players = pygame.sprite.RenderUpdates()
        self.asteroids = pygame.sprite.RenderUpdates()
        shots = pygame.sprite.RenderUpdates()
        allsprites = [players, self.asteroids, shots]

        player = Player(player_pos, player_dir, player_thrust, player_mass,
                        player_turn_speed, level_friction, player_fire_rate,
                        player_shot_power, player_animation_speed, 
                        player_folder_name, player_remains_alive)
        players.add(player)

        self.asteroids.add(Asteroid.spawn_asteroids(level + level_asteroids_offset,
                                               min_asteroid_velocity, 
                                               max_asteroid_velocity,
                                               min_asteroid_direction_angle, 
                                               player.rect, 
                                               min_asteroid_spawn_dist_to_player, 
                                               self.screen.get_width(), 
                                               self.screen.get_height()))

        # initial blit/update
        self.background.fill(self.bg_color)
        self.screen.blit(self.background, (0, 0))
        pygame.display.update()

        while True:
            dirty_rects = []
            fps_number = 1000 / self.clock.tick(self.fps)
            delta_time = self.clock.get_time() / 1000 # converted to seconds


            # check if the player got hit by an asteroid
            colliding_asteroids = pygame.sprite.spritecollide(player, self.asteroids, False,
                                                              collided=pygame.sprite.collide_mask)
            
            if len(colliding_asteroids) > 0 or not player.remains_alive:
                return 'end'

            # check if any asteroids got hit
            shot_asteroids = pygame.sprite.groupcollide(self.asteroids, shots, True, True,
                                                        collided=pygame.sprite.collide_rect_ratio(0.75))
            
            for asteroid, shot_list in shot_asteroids.items():
                self.score += int(base_score / asteroid.state)
                new_asteroids = asteroid.hit(breakaway_asteroid_velocity_scale)
                if new_asteroids is not None:
                    self.asteroids.add(new_asteroids)

            if len(self.asteroids) == 0:
                level += 1
                shots.clear(self.screen, self.background)
                shots.empty()
                self.asteroids.add(Asteroid.spawn_asteroids(level + level_asteroids_offset, 
                                                       min_asteroid_velocity,
                                                       max_asteroid_velocity,
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
                        return 'intro'
                    if event.key == pygame.K_LSHIFT:
                        player.hyperspace(len(self.asteroids))
                    if event.key == pygame.K_SPACE:
                        t = pygame.time.get_ticks()
                        shot = player.fire(t, bullet_lifespan)
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
                
            # erase and update
            scoreboard_clear_rects = [dirty_rect for dirty_rect in scoreboard.clear(self.screen, self.background)]
            scoreboard.update(level, self.score)

            for sprite_group in allsprites:
                sprite_group.clear(self.screen, self.background)
                sprite_group.update(delta_time)

            # draw to screen
            scoreboard_blit_rects = [dirty_rect for dirty_rect in scoreboard.blit(self.screen)]
            sprite_blit_rects = [dirty_rect for sprite_group in allsprites 
                                            for dirty_rect in sprite_group.draw(self.screen)]
            
            dirty_rects = scoreboard_clear_rects + scoreboard_blit_rects + sprite_blit_rects

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
        heading_font = pygame.font.Font(self.font_file, 42)        
        heading_text = heading_font.render('Game Over', True, self.font_color)
        heading_text_rect = heading_text.get_rect()
        heading_text_rect.center = (self.screen.get_width() / 2, 200)

        score_font = pygame.font.Font(self.font_file, 52)
        score_text = score_font.render('Score: ' + str(int(self.score)), 
                                       True, self.font_color)
        score_text_rect = score_text.get_rect()
        score_text_rect.center = (self.screen.get_width() / 2, 300)

        buttons_panel = Buttons(self.font_file, 28, self.font_color, 
                                self.button_color, self.screen.get_width() / 2,
                                400, 5, 'New Game', 'Main Menu', 'Quit')

        while True:
            self.clock.tick(self.fps)
            delta_time = self.clock.get_time() / 1000
            self.screen.blit(self.background, (0,0))
            self.asteroids.update(delta_time)
            self.asteroids.draw(self.screen)
            self.screen.blit(heading_text, heading_text_rect)
            self.screen.blit(score_text, score_text_rect)
            buttons_panel.blit(self.screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    if event.key == pygame.K_RETURN:
                        return 'main'
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    for button in buttons_panel.buttons:
                        if button['label'] == 'New Game':
                            if button['button_rect'].collidepoint(mouse_pos):
                                return 'main'
                        elif button['label'] == 'Main Menu':
                            if button['button_rect'].collidepoint(mouse_pos):
                                return 'intro'
                        elif button['label'] == 'Quit':
                            if button['button_rect'].collidepoint(mouse_pos):
                                return None
            
            pygame.display.update()
