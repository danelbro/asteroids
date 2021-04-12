import os
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
