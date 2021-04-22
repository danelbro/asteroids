import pygame
import sys
import assets
import utility
import random
import math

class GameState():
    """A class to control the game state, containing functions for
    different game states.
    """
    def __init__(self, screen, background, bg_color, 
                 clock, fps, font_color, font_file, button_color):
        """Construct a GameState object.

        Args:
            screen (pygame.Surface): the surface where the game takes 
            place 
            background (pygame.Surface): the background of the game, 
            used for clearing the screen 
            bg_color (tuple): default background colour, used for 
            clearing the screen
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
        """Runs the appropriate game state function

        Returns:
            bool: represents whether the game is finished.
        """
        self.state = self.state_dict[self.state]()
        if self.state is None:
            return True
        else:
            return False

    def intro(self):
        """Main menu/intro screen. Presents a title and menu.
        
        The menu consists of buttons which start a new game, go to the
        options menu, and quit the game.

        Returns:
            str: a new game state
            None: the player quit the game
        """
        title_y_pos = self.screen.get_rect().centery
        padding = 5
        
        title = assets.Title('Asteroids', self.font_file, 52, self.font_color,
                             (self.screen.get_rect().centerx, title_y_pos))

        buttons_panel = assets.Buttons(self.font_file, 28, self.font_color,
                                self.button_color,
                                self.screen.get_rect().centerx, 0, 
                                padding, 'New Game', 'Options', 'Quit')
        
        buttons_y_pos = (self.screen.get_height() 
                         - (padding * 4) 
                         - buttons_panel.height)
        
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

            dirty_rects = utility.draw_all(self.allsprites, self.screen, 
                                           self.background)
            pygame.display.update(dirty_rects)

    def options(self):
        """An options menu.
        
        Returns:
            str: a new game state
            None: the player quit the game
        """
        return None

    def main(self):
        """The main game loop. 
        
        The player controls a spaceship and shoots at asteroids. If the
        player is hit by an asteroid, they lose a life. Once they are 
        out of lives, the game ends. The player can also use a 
        hyperspace jump to get out of a tight spot, at the risk of
        immediately dying or landing on an asteroid. Large asteroids 
        break apart to form new asteroids. The player earns more points 
        for destroying smaller asteroids. When all asteroids are 
        cleared, a new level starts. Each level spawns more asteroids 
        than the previous level. Eventually enemy flying saucers which 
        shoot at the player appear.

        Returns:
            str: a new game state
            None: the player quit the game
        """
        # initial variables
        level_transition_time = 1000
        asteroids_spawned = False
        player_alive = True
        player_hit_time = 0
        base_score = 150
        self.score = 0
        self.level = 1
        self.lives = 3
        scoreboard_pos = (15, 10)
        
        # player variables
        player_pos = self.screen.get_rect().center
        player_dir = (0, -1)
        player_thrust = 16000
        player_mass = 32
        player_turn_speed = 400
        player_fire_rate = 6  # shots per second
        player_shot_power = 550
        player_animation_speed = 24
        player_folder_name = 'player'
        player_remains_alive = True
        player_hyperspace_length = 0.5  # in seconds
        player_respawn_flash_speed = 24
        level_transition_flash_speed = 16
        player_respawn_time = 1500 # in miliseconds
        dead_player_folder_name = 'dead_player'
        dead_player_animation_speed = 24
        player_dead_time = (dead_player_animation_speed 
                            / (dead_player_animation_speed / 1000))
        level_friction = 0.1
        player_bullet_lifespan = 1.0
                
        # enemy variables
        enemy_min_speed = 200
        enemy_max_speed = 300
        enemy_min_angle = 0.3
        min_enemy_distance = 150        
        enemy_shot_power = 500
        enemy_fire_rate = 0.5  # shots per second
        enemy_bullet_lifespan = 1.0
        enemy_spawned = False
        time_between_enemy_spawns = 7000  # in miliseconds
        enemy_overlap_offset = 4000
        enemy_max_innacuracy_angle = 20
        enemy_max_difficulty_at_score = 30000
        
        # asteroid variables
        level_asteroids_offset = 3
        min_asteroid_speed = 100
        max_asteroid_speed = 150
        min_asteroid_dir_angle = 0.3
        min_asteroid_dist = 200     # minimum distance from the player, center-to-center
        new_asteroid_velocity_scale = 1.2
        min_broken_asteroids = 2
        max_broken_asteroids = 2
                    
        # initialise scoreboard, sprite groups, player and asteroids
        scoreboard = assets.Scoreboard(self.font_file, 24, self.font_color, self.bg_color,
                                       scoreboard_pos, self.level, self.score, self.lives)
        scoreboard.hide()

        players = pygame.sprite.RenderUpdates()
        enemies = pygame.sprite.RenderUpdates()
        asteroids = pygame.sprite.RenderUpdates()
        shots = pygame.sprite.RenderUpdates()
        enemy_shots = pygame.sprite.RenderUpdates()
        self.allsprites.extend([players, enemies, asteroids, 
                                shots, enemy_shots, scoreboard])

        player = assets.Player(player_pos, player_dir, player_thrust, 
                        player_mass, player_turn_speed, level_friction, 
                        1000 / player_fire_rate, player_shot_power, 
                        player_animation_speed, player_folder_name, 
                        player_remains_alive, player_hyperspace_length,
                        self.bg_color, self.lives, player_respawn_flash_speed,
                        player_respawn_time / 1000, player_bullet_lifespan)
        players.add(player)

        # initial blit/update
        self.background.fill(self.bg_color)
        self.screen.blit(self.background, (0, 0))
        pygame.display.update()
        level_start_time = pygame.time.get_ticks() + level_transition_time
        previous_enemy_spawn = level_start_time

        # start game loop
        while True:
            dirty_rects = []
            colliding_asteroids = []
            self.clock.tick(self.fps)            
            delta_time = self.clock.get_time() / 1000 # converted to seconds
            current_time = pygame.time.get_ticks()
            player_has_control = (player.alive
                                  and not player.in_hyperspace)
            player_is_vulnerable = (player_has_control 
                                    and not player.respawning)
            
            score_at_frame_start = self.score
            
            # handle input
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.allsprites.clear()
                        return 'intro'
                    if (event.key == pygame.K_LSHIFT 
                        and player_has_control):
                        player.hyperspace(len(asteroids))
                    if (event.key == pygame.K_SPACE
                        and player_has_control):
                        shot = player.gun.fire(current_time, player.rect, 
                                               player.facing_direction)
                        if shot is not None:
                            shots.add(shot)
                elif event.type == pygame.KEYUP:
                    if (event.key == pygame.K_UP
                        and player_has_control):
                        player.engine_off()

            keys = pygame.key.get_pressed()
            if player_has_control:
                if keys[pygame.K_UP]:
                    player.engine_on()
                if keys[pygame.K_LEFT]:
                    player.turn(1)
                if keys[pygame.K_RIGHT]:
                    player.turn(-1)

            # check if the player got hit - lose a life if so
            if player_is_vulnerable:
                colliding_asteroids = pygame.sprite.groupcollide(
                    players, asteroids, False, False, 
                    pygame.sprite.collide_mask
                )
                
                colliding_enemy_shots = pygame.sprite.groupcollide(
                    players, enemy_shots, False, True,
                    pygame.sprite.collide_mask
                )

                colliding_spaceships = pygame.sprite.groupcollide(
                    players, enemies, False, False,
                    pygame.sprite.collide_mask
                )
                
                colliding_things = {**colliding_asteroids,
                                    ** colliding_enemy_shots,
                                    **colliding_spaceships}
            
                if len(colliding_things) > 0 or not player.remains_alive:
                    dead_player = assets.DeadPlayer(
                        dead_player_folder_name, dead_player_animation_speed,
                        player.rect.center, player.facing_direction,
                        player.velocity, player.velocity_direction,
                        level_friction, player.mass
                    )
                    players.remove(player)
                    player.lives -= 1
                    self.lives = player.lives
                    player.alive = False
                    player_hit_time = current_time
                    players.add(dead_player)
                    if player.lives < 1:
                        return 'end'
                    
            # respawn the player if necessary
            if (not player.alive 
                and current_time - player_hit_time >= player_dead_time):
                players.remove(dead_player)
                player.respawn(player_respawn_time / 1000, 
                               player_respawn_flash_speed,
                               self.screen.get_rect().center)
                players.add(player)
                
            # check whether enemies got shot
            enemies_shot_by_player = pygame.sprite.groupcollide(
                enemies, shots, True, True,
                pygame.sprite.collide_mask
            )
            
            for enemy, shot_list in enemies_shot_by_player.items():
                self.score += int(base_score * enemy.state)
                enemy.kill()
                enemy_spawned = False
                previous_enemy_spawn = current_time - enemy_overlap_offset
                
            # spawn an enemy if it's time
            if (not enemy_spawned 
                and current_time - previous_enemy_spawn 
                >= time_between_enemy_spawns):
                enemies.add(assets.Enemy.spawn(enemy_min_speed, 
                                               enemy_max_speed,
                                               enemy_min_angle,
                                               player.rect,
                                               min_enemy_distance,
                                               self.screen.get_rect().width,
                                               self.screen.get_rect().height,
                                               1000 / enemy_fire_rate,
                                               enemy_shot_power,
                                               enemy_bullet_lifespan, 1,
                                               enemy_max_innacuracy_angle,
                                               enemy_max_difficulty_at_score))
                previous_enemy_spawn = current_time
                enemy_spawned = True
                    
            
            # check whether asteroids got shot
            asteroids_shot_by_player = pygame.sprite.groupcollide(
                asteroids, shots, True, True,
                pygame.sprite.collide_mask
            )
            
            asteroids_shot_by_enemies = pygame.sprite.groupcollide(
                asteroids, enemy_shots, True, True,
                pygame.sprite.collide_mask
            )
            
            shot_asteroids = {**asteroids_shot_by_player,
                              **asteroids_shot_by_enemies}
            
            for asteroid, shot_list in shot_asteroids.items():
                for shot in shot_list:
                    if shot.id == 'player':
                        self.score += int(base_score / asteroid.state)
                        break
                
                number_to_spawn = random.randint(min_broken_asteroids,
                                                 max_broken_asteroids)
                new_asteroids = asteroid.hit(
                    new_asteroid_velocity_scale, number_to_spawn
                )
                if new_asteroids is not None:
                    asteroids.add(new_asteroids)
            
            # check if all asteroids were destroyed
            if len(asteroids) == 0 and len(enemies) == 0:
                # enter level transition if so
                if asteroids_spawned:
                    self.level += 1
                    shots.clear(self.screen, self.background)
                    shots.empty()
                    level_start_time = current_time + level_transition_time
                    previous_enemy_spawn = level_start_time
                    player.respawn(level_transition_time / 1000,
                                   level_transition_flash_speed,
                                   self.screen.get_rect().center,
                                   reset=False)
                    asteroids_spawned = False
                
                # start a new level if necessary
                if current_time - level_start_time >= 0:
                    scoreboard.show()
                    ast_list = assets.Asteroid.spawn((self.level 
                                                    + level_asteroids_offset),
                                                    min_asteroid_speed,
                                                    max_asteroid_speed,
                                                    min_asteroid_dir_angle,
                                                    player.rect,
                                                    min_asteroid_dist,
                                                    self.screen.get_width(),
                                                    self.screen.get_height())
                    asteroids.add(ast_list)
                    asteroids_spawned = True
            
            # have the enemy fire at the player
            for enemy in enemies.sprites():
                if enemy.primed:
                    enemy_shot = enemy.gun.fire(current_time, enemy.rect, 
                                                enemy.facing_direction)
                    if enemy_shot is not None:
                        enemy_shots.add(enemy_shot)

            # render
            dirty_rects = utility.draw_all(self.allsprites, self.screen, 
                                           self.background, delta_time, 
                                           self.score, self.level, self.lives,
                                           player_rect=player.rect)

            pygame.display.update(dirty_rects)

    def end(self):
        """The game over screen. 
        
        Presents a message, score, list of top 5 highscores, and a 
        menu to the player. If the score is higher than one of the 
        presented highscores, ask the player to enter their name to 
        save their highscore. The menu has buttons to start a new game,
        return to the main menu, or quit.

        Returns:
            str: a new game state
            None: the player quit the game.
        """
        text_pos = 50
        padding = 5
        
        heading_y_pos = text_pos
        heading = assets.Title('Game Over', self.font_file, 42, 
                               self.font_color, 
                               (self.screen.get_rect().centerx, 
                                heading_y_pos))

        score_heading_y_pos = heading_y_pos + heading.height + padding
        
        score_heading = assets.Title(('Score: ' 
                                      + str(utility.thousands(self.score))),
                                      self.font_file, 36, self.font_color, 
                                      (self.screen.get_rect().centerx,
                                       score_heading_y_pos))
        
        highscores_y_pos = (score_heading_y_pos 
                            + score_heading.height 
                            + padding)
        
        highscores = assets.Highscores(self.score, self.font_file, 36,
                                self.font_color,
                                self.screen.get_rect().centerx, 
                                highscores_y_pos, padding, self.button_color)

        buttons_panel = assets.Buttons(self.font_file, 28, self.font_color,
                                self.button_color, 
                                self.screen.get_rect().centerx, 0,
                                padding, 'New Game', 'Main Menu', 'Quit')
        
        buttons_y_pos = (self.screen.get_height() 
                         - (padding * 4) 
                         - buttons_panel.height)
        
        buttons_panel.y_pos = buttons_y_pos
        buttons_panel.reposition()
        
        time_to_start = 1000
        menu_showing = False
        start_time = pygame.time.get_ticks()

        while True:
            self.clock.tick(self.fps)
            current_time = pygame.time.get_ticks()
            delta_time = self.clock.get_time() / 1000
            
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
                    
            dirty_rects = utility.draw_all(self.allsprites, self.screen,
                                           self.background, delta_time, 
                                           self.score, self.level, self.lives)

            if (not menu_showing and
                current_time - start_time >= time_to_start):
                    menu_showing = True
                    scoreboard = self.allsprites.pop()
                    dirty_rects.extend(scoreboard.clear(self.screen, 
                                                        self.background))
                    self.allsprites.extend([heading, score_heading, 
                                            highscores, buttons_panel])
            
            pygame.display.update(dirty_rects)
