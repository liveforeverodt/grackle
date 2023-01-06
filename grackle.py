#!/usr/bin/env python
"""Grackle game (is that even the name?)
"""
__author__ = 'Kevin'
__copyright__ = 'Copyright (c) 2014, CloudCage'

import argparse
import logging
import random

#import pygame
#import kgame

LOGGER = logging.getLogger()

SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN = 800, 600
FRAMERATE = 20

TILE_ARROW = 'arrow: Put opponents tile under pile'
TILE_BOOT = 'boot: Play the boot then the top card immediately'
TILE_CHEST = 'chest: Take one more turn; hopefully you will win the game'
TILE_HAMHOCK = 'hamhock: Get new tile and put into larder for one turn'
TILE_KEY = 'key: Nothing; hopefully you will win the game.'
TILE_MIRROR = 'mirror: Re-use any tile in play'
TILE_MONEYBAG = 'moneybag: Look at and optionally replace top'
TILE_RAVEN = "raven: Look at opponent's tile"
TILE_ROPE = 'rope: Look at bottom pile tile and optionally move it to the top'
TILE_SHIELD = 'shield: Protect player from any effects of tiles in play'
TILE_SHOVEL = 'shovel: Bury a tile in play under pile (removing its effect)'
TILE_SICKLE = "sickle: Kill the effect of an opponent's tile"
TILE_SWORD = 'sword: Trade tiles with opponent'
TILE_WIND = 'wind: Shuffle all tiles in play into the pile (except wind)'

TILES = [
        TILE_ARROW,
        TILE_BOOT,
        TILE_HAMHOCK,
        TILE_MIRROR,
        TILE_MONEYBAG,
        TILE_RAVEN,
        TILE_ROPE,
        TILE_SHIELD,
        TILE_SHOVEL,
        TILE_SICKLE,
        TILE_SWORD,
        TILE_WIND,
        ]
TILES_KEY = [
        TILE_CHEST,
        TILE_KEY,
        ]
TILES_MAX = 2


class Player(object):
    def __init__(self, name, password=None):
        self.name = name
        self.password = password
        self.tiles = []
        self.effects = []
        self.larder = None

    def add_tile(self, tile):
        """Adds tile to player's tiles.

        Args:
            tile:

        Returns:
            None if tile was added successfully, otherwise the tile is
            returned.
        """
        if len(self.tiles) < TILES_MAX and tile not in self.tiles:
            self.tiles.append(tile)
            tile = None
        return tile

    def show_tiles(self):
        """Shows and returns the tiles the player can play.
        """
        print('%s currently has the following tile(s):' % self.name)
        for index, tile in enumerate(self.tiles, start=1):
            print('    %d) %s' % (index, tile))

    def select_tile(self):
        """Plays a hand: player selects tile to play.
        """
        # If there is something in the larder, it MUST be played next
        if self.larder:
            tile = self.larder
            self.larder = None
            return tile

        if not self.tiles:
            print('%s has no tiles to play!  Skipping turn.' % self.name)
            return None

        tile = None
        while not tile:
            self.show_tiles()
            valid_options = range(1, len(self.tiles) + 1)
            try:
                answer = input('Which tile do you want to play? %s ' %
                        valid_options)
            except:
                answer = 0
            if answer in valid_options:
                correct_input = True
                tile = self.tiles[answer - 1]
                self.tiles.remove(tile)
            else:
                exit()
        return tile


class Pile(object):
    def __init__(self, num_to_remove=0):
        """Returns a shuffled pile of tiles.

        Args:
            num_to_remove: Number of tiles to remove prior to shuffling.

        Returns:
            A shuffled pile, with N tile optionally removed.
        """
        self.in_play = []
        self.pile = list(TILES)
        for i in range(num_to_remove):
            if len(self.pile) > TILES_MAX * 2:
                random_tile = random.choice(self.pile)
                self.pile.remove(random_tile)
        self.pile += TILES_KEY
        self.shuffle()

    def shuffle(self):
        """Shuffles pile tiles.
        """
        random.shuffle(self.pile)

    def deal(self):
        """Removes and returns the top tile from the pile.

        Returns:
            Top tile from the pile.  If there are no tiles in the pile,
            None is returned.
        """
        if self.pile:
            tile = self.pile[0]
            self.pile.remove(tile)
        else:
            tile = None
        return tile

    def play(self, tile):
        """Puts a tile 'in_play'.

        Args:
            tile:
        """
        print('You have played %s' % tile)
        self.in_play.append(tile)

    def reintegrate(self):
        """Puts the in-play tiles back into the pile.
        """
        self.pile += self.in_play
        self.in_play = []

    def return_tile(self, tile):
        """Returns a tile to the top of the pile.

        Args:
            tile:
        """
        self.pile.insert(0, tile)

    def bury_tile(self, tile):
        """Buries a tile at the bottom of the pile.

        Args:
            tile:
        """
        self.pile.append(tile)

    def show_in_play(self):
        """Shows tiles that are 'in-play' on the board.
        """
        print('The board:')
        for tile in self.in_play:
            print('    %s' % tile)


def verify_player(player):
    """Simple check to see if the current player is at the console.

    Additionally, a challenge prompt could be added.

    Args:
        player: The current player object
    """
    correct_player = False
    while not correct_player:
        print('\n' * 50)
        try:
            answer = input('Is this %s? (1 = Yes, 0 = No) ' % player.name)
            answer = int(answer)
        except:
            answer = 0
        if answer < 0:
            exit()
        correct_player = bool(answer)


def verify_game_end(pile):
    """Checks to see if the key and chest are both in play.

    Args:
        pile:

    Returns:
        Boolean True if both key and chest are in play, False otherwise.
    """
    return 'key' in pile.in_play and 'chest' in pile.in_play


def parse_args():
    """Augment argument parser with script-specific options.

    Returns:
        argparse Parser object with flags as attributes.
    """
    parser = argparse.ArgumentParser(
            description='Grackle: The Python Version')
    parser.add_argument('-p', '--p1', default='Player 1',
            help='Name of Player 1.')
    parser.add_argument('-P', '--p2', default='Player 2',
            help='Name of Player 2.')
    parser.add_argument('-r', '--remove', type=int, default=0,
            help='Number of tiles to remove.')
    args = parser.parse_args()
    return args


def main():
    p1 = Player(ARGS.p1)
    p2 = Player(ARGS.p2)
    pile = Pile(num_to_remove=ARGS.remove)
    # Set up each player with one tile
    p1.add_tile(pile.deal())
    p2.add_tile(pile.deal())
    current_player = p1
    game_over = False
    while not game_over:
        verify_player(current_player)
        pile.show_in_play()
        tile = pile.deal()
        if tile:
            tile = current_player.add_tile(tile)
        if tile:
            pile.return_tile
        tile = current_player.select_tile()
        # Now determine the effects of each tile
        while tile:
            pile.play(tile)
            if tile == TILE_ARROW:
                pass
            elif tile == TILE_BOOT:
                print('You are moving so fast that you play the next tile on the'
                      ' pile as well immediately(!)')
                tile = pile.deal()
            elif tile == TILE_HAMHOCK:
                tile = pile.deal()
                current_player.add_tile(tile)
                tile = current_player.add_to_larder(tile)
            elif tile == TILE_MIRROR:
                pass
            elif tile == TILE_MONEYBAG:
                pass
            elif tile == TILE_RAVEN:
                pass
            elif tile == TILE_ROPE:
                pass
            elif tile == TILE_SHIELD:
                pass
            elif tile == TILE_SHOVEL:
                pass
            elif tile == TILE_SICKLE:
                pass
            elif tile == TILE_SWORD:
                pass
            elif tile == TILE_WIND:
                pass
            elif tile == TILE_CHEST:
                pass
            elif tile == TILE_KEY:
                pass

        game_over = verify_game_end(pile)
        if game_over:
            print('%s wins!' % current_player.name)
        else:
            if current_player == p1:
                current_player = p2
            else:
                current_player = p1
    print('Thanks for playing.')


if __name__ == '__main__':
    ARGS = parse_args()
#    pygame.init()
#    BOARD = pygame.display.set_mode(SCREEN)
#    CLOCK = pygame.time.Clock()
#    for image in TILES:
#        kgame.ImageStore.add(image)
    main()
#    pygame.quit()
