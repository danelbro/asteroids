import pygame
import sys
import assets
import utility
import random
import math
import enum
import configparser


class GameStates(enum.Enum):
    INTRO = enum.auto()
    OPTIONS = enum.auto()
    MAIN = enum.auto()
    END = enum.auto()


class StateMachine():
    """A class to control the game state, containing functions for
    different game states.
    """

    def __init__(self, screen, background, bg_color,
                 clock, fps, font_color, font_file,
                 button_color, padding, channels):
        """Construct a StateMachine object."""
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
        self.padding = padding
        self.states_dict = {GameStates.INTRO: Intro(self.font_file,
                                                    self.font_color,
                                                    self.button_color,
                                                    self.padding,
                                                    self.screen,
                                                    self.background,
                                                    self.bg_color,
                                                    self),
                            GameStates.OPTIONS: Options(),
                            GameStates.MAIN: Main(self.font_file,
                                                  self.font_color,
                                                  self.button_color,
                                                  self.padding,
                                                  self.screen,
                                                  self.background,
                                                  self.bg_color,
                                                  self, channels),
                            GameStates.END: End(self.font_file,
                                                self.font_color,
                                                self.button_color,
                                                self.padding,
                                                self.screen,
                                                self.background,
                                                self.bg_color,
                                                self)}
        self.current_state = GameStates.INTRO

    def main_loop(self):
        self.clock.tick(self.fps)
        delta_time = self.clock.get_time() / 1000  # converted to seconds
        input_dict = self.states_dict[self.current_state].get_input()
        next_state = self.states_dict[self.current_state].update(
            input_dict, delta_time)
        self.states_dict[self.current_state].render(delta_time)

        if next_state:
            self.current_state = next_state
            return True
        else:
            return False


class Intro():
    def __init__(self, font_file, font_color, button_color, padding,
                 screen, background, bg_color, state_machine):
        self.screen = screen
        self.background = background
        self.seen = False
        self.state_machine = state_machine

        self.BG_COLOR = bg_color
        self.FONT_FILE = font_file
        self.FONT_COLOR = font_color
        self.BUTTON_COLOR = button_color
        self.PADDING = padding

        self.title_y_pos = self.screen.get_rect().centery
        self.title = assets.Title('Asteroids',
                                  self.FONT_FILE, 52,
                                  self.FONT_COLOR,
                                  (self.screen.get_rect().centerx,
                                   self.title_y_pos))

        self.buttons_panel = assets.Buttons(self.FONT_FILE, 28,
                                            self.FONT_COLOR,
                                            self.BUTTON_COLOR,
                                            screen.get_rect().centerx, 0,
                                            self.PADDING,
                                            'New Game',
                                            'Controls',
                                            'Options',
                                            'Quit')

        self.buttons_y_pos = (self.screen.get_height()
                              - (self.PADDING * 4)
                              - self.buttons_panel.height)

        self.buttons_panel.y_pos = self.buttons_y_pos
        self.buttons_panel.reposition()
        self.all_assets = [self.title, self.buttons_panel]

    def _first_render(self):
        self.background.fill(self.BG_COLOR)
        self.screen.blit(self.background, (0, 0))
        pygame.display.update()
        self.seen = True

    def get_input(self):
        input_dict = {'next_state': GameStates.INTRO}
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                input_dict['next_state'] = None
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    input_dict['next_state'] = None
                    break
                if event.key == pygame.K_RETURN:
                    input_dict['next_state'] = GameStates.MAIN
                    break
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for button in self.buttons_panel.buttons:
                    if button['button_rect'].collidepoint(mouse_pos):
                        if button['label'] == 'New Game':
                            input_dict['next_state'] = GameStates.MAIN
                            break
                        elif button['label'] == 'Options':
                            input_dict['next_state'] = GameStates.OPTIONS
                            break
                        elif button['label'] == 'Quit':
                            input_dict['next_state'] = None
                            break
        return input_dict

    def update(self, input_dict, *args, **kwargs):
        if not self.seen:
            self._first_render()
        if input_dict['next_state']:
            if input_dict['next_state'] != GameStates.INTRO:
                self.seen = False
            return input_dict['next_state']
        else:
            return None

    def render(self, *args, **kwargs):
        dirty_rects = utility.draw_all(self.all_assets, self.screen,
                                       self.background)
        pygame.display.update(dirty_rects)


class Options():
    def get_input(self):
        return {'next_state': GameStates.INTRO}

    def update(self, *args, **kwargs):
        pass

    def render(self, *args, **kwargs):
        pass


class Main():
    def __init__(self, font_file, font_color, button_color, padding,
                 screen, background, bg_color, state_machine, channels):
        # general
        self.FONT_FILE = font_file
        self.FONT_COLOR = font_color
        self.BUTTON_COLOR = button_color
        self.PADDING = padding
        self.BG_COLOR = bg_color
        self.LEVEL_TRANSITION_TIME = 1000
        self.BASE_SCORE = 150
        self.SCOREBOARD_POS = (15, 10)
        self.SCOREBOARD_FONT_SIZE = 24
        self.STARTING_LIVES = 3

        self.screen = screen
        self.background = background
        self.all_assets = []
        self.seen = False
        self.state_machine = state_machine
        self.channels = channels

        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        player_config = self.config['PLAYER']
        enemy_config = self.config['ENEMY']
        asteroid_config = self.config['ASTEROID']

        # player
        self.player_remains_alive = True

        self.PLAYER_POS = screen.get_rect().center
        self.PLAYER_DIR = (0, -1)
        self.PLAYER_FOLDER_NAME = 'player'
        self.EXTRA_LIFE_TARGET = 10000
        self.PLAYER_THRUST = int(player_config['thrust'])
        self.PLAYER_MASS = int(player_config['mass'])
        self.PLAYER_TURN_SPEED = int(player_config['turn_speed'])
        self.LEVEL_FRICTION = float(player_config['level_friction'])
        self.PLAYER_FIRE_RATE = int(player_config['fire_rate_per_s'])
        self.PLAYER_SHOT_POWER = int(player_config['shot_power'])
        self.PLAYER_ANIMATION_SPEED = int(player_config['animation_speed'])
        self.PLAYER_HYPERSPACE_LENGTH = float(
            player_config['hyperspace_length_s'])
        self.PLAYER_RESPAWN_FLASH_SPEED = int(
            player_config['respawn_flash_speed'])
        self.LEVEL_TRANSITION_FLASH_SPEED = int(
            player_config['level_transition_flash_speed'])
        self.PLAYER_RESPAWN_TIME = int(player_config['respawn_time_ms'])
        self.PLAYER_BULLET_LIFESPAN = float(player_config['bullet_lifespan'])

        # dead player
        self.DEAD_PLAYER_FOLDER_NAME = 'dead_player'
        self.DEAD_PLAYER_ANIMATION_SPEED = 24
        self.PLAYER_DEATH_TIMER = 1000  # in miliseconds

        # enemy
        self.ENEMY_MIN_SPEED = int(enemy_config['min_speed'])
        self.ENEMY_MAX_SPEED = int(enemy_config['max_speed'])
        self.ENEMY_MIN_ANGLE = float(enemy_config['min_angle'])
        self.MIN_ENEMY_DISTANCE = int(enemy_config['min_distance'])
        self.ENEMY_SHOT_POWER = int(enemy_config['shot_power'])
        self.ENEMY_FIRE_RATE = float(enemy_config['fire_rate_per_s'])
        self.ENEMY_BULLET_LIFESPAN = float(enemy_config['bullet_lifespan_s'])
        self.TIME_BETWEEN_ENEMY_SPAWNS = int(
            enemy_config['time_between_spawns_ms'])
        self.ENEMY_OVERLAP_OFFSET = int(
            enemy_config['spawn_overlap_offset_ms'])
        self.ENEMY_MAX_INNACURACY_ANGLE = int(
            enemy_config['max_innacuracy_angle'])
        self.ENEMY_MAX_DIFFICULTY_AT_SCORE = int(
            enemy_config['max_difficulty_score'])

        # asteroid
        self.LEVEL_ASTEROIDS_OFFSET = int(
            asteroid_config['spawn_level_offset'])
        self.MIN_ASTEROID_SPEED = int(asteroid_config['min_speed'])
        self.MAX_ASTEROID_SPEED = int(asteroid_config['max_speed'])
        self.MIN_ASTEROID_DIR_ANGLE = float(asteroid_config['min_dir_angle'])
        self.MIN_ASTEROID_DIST = int(asteroid_config['min_distance'])
        self.NEW_ASTEROID_VELOCITY_SCALE = float(
            asteroid_config['new_asteroid_velocity_scale'])
        self.MIN_BROKEN_ASTEROIDS = int(
            asteroid_config['min_broken_asteroids'])
        self.MAX_BROKEN_ASTEROIDS = int(
            asteroid_config['max_broken_asteroids'])
        self.MAX_NEW_ASTEROIDS = int(asteroid_config['max_new_asteroids'])

    def _first_render(self):
        self.score = 0
        self.extra_life_tracker = 0
        self.player_out_of_lives = False
        self.level = 1
        self.player_alive = True
        self.asteroids_spawned = False
        self.player_hit_time = 0
        self.previous_enemy_spawn = 0
        self.enemy_spawned = False

        # initialise sprite groups, player and scoreboard
        self.players = pygame.sprite.RenderUpdates()
        self.enemies = pygame.sprite.RenderUpdates()
        self.asteroids = pygame.sprite.RenderUpdates()
        self.shots = pygame.sprite.RenderUpdates()
        self.enemy_shots = pygame.sprite.RenderUpdates()


        self.player = assets.Player(self.PLAYER_POS, self.PLAYER_DIR,
                                    self.PLAYER_THRUST, self.PLAYER_MASS,
                                    self.PLAYER_TURN_SPEED,
                                    self.LEVEL_FRICTION,
                                    1000 / self.PLAYER_FIRE_RATE,
                                    self.PLAYER_SHOT_POWER,
                                    self.PLAYER_ANIMATION_SPEED,
                                    self.PLAYER_FOLDER_NAME,
                                    self.player_remains_alive,
                                    self.PLAYER_HYPERSPACE_LENGTH,
                                    self.BG_COLOR, self.STARTING_LIVES,
                                    self.PLAYER_RESPAWN_FLASH_SPEED,
                                    self.PLAYER_RESPAWN_TIME / 1000,
                                    self.PLAYER_BULLET_LIFESPAN,
                                    self.channels['thrust_player'],
                                    self.channels['hyperspace_player'],
                                    self.channels['shoot_player'])
        self.players.add(self.player)

        self.scoreboard = assets.Scoreboard(self.FONT_FILE,
                                            self.SCOREBOARD_FONT_SIZE,
                                            self.FONT_COLOR,
                                            self.BG_COLOR,
                                            self.SCOREBOARD_POS,
                                            self.level, self.score,
                                            self.player.lives)
        self.scoreboard.hide()

        self.all_assets.extend([self.players, self.enemies, self.asteroids,
                                self.shots, self.enemy_shots, self.scoreboard])

        self.background.fill(self.BG_COLOR)
        self.screen.blit(self.background, (0, 0))
        pygame.display.update()
        self.level_start_time = (pygame.time.get_ticks()
                                 + self.LEVEL_TRANSITION_TIME)
        self.previous_enemy_spawn = self.level_start_time
        self.player_has_control = True
        self.player_is_vulnerable = True
        self.seen = True

    def _prepare_next_state(self):
        self.seen = False
        self.all_assets.clear()

    def _handle_input(self, input_dict, player_has_control, current_time):
        if player_has_control:
            if input_dict['player_engine_on']:
                self.player.engine_on()
            if input_dict['player_engine_off']:
                self.player.engine_off()
            if input_dict['player_turn'] is not None:
                self.player.turn(input_dict['player_turn'])
            if input_dict['player_hyperspace']:
                self.player.hyperspace(len(self.asteroids))
            if input_dict['player_fire']:
                shot = self.player.gun.fire(current_time)
                if shot is not None:
                    self.shots.add(shot)

    def _check_player_collisions(self):
        colliding_asteroids = pygame.sprite.groupcollide(
            self.players, self.asteroids, False, False,
            pygame.sprite.collide_mask)

        colliding_enemy_shots = pygame.sprite.groupcollide(
            self.players, self.enemy_shots, False, True,
            pygame.sprite.collide_mask)

        colliding_spaceships = pygame.sprite.groupcollide(
            self.players, self.enemies, False, False,
            pygame.sprite.collide_mask)

        return {**colliding_asteroids,
                **colliding_enemy_shots,
                **colliding_spaceships}

    def _kill_player(self, current_time):
        self.dead_player = assets.DeadPlayer(self.DEAD_PLAYER_FOLDER_NAME,
                                             self.DEAD_PLAYER_ANIMATION_SPEED,
                                             self.player.rect.center,
                                             self.player.facing_direction,
                                             self.player.velocity,
                                             self.player.velocity_direction,
                                             self.LEVEL_FRICTION,
                                             self.player.mass,
                                             self.channels['explosion_player'])
        self.players.remove(self.player)
        self.player.lives -= 1
        self.player.alive = False
        self.player.thrust_channel.stop()
        self.player_hit_time = current_time
        self.players.add(self.dead_player)
        if self.player.lives < 1:
            return True
        else:
            return False

    def _respawn_player(self):
        self.players.remove(self.dead_player)
        self.player.respawn(self.PLAYER_RESPAWN_TIME / 1000,
                            self.PLAYER_RESPAWN_FLASH_SPEED,
                            self.screen.get_rect().center)
        self.players.add(self.player)

    def _shoot_enemies(self, current_time):
        enemies_shot_by_player = pygame.sprite.groupcollide(
            self.enemies, self.shots, True, True,
            pygame.sprite.collide_mask)

        for enemy, shot_list in enemies_shot_by_player.items():
            score_gain = int(self.BASE_SCORE * enemy.state.value)
            self.score += score_gain
            self.extra_life_tracker += score_gain
            enemy.explosion_channel.play(enemy.explosion_sound)
            enemy.kill()
            self.enemy_spawned = False
            self.previous_enemy_spawn = current_time - self.ENEMY_OVERLAP_OFFSET

    def _spawn_enemy(self, current_time):
        new_enemy_state_gen = random.random()
        new_enemy_state_weight = utility.normalize(self.score, 0, 40000)
        if new_enemy_state_weight >= new_enemy_state_gen:
            new_enemy_state = assets.EnemyStates.SMALL
        else:
            new_enemy_state = assets.EnemyStates.BIG

        self.enemies.add(assets.Enemy.spawn(
            self.ENEMY_MIN_SPEED, self.ENEMY_MAX_SPEED,
            self.ENEMY_MIN_ANGLE, self.player.rect, self.ENEMY_SHOT_POWER,
            self.screen.get_rect().width, self.screen.get_rect().height,
            1000 / self.ENEMY_FIRE_RATE, self.ENEMY_SHOT_POWER,
            self.ENEMY_BULLET_LIFESPAN, new_enemy_state,
            self.ENEMY_MAX_INNACURACY_ANGLE,
            self.ENEMY_MAX_DIFFICULTY_AT_SCORE,
            self.channels['shoot_enemy'],
            self.channels['explosion_enemy']))
        self.previous_enemy_spawn = current_time
        self.enemy_spawned = True

    def _check_asteroid_collisions(self):
        asteroids_shot_by_player = pygame.sprite.groupcollide(
            self.asteroids, self.shots, True, True,
            pygame.sprite.collide_mask)

        asteroids_shot_by_enemies = pygame.sprite.groupcollide(
            self.asteroids, self.enemy_shots, True, True,
            pygame.sprite.collide_mask)

        shot_asteroids = {**asteroids_shot_by_player,
                          **asteroids_shot_by_enemies}

        for asteroid, shot_list in shot_asteroids.items():
            for shot in shot_list:
                if isinstance(shot.owner, assets.Player):
                    score_gain = int(self.BASE_SCORE / asteroid.state)
                    self.score += score_gain
                    self.extra_life_tracker += score_gain
                    break

            number_to_spawn = random.randint(self.MIN_BROKEN_ASTEROIDS,
                                             self.MAX_BROKEN_ASTEROIDS)
            new_asteroids = asteroid.hit(
                self.NEW_ASTEROID_VELOCITY_SCALE, number_to_spawn)
            if new_asteroids is not None:
                self.asteroids.add(new_asteroids)

    def _add_extra_life(self):
        if self.extra_life_tracker >= self.EXTRA_LIFE_TARGET:
            self.player.lives += 1
            self.extra_life_tracker = self.extra_life_tracker % self.EXTRA_LIFE_TARGET

    def _start_level_transition(self, current_time):
        self.level += 1
        self.shots.clear(self.screen, self.background)
        self.shots.empty()
        self.level_start_time = (current_time
                                 + self.LEVEL_TRANSITION_TIME)
        self.previous_enemy_spawn = self.level_start_time
        self.player.respawn(self.LEVEL_TRANSITION_TIME / 1000,
                            self.LEVEL_TRANSITION_FLASH_SPEED,
                            self.screen.get_rect().center,
                            reset=False)
        self.asteroids_spawned = False

    def _start_next_level(self):
        self.scoreboard.show()
        asteroid_number = min(
            self.MAX_NEW_ASTEROIDS, self.level + self.LEVEL_ASTEROIDS_OFFSET)
        ast_list = assets.Asteroid.spawn(asteroid_number,
                                         self.MIN_ASTEROID_SPEED,
                                         self.MAX_ASTEROID_SPEED,
                                         self.MIN_ASTEROID_DIR_ANGLE,
                                         self.player.rect,
                                         self.MIN_ASTEROID_DIST,
                                         self.screen.get_width(),
                                         self.screen.get_height(),
                                         self.channels['explosion_asteroid'])
        self.asteroids.add(ast_list)
        self.asteroids_spawned = True

    def _enemy_fire(self, current_time):
        for enemy in self.enemies.sprites():
            if enemy.primed:
                enemy_shot = enemy.gun.fire(current_time)
                if enemy_shot is not None:
                    self.enemy_shots.add(enemy_shot)

    def get_input(self):
        input_dict = {'next_state': GameStates.MAIN,
                      'player_hyperspace': False,
                      'player_fire': False,
                      'player_engine_on': False,
                      'player_engine_off': False,
                      'player_turn': None}

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                input_dict['next_state'] = None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    input_dict['next_state'] = GameStates.INTRO
                if event.key == pygame.K_LSHIFT:
                    input_dict['player_hyperspace'] = True
                if event.key == pygame.K_SPACE:
                    input_dict['player_fire'] = True
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_UP:
                    input_dict['player_engine_off'] = True

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            input_dict['player_engine_on'] = True
        if keys[pygame.K_LEFT]:
            input_dict['player_turn'] = 1
        if keys[pygame.K_RIGHT]:
            input_dict['player_turn'] = -1

        return input_dict

    def update(self, input_dict, delta_time, *args, **kwargs):
        if not self.seen:
            self._first_render()
        current_time = pygame.time.get_ticks()

        self._handle_input(input_dict, self.player_has_control, current_time)

        self.player_has_control = (self.player.alive
                                   and not self.player.in_hyperspace)
        self.player_is_vulnerable = (self.player_has_control
                                     and not self.player.respawning)

        if self.player_is_vulnerable:
            colliding_things = self._check_player_collisions()
            if len(colliding_things) > 0 or not self.player.remains_alive:
                self.player_out_of_lives = self._kill_player(current_time)

        if self.player_out_of_lives:
            input_dict['next_state'] = GameStates.END
            self.state_machine.states_dict[GameStates.END].setup(
                50, self.score, self.player.lives, self.level, self.all_assets)
        if (not self.player.alive
            and not self.player_out_of_lives
            and (current_time - self.player_hit_time
                 >= self.PLAYER_DEATH_TIMER)):
            self._respawn_player()

        self._shoot_enemies(current_time)

        if (not self.enemy_spawned
            and (current_time - self.previous_enemy_spawn
                 >= self.TIME_BETWEEN_ENEMY_SPAWNS)):
            self._spawn_enemy(current_time)

        self._check_asteroid_collisions()

        self._add_extra_life()

        if len(self.asteroids) == 0 and len(self.enemies) == 0:
            if self.asteroids_spawned:
                self._start_level_transition(current_time)
            if current_time - self.level_start_time >= 0:
                self._start_next_level()

        self._enemy_fire(current_time)

        if input_dict['next_state']:
            if input_dict['next_state'] != GameStates.MAIN:
                self._prepare_next_state()
            return input_dict['next_state']
        else:
            return None

    def render(self, delta_time, *args, **kwargs):
        dirty_rects = utility.draw_all(self.all_assets, self.screen,
                                       self.background, delta_time,
                                       self.score, self.level,
                                       self.player.lives,
                                       player_rect=self.player.rect)
        pygame.display.update(dirty_rects)


class End():
    def __init__(self, font_file, font_color, button_color, padding,
                 screen, background, bg_color, state_machine):
        self.FONT_FILE = font_file
        self.FONT_COLOR = font_color
        self.BUTTON_COLOR = button_color
        self.PADDING = padding
        self.BG_COLOR = bg_color

        self.screen = screen
        self.background = background
        self.state_machine = state_machine

    def setup(self, text_pos, score, lives, level, asset_list):
        self.heading_y_pos = text_pos
        self.score = score
        self.lives = lives
        self.level = level
        self.scoreboard_dirty_rects = None
        self.dirty_rects = []
        self.all_assets = []

        self.heading = assets.Title('Game Over', self.FONT_FILE, 42,
                                    self.FONT_COLOR,
                                    (self.screen.get_rect().centerx,
                                     self.heading_y_pos))

        self.score_heading_y_pos = (self.heading_y_pos
                                    + self.heading.height
                                    + self.PADDING)

        self.score_heading = assets.Title(
            ('Score: ' + str(utility.thousands(self.score))),
            self.FONT_FILE, 36, self.FONT_COLOR,
            (self.screen.get_rect().centerx,
             self.score_heading_y_pos))

        self.highscores_y_pos = (self.score_heading_y_pos
                                 + self.score_heading.height
                                 + self.PADDING)

        self.highscores = assets.Highscores(self.score, self.FONT_FILE, 36,
                                            self.FONT_COLOR,
                                            self.screen.get_rect().centerx,
                                            self.highscores_y_pos,
                                            self.PADDING, self.BUTTON_COLOR)

        self.buttons_panel = assets.Buttons(self.FONT_FILE, 28,
                                            self.FONT_COLOR,
                                            self.BUTTON_COLOR,
                                            self.screen.get_rect().centerx,
                                            0, self.PADDING, 'New Game',
                                            'Main Menu', 'Quit')

        self.buttons_y_pos = (self.screen.get_height()
                              - (self.PADDING * 4) - self.buttons_panel.height)

        self.buttons_panel.y_pos = self.buttons_y_pos
        self.buttons_panel.reposition()

        self.TIME_TO_START = 1000
        self.all_assets.extend(asset_list)
        self.menu_showing = False
        self.start_time = pygame.time.get_ticks()

    def get_input(self):
        input_dict = {'next_state': GameStates.END}
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                input_dict['next_state'] = None
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    input_dict['next_state'] = None
                    break
                if event.key == pygame.K_RETURN:
                    input_dict['next_state'] = GameStates.MAIN
                    break
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for button in self.buttons_panel.buttons:
                    if button['button_rect'].collidepoint(mouse_pos):
                        if button['label'] == 'New Game':
                            input_dict['next_state'] = GameStates.MAIN
                            break
                        elif button['label'] == 'Main Menu':
                            input_dict['next_state'] = GameStates.INTRO
                            break
                        elif button['label'] == 'Quit':
                            input_dict['next_state'] = None
        return input_dict

    def update(self, input_dict, delta_time, *args, **kwargs):
        current_time = pygame.time.get_ticks()

        if (not self.menu_showing and
            current_time - self.start_time >= self.TIME_TO_START):
            self.menu_showing = True
            scoreboard = self.all_assets.pop()
            self.scoreboard_dirty_rects = scoreboard.clear(self.screen,
                                                           self.background)
            self.all_assets.extend([self.heading, self.score_heading,
                                    self.highscores, self.buttons_panel])

        return input_dict['next_state']

    def render(self, delta_time, *args, **kwargs):
        dirty_rects = utility.draw_all(self.all_assets, self.screen,
                                       self.background, delta_time,
                                       self.score, self.level,
                                       self.lives)
        if self.scoreboard_dirty_rects:
            dirty_rects.extend(self.scoreboard_dirty_rects)
            self.scoreboard_dirty_rects = None
        pygame.display.update(dirty_rects)
