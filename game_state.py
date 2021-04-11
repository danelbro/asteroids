import pygame
import sys
from onscreen_classes import Player, Shot, Asteroid, Scoreboard, Buttons
from resource_functions import load_image, load_sound, update_text

class GameState():
    def __init__(self, screen, background, bg_color, 
                 clock, fps, font_color, font_file, button_color):
        self.state_dict = {'intro': self.intro, 
                           'main': self.main, 
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
        self.state = self.state_dict[self.state]()
        if self.state is None:
            return True

    def intro(self):
        title_font = pygame.font.Font(self.font_file, 52)
        button_font = pygame.font.Font(self.font_file, 28)

        title_text = title_font.render('Asteroids', True, self.font_color)
        title_rect = title_text.get_rect()
        title_rect.center = (self.screen.get_rect().centerx, 200)

        new_game_text = button_font.render('New Game', True, self.font_color)
        new_game_text_rect = new_game_text.get_rect()
        new_game_text_rect.center = (self.screen.get_width() / 2, 400)
        new_game_button_rect = new_game_text_rect.inflate(10,10)
        new_game_button = pygame.Surface(new_game_button_rect.size).convert()
        new_game_button.fill(self.button_color)

        quit_text = button_font.render('Quit', True, self.font_color)
        quit_text_rect = quit_text.get_rect()
        quit_text_rect.center = (self.screen.get_width() / 2, 450)
        quit_button_rect = pygame.rect.Rect(new_game_button_rect.x, 
                                            quit_text_rect.y, 
                                            new_game_button_rect.width, 
                                            quit_text_rect.height)
        quit_button = pygame.Surface(quit_button_rect.size).convert()
        quit_button.fill(self.button_color)

        while True:
            self.clock.tick(self.fps)
            self.background.fill(self.bg_color)
            self.screen.blit(self.background, (0,0))
            self.screen.blit(title_text, title_rect)
            self.screen.blit(new_game_button, new_game_button_rect)
            self.screen.blit(new_game_text, new_game_text_rect)
            self.screen.blit(quit_button, quit_button_rect)
            self.screen.blit(quit_text, quit_text_rect)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_RETURN:
                        return 'main'
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if new_game_button_rect.collidepoint(pygame.mouse.get_pos()):
                        return 'main'
                    if quit_button_rect.collidepoint(pygame.mouse.get_pos()):
                        pygame.quit()
                        sys.exit()

            pygame.display.update()
        

    def main(self):
        # initial variables
        padding = 10
        base_score = 150
        self.score = 0
        player_pos = self.screen.get_rect().center
        player_dir = (0, -1)
        player_thrust = 16000
        player_mass = 32
        player_turn_speed = 500
        player_fire_rate = 10
        player_shot_power = 800
        player_animation_speed = 0.4
        player_folder_name = 'player'
        level_friction = 0.1
        level = 1
        level_asteroids_offset = 3
        min_asteroid_velocity = 100
        max_asteroid_velocity = 150
        min_asteroid_direction_angle = 0.3
        min_asteroid_spawn_dist_to_player = 100
        breakaway_asteroid_velocity_scale = 1.2
        bullet_lifespan = 1.0
        space_pressed = False
        shift_pressed = False
        remains_alive = True
    
        # text setup
        scoreboard_font = pygame.font.Font(self.font_file, 24)
        level_text = scoreboard_font.render(str(level), True, self.font_color)
        score_text = scoreboard_font.render(str(self.score), True, self.font_color)
        level_text_pos = (padding, padding)
        level_text_rect = level_text.get_rect(topleft=level_text_pos)
        scoreboard_pos = (padding, padding * 2 + level_text_rect.height)
        score_text_rect = score_text.get_rect(topleft=scoreboard_pos)
            
        # initialise sprite groups, player and asteroids
        players = pygame.sprite.RenderUpdates()
        asteroids = pygame.sprite.RenderUpdates()
        shots = pygame.sprite.RenderUpdates()
        allsprites = [players, asteroids, shots]

        player = Player(player_pos, player_dir, player_thrust, player_mass,
                        player_turn_speed, level_friction, player_fire_rate,
                        player_shot_power, player_animation_speed, 
                        player_folder_name)
        players.add(player)

        asteroids.add(Asteroid.spawn_asteroids(level + level_asteroids_offset,
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
            dirty_rects.append(score_text_rect)
            fps_number = 1000 / self.clock.tick(self.fps)
            delta_time = self.clock.get_time() / 1000 # converted to seconds


            # check if the player got hit by an asteroid
            colliding_asteroids = pygame.sprite.spritecollide(player, asteroids, False,
                                                              collided=pygame.sprite.collide_mask)
            
            if len(colliding_asteroids) > 0 or not remains_alive:
                return 'end'

            # check if any asteroids got hit
            shot_asteroids = pygame.sprite.groupcollide(asteroids, shots, True, True,
                                                        collided=pygame.sprite.collide_rect_ratio(0.75))
            
            for asteroid, shot_list in shot_asteroids.items():
                self.score += base_score / asteroid.state
                new_asteroids = asteroid.hit(breakaway_asteroid_velocity_scale)
                if new_asteroids is not None:
                    asteroids.add(new_asteroids)

            if len(asteroids) == 0:
                level += 1
                shots.clear(self.screen, self.background)
                shots.empty()
                asteroids.add(Asteroid.spawn_asteroids(level + level_asteroids_offset, 
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
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return 'intro'
                    if event.key == pygame.K_LSHIFT:
                        remains_alive = player.hyperspace(len(asteroids))
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
                player.turn('left')
            if keys[pygame.K_RIGHT]:
                player.turn('right')
                
            # erase and update
            self.screen.blit(self.background, level_text_rect, level_text_rect)
            self.screen.blit(self.background, score_text_rect, score_text_rect)
            for sprite_group in allsprites:
                sprite_group.clear(self.screen, self.background)
                sprite_group.update(delta_time)

            for shot in shots.sprites():
                if shot.lifetime >= shot.lifespan:
                    shots.remove(shot)

            # draw to screen
            level_text, level_text_rect = update_text(level, "Level: ", 
                                                      scoreboard_font,
                                                      self.font_color, 
                                                      level_text_pos)
            score_text, score_text_rect = update_text(self.score, "Score: ",
                                                      scoreboard_font, 
                                                      self.font_color, 
                                                      scoreboard_pos)
            dirty_rects.append(self.screen.blit(level_text, level_text_rect))
            dirty_rects.append(self.screen.blit(score_text, score_text_rect))
            for sprite_group in allsprites:
                group_dirty_rects = sprite_group.draw(self.screen)
                for dirty_rect in group_dirty_rects:
                    dirty_rects.append(dirty_rect)

            pygame.display.update(dirty_rects)

    def end(self):
        heading_font = pygame.font.Font(self.font_file, 42)
        score_font = pygame.font.Font(self.font_file, 52)
        button_font = pygame.font.Font(self.font_file, 28)
        
        heading_text = heading_font.render('Game Over', True, self.font_color)
        heading_text_rect = heading_text.get_rect()
        heading_text_rect.center = (self.screen.get_width() / 2, 200)

        score_text = score_font.render('Score: ' + str(int(self.score)), 
                                       True, self.font_color)
        score_text_rect = score_text.get_rect()
        score_text_rect.center = (self.screen.get_width() / 2, 300)

        new_game_text = button_font.render('New Game', True, self.font_color)
        new_game_text_rect = new_game_text.get_rect()
        new_game_text_rect.center = (self.screen.get_width() / 2, 400)
        new_game_button_rect = new_game_text_rect.inflate(10,10)
        new_game_button = pygame.Surface(new_game_button_rect.size).convert()
        new_game_button.fill(self.button_color)

        quit_text = button_font.render('Quit', True, self.font_color)
        quit_text_rect = quit_text.get_rect()
        quit_text_rect.center = (self.screen.get_width() / 2, 450)
        quit_button_rect = pygame.rect.Rect(new_game_button_rect.x, 
                                            quit_text_rect.y, 
                                            new_game_button_rect.width, 
                                            quit_text_rect.height)
        quit_button = pygame.Surface(quit_button_rect.size).convert()
        quit_button.fill(self.button_color)

        while True:
            self.clock.tick(self.fps)
            self.background.fill(self.bg_color)
            self.screen.blit(self.background, (0,0))
            self.screen.blit(heading_text, heading_text_rect)
            self.screen.blit(score_text, score_text_rect)
            self.screen.blit(new_game_button, new_game_button_rect)
            self.screen.blit(new_game_text, new_game_text_rect)
            self.screen.blit(quit_button, quit_button_rect)
            self.screen.blit(quit_text, quit_text_rect)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_RETURN:
                        return 'main'
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()
                    if new_game_button.get_rect().collidepoint(mouse_pos):
                        return 'main'
                    elif quit_button.get_rect().collidepoint(mouse_pos):
                        pygame.quit()
                        sys.exit()
            
            pygame.display.update()

        return None
