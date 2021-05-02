import os
import math
import random
import pygame

def load_image(name, folder_name, colorkey=None):
    """Utility function to load images.

    Args:
        name (str): name of the image to be loaded
        folder_name (str): name of the folder where the image is saved
        colorkey (int, tuple, optional): Set to -1 to get colorkey from
        top left of image. Otherwise set to a tuple representing the color
        to be keyed. Defaults to None, use if you don't need a colorkey.

    Raises:
        SystemExit: if the image cannot be loaded

    Returns:
        pygame.Surface: a pygame Surface object representing the image
    """
    fullname = os.path.join(folder_name, name)
    try:
        image = pygame.image.load(fullname).convert()
    except pygame.error as message:
        print('Cannot load image: ', name)
        raise SystemExit(message)
    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, pygame.RLEACCEL)
    return image


def load_sound(name):
    """Utility function to load sounds

    Args:
        name (str): name of the sound file to be loaded

    Raises:
        SystemExit: if the sound cannot be loaded

    Returns:
        pygame.mixer.Sound: pygame Sound object representing the sound
    """
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


def draw_all(sprites, screen, background, *args, **kwargs):
    for sprite_group in sprites:
            sprite_group.clear(screen, background)
            sprite_group.update(*args, **kwargs)
    return [dirty_rect for sprite_group in sprites
                       for dirty_rect in sprite_group.draw(screen)]

def thousands(n):
    return "{:,}".format(n)

def normalize(x, x_min, x_max):
            return (x - x_min) / (x_max - x_min)

def lerp(min, max, t):
            return (1 - t) * min + t * max

def random_angle_vector(min_angle):
    direction = pygame.math.Vector2(0, 0)
    while (math.fabs(direction.x) < min_angle and
           math.fabs(direction.y) < min_angle):
        direction.x = random.uniform(-1.0, 1.0)
        direction.y = random.uniform(-1.0, 1.0)
    return direction

def random_angle(min_angle, max_angle):
    angle = 0
    while math.fabs(angle) < min_angle:
        angle = random.randint(-max_angle, max_angle)
    return angle

def random_position(min_distance, width, height, avoid_rect):
    distance = 0
    while distance < min_distance:
        position_x = random.randint(0, width)
        position_y = random.randint(0, height)
        x_distance = math.fabs(position_x - avoid_rect.centerx)
        y_distance = math.fabs(position_y - avoid_rect.centery)
        distance = math.hypot(x_distance, y_distance)
    return pygame.math.Vector2(position_x, position_y)
