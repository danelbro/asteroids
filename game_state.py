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
    CONTROLS = enum.auto()
    OPTIONS = enum.auto()
    MAIN = enum.auto()
    END = enum.auto()


class MusicHandler():
    def __init__(self, low_channel, high_channel, volume, initial_time, rate):
        self.low_sound = utility.load_sound('heart_low.wav')
        self.high_sound = utility.load_sound('heart_high.wav')
        self.low_channel = low_channel
        self.high_channel = high_channel
        self.low_channel.set_volume(volume)
        self.high_channel.set_volume(volume)
        self.initial_time = initial_time
        self.rate = rate
        self.fastest_time = self._determine_fastest_time()
        self.last_played_time = 0
        self.last_played_sound = self.low_sound
        self.reset()

    def _determine_fastest_time(self):
        first_length = self.low_sound.get_length()
        second_length = self.high_sound.get_length()
        return max(first_length, second_length) + 200

    def _determine_sound(self):
        if self.last_played_sound == self.low_sound:
            return self.high_sound, self.high_channel
        return self.low_sound, self.low_channel

    def reset(self):
        self.time = self.initial_time
        self.count = 1000 / self.time

    def play(self, current_time):
        if current_time < self.last_played_time + self.time:
            return
        self.last_played_time = current_time
        next_sound, next_channel = self._determine_sound()
        next_channel.play(next_sound)
        self.last_played_sound = next_sound
        self.time = max(self.fastest_time, 1 / (self.count / 1000))
        self.count += self.rate / 1000


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
                            GameStates.CONTROLS: Controls(self.font_file,
                                                          self.font_color,
                                                          self.button_color,
                                                          self.padding,
                                                          self.screen,
                                                          self.background,
                                                          self.bg_color,
                                                          self),
                            GameStates.OPTIONS: Options(self.font_file,
                                                        self.font_color,
                                                        self.button_color,
                                                        self.padding,
                                                        self.screen,
                                                        self.background,
                                                        self.bg_color,
                                                        self),
                            GameStates.MAIN:Main(self.font_file,
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
        self.BUTTONS_DICT = {'New Game': GameStates.MAIN,
                             'Controls': GameStates.CONTROLS,
                             'Options': GameStates.OPTIONS,
                             'Quit': None}
        self.BUTTON_LABELS = list(self.BUTTONS_DICT.keys())

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
                                            *self.BUTTON_LABELS)

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
                        next_state = self.BUTTONS_DICT[button['label']]
                        input_dict['next_state'] = next_state
                        break
        return input_dict

    def update(self, input_dict, *args, **kwargs):
        if not self.seen:
            self._first_render()
        if input_dict['next_state']:
            if input_dict['next_state'] != GameStates.INTRO:
                self.seen = False
        return input_dict['next_state']

    def render(self, *args, **kwargs):
        dirty_rects = utility.draw_all(self.all_assets, self.screen,
                                       self.background)
        pygame.display.update(dirty_rects)


class Controls():
    def __init__(self, font_file, font_color, button_color, padding,
                 screen, background, bg_color, state_machine):
        self.screen = screen
        self.background = background
        self.BG_COLOR = bg_color
        self.state_machine = state_machine

        self.heading_y_pos = 50
        self.heading = assets.Title('Controls', font_file, 40, font_color,
                                    (self.screen.get_rect().centerx,
                                     self.heading_y_pos))

        expl_x_offset = int(self.screen.get_rect().centerx / 2)
        expl_y_offset = int(self.screen.get_rect().centery / 8)
        first_row_y = int(self.screen.get_rect().centery - expl_y_offset)
        second_row_y = int(self.screen.get_rect().centery + expl_y_offset)
        self.thrust_expl = assets.Title('Thrust: Up Arrow',
                                        font_file, 30, font_color,
                                        (expl_x_offset, first_row_y))

        self.turn_expl = assets.Title('Turn: L/R Arrow',
                                      font_file, 30, font_color,
                                      (self.screen.get_rect().centerx
                                       + expl_x_offset, first_row_y))

        self.fire_expl = assets.Title('Fire: Space',
                                      font_file, 30, font_color,
                                      (expl_x_offset, second_row_y))

        self.hyperspace_expl = assets.Title('Hyperspace: Left Shift',
                                            font_file, 30, font_color,
                                            (self.screen.get_rect().centerx
                                             + expl_x_offset, second_row_y))
        self.buttons_dict = {'Back': GameStates.INTRO}
        self.button_labels = list(self.buttons_dict.keys())
        self.buttons_panel = assets.Buttons(font_file, 28, font_color,
                                            button_color,
                                            self.screen.get_rect().centerx,
                                            650, padding, *self.button_labels)

        self.all_assets = [self.heading, self.thrust_expl, self.turn_expl,
                           self.fire_expl, self.hyperspace_expl,
                           self.buttons_panel]
        self.seen = False

    def _first_render(self):
        self.background.fill(self.BG_COLOR)
        self.screen.blit(self.background, (0, 0))
        pygame.display.update()
        self.seen = True

    def get_input(self):
        input_dict = {'next_state': GameStates.CONTROLS}
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                input_dict['next_state'] = None
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    input_dict['next_state'] = GameStates.INTRO
                    break
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                for button in self.buttons_panel.buttons:
                    if button['button_rect'].collidepoint(mouse_pos):
                        input_dict['next_state'] = self.buttons_dict[button['label']]
                        break

        return input_dict

    def update(self, input_dict, *args, **kwargs):
        if not self.seen:
            self._first_render()
        if input_dict['next_state']:
            if input_dict['next_state'] != GameStates.CONTROLS:
                self.seen = False
        return input_dict['next_state']

    def render(self, *args, **kwargs):
        dirty_rects = utility.draw_all(self.all_assets, self.screen,
                                       self.background)
        pygame.display.update(dirty_rects)


class Options():
    def __init__(self, font_file, font_color, button_color, padding,
                 screen, background, bg_color, state_machine):
        self.font_file = font_file
        self.font_color = font_color
        self.button_color = button_color
        self.padding = padding
        self.screen = screen
        self.background = background
        self.bg_color = bg_color
        self.config = configparser.ConfigParser()
        self.seen = False
        self.button_speed = 100

        self.heading = assets.Title('Options', self.font_file,
                                    24, self.font_color,
                                    (self.screen.get_rect().centerx,
                                     self.padding * 5))
        self.column_size = self.screen.get_rect().width / 6
        self.subtitle_height = 55
        self.player_title = assets.Title('Player', self.font_file, 20,
                                         self.font_color,
                                         (self.column_size,
                                          self.subtitle_height))
        self.enemy_title = assets.Title('Enemies', self.font_file, 20,
                                        self.font_color,
                                        (self.column_size * 2.25,
                                         self.subtitle_height))
        self.asteroid_title = assets.Title('Asteroids', self.font_file, 20,
                                           self.font_color,
                                           (self.column_size * 3.5,
                                            self.subtitle_height))
        self.music_title = assets.Title('Music', self.font_file, 20,
                                        self.font_color,
                                        (self.column_size * 4.75,
                                        self.subtitle_height))

        self.buttons_dict = {'Save': GameStates.INTRO,
                             'Back': GameStates.INTRO}
        self.button_labels = list(self.buttons_dict.keys())
        self.buttons_panel = assets.Buttons(self.font_file, 30,
                                            self.font_color,
                                            self.button_color,
                                            self.column_size * 4.75, 0,
                                            self.padding,
                                            *self.button_labels)
        buttons_y_pos = (self.screen.get_rect().height
                         - self.buttons_panel.height
                         - self.padding)
        self.buttons_panel.y_pos = buttons_y_pos
        self.buttons_panel.reposition()
        self.config_buttons = pygame.sprite.RenderUpdates()
        
    def _first_render(self):
        self.config_buttons.empty()
        self.all_assets = []
        self.last_pressed = 0
        button_offset = 35

        self.config.read('config.ini')

        self.config_titles = []
        self.config_text_strings = []
        for j, section in enumerate(self.config.sections()):
            for i, option in enumerate(self.config[section]):
                title_text_string = ' '.join(option.capitalize().split('_'))
                option_title = assets.Title(
                    title_text_string, self.font_file, 16, self.font_color,
                    ((self.column_size
                      * ((1.25 * j) + 1)),
                     (self.subtitle_height
                      + ((self.padding * 5)
                         + (self.padding * 5 * i) * 2))))

                option_text_string = self.config[section][option]
                option_text = assets.Title(
                    option_text_string, self.font_file, 16, self.font_color,
                    ((self.column_size
                      * ((1.25 * j) + 1)),
                     (self.subtitle_height
                      + (((self.padding * 5) * 2)
                        + (self.padding * 5 * i) * 2))))

                left_button = assets.OptionsButton(
                    'down', (option_text.text_rect.centerx - button_offset,
                             (self.subtitle_height
                              + (((self.padding * 5) * 2)
                                 + (self.padding * 5 * i) * 2))),
                    self.config, section, option)

                right_button = assets.OptionsButton(
                    'up', (option_text.text_rect.centerx + button_offset,
                           (self.subtitle_height
                            + (((self.padding * 5) * 2)
                               + (self.padding * 5 * i) * 2))),
                    self.config, section, option)

                self.config_titles.append(option_title)
                self.config_text_strings.append(option_text)
                self.config_buttons.add(left_button, right_button)

        self.all_assets.extend([self.heading, self.player_title,
                                self.enemy_title, self.asteroid_title,
                                self.music_title, self.buttons_panel,
                                *self.config_titles,
                                *self.config_text_strings,
                                self.config_buttons])

        self.background.fill(self.bg_color)
        self.screen.blit(self.background, (0, 0))
        pygame.display.update()
        self.seen = True

    def _update_options(self):
        last_section_length = 0
        for section in self.config.sections():
            for i, option in enumerate(self.config[section]):
                new_option_text = self.config[section][option]
                self.config_text_strings[i + last_section_length].update_text(
                    new_option_text)
            last_section_length += len(self.config[section])  

    def _change_option(self, pressed_button):
        pressed_button.update_option()

    def _save_options(self):
        with open('config.ini', 'w') as configfile:
            self.config.write(configfile)

    def get_input(self):
        input_dict = {'next_state': GameStates.OPTIONS,
                      'save': False,
                      'change_option': None}

        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                input_dict['next_state'] = None
                break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                   input_dict['next_state'] = GameStates.INTRO
                   break
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    for button in self.buttons_panel.buttons:
                        if button['button_rect'].collidepoint(mouse_pos):
                            input_dict['next_state'] = self.buttons_dict[button['label']]
                            if button['label'] == 'Save':
                                input_dict['save'] = True

        mouse_buttons = pygame.mouse.get_pressed()
        if mouse_buttons[0]:
            for button in self.config_buttons:
                if button.rect.collidepoint(mouse_pos):
                    input_dict['change_option'] = button

        return input_dict

    def update(self, input_dict, delta_time, *args, **kwargs):
        current_time = pygame.time.get_ticks()
        if not self.seen:
            self._first_render()
            
        self._update_options()

        if (input_dict['change_option'] is not None
            and current_time - self.last_pressed >= self.button_speed):
            self._change_option(input_dict['change_option'])
            self.last_pressed = current_time
 
        if input_dict['save']:
            self._save_options()

        if input_dict['next_state']:
            if input_dict['next_state'] != GameStates.OPTIONS:
                self.seen = False
                self.all_assets.clear()
        return input_dict['next_state']

    def render(self, *args, **kwargs):
        self.screen.blit(self.background, (0, 0))
        utility.draw_all(self.all_assets, self.screen, self.background)
        pygame.display.update()


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
        music_config = self.config['MUSIC']

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
        self.PLAYER_FIRE_RATE = int(player_config['fire_rate'])
        self.PLAYER_SHOT_POWER = int(player_config['shot_power'])
        self.PLAYER_ANIMATION_SPEED = int(player_config['animation_speed'])
        self.PLAYER_HYPERSPACE_LENGTH = float(
            player_config['hyperspace_length'])
        self.PLAYER_RESPAWN_FLASH_SPEED = int(
            player_config['respawn_flash_speed'])
        self.LEVEL_TRANSITION_FLASH_SPEED = int(
            player_config['level_transition_flash_speed'])
        self.PLAYER_RESPAWN_TIME = int(player_config['respawn_time'])
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
        self.ENEMY_FIRE_RATE = float(enemy_config['fire_rate'])
        self.ENEMY_BULLET_LIFESPAN = float(enemy_config['bullet_lifespan'])
        self.TIME_BETWEEN_ENEMY_SPAWNS = int(
            enemy_config['time_between_spawns'])
        self.ENEMY_OVERLAP_OFFSET = int(
            enemy_config['spawn_overlap_offset'])
        self.ENEMY_MAX_INNACURACY_ANGLE = int(
            enemy_config['max_innacuracy_angle'])
        self.ENEMY_MIN_INNACURACY_ANGLE = int(
            enemy_config['min_innacuracy_angle'])
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

        # music
        self.MUSIC_VOLUME = float(music_config['volume'])
        self.MUSIC_GAP = int(music_config['gap'])
        self.MUSIC_RATE = int(music_config['rate'])
        self.music_handler = MusicHandler(self.channels['heart_low'],
                                          self.channels['heart_high'],
                                          self.MUSIC_VOLUME,
                                          self.MUSIC_GAP,
                                          self.MUSIC_RATE)
        self.enemy_attack_channel = self.channels['attack_enemy']
        self.enemy_attack_sound = utility.load_sound('attack_enemy.wav')

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
        self._level_started = False
        self.player_has_control = True
        self.player_is_vulnerable = True
        self.seen = True

    def _prepare_next_state(self):
        self.seen = False
        for channel in self.channels.values():
            channel.stop()
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
        self.player.engine_off()
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

        if not self.enemy_spawned:
            self.enemy_attack_channel.stop()

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
            self.ENEMY_MIN_INNACURACY_ANGLE,
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
        self._level_started = False

    def _start_next_level(self):
        self.scoreboard.show()
        self.music_handler.reset()
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
        self._level_started = True

    def _enemy_fire(self, current_time):
        for enemy in self.enemies.sprites():
            if enemy.primed:
                enemy_shot = enemy.gun.fire(current_time)
                if enemy_shot is not None:
                    self.enemy_shots.add(enemy_shot)

    def _check_player_control(self):
        self.player_has_control = (self.player.alive
                                   and not self.player.in_hyperspace)

    def _check_player_vulnerability(self):
        self._check_player_control()
        self.player_is_vulnerable = (self.player_has_control
                                     and not self.player.respawning)

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

        if self._level_started:
            self.music_handler.play(current_time)

        if self.enemy_spawned and not self.enemy_attack_channel.get_busy():
            self.enemy_attack_channel.play(self.enemy_attack_sound)

        self._check_player_control()
        self._handle_input(input_dict, self.player_has_control, current_time)

        self._check_player_vulnerability()
        if self.player_is_vulnerable:
            colliding_things = self._check_player_collisions()
            if len(colliding_things) > 0 or not self.player.remains_alive:
                self.player_out_of_lives = self._kill_player(current_time)

        if self.player_out_of_lives:
            input_dict['next_state'] = GameStates.END
            self.state_machine.states_dict[GameStates.END].setup(
                self.score, self.player.lives, self.level, self.all_assets)

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
        self.TEXT_POS = 50
        self.BUTTONS_DICT = {'New Game': GameStates.MAIN,
                             'Main Menu': GameStates.INTRO,
                             'Quit': None}
        self.BUTTON_LABELS = list(self.BUTTONS_DICT.keys())

        self.screen = screen
        self.background = background
        self.state_machine = state_machine

    def setup(self, score, lives, level, asset_list):
        self.heading_y_pos = self.TEXT_POS
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
                                            0, self.PADDING,
                                            *self.BUTTON_LABELS)

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
                        input_dict['next_state'] = self.BUTTONS_DICT[button['label']]
                        break
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
