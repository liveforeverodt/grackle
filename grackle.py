#!/usr/bin/env python
"""Grackle game (is that even the name?)
"""
__author__ = 'Kevin'
__copyright__ = 'Copyright (c) 2014-2023, CloudCage'

import argparse
import logging
import random

#import pygame


LOGGER = logging.getLogger()

SCREEN_WIDTH, SCREEN_HEIGHT = SCREEN = 800, 600
FRAMERATE = 20

TILES = {  # Ordering is important!  These two are required at all times:
    'key': 'Nothing; hopefully you will win the game.',
    'chest': 'Take one more turn; hopefully you will win the game',
    # The tiles below can be removed prior to game play
    'arrow': "Put the tile in opponent's hand under pile",
    'boot': 'Play the boot then the top card immediately',
    'hamhock': 'Get new tile and put into larder for one turn',
    'mirror': 'Re-use any tile in play',
    'coinpurse': 'Draw a tile and place one in your hand back on top',
    'raven': "Look at opponent's tile",
    'rope': 'Look at bottom pile tile and optionally move it to the top',
    'shield': 'Protect player from any effects of tiles in play',  # except wind, shovel
    'shovel': 'Bury a tile in play under pile (removing its effect)',
    'sickle': "Kill the effect of an opponent's tile",
    'sword': 'Trade tiles with opponent',
    'wind': 'Shuffle all tiles in play into the pile (except wind)',
    }
HAND_MAX = 2


class Player:
    def __init__(self, name, password=None):
        self.name = name
        self.password = password
        self.tiles = []
        self.shield = False  # Basically, just the shield
        self.larder = None

    def add_tile(self, tile):
        """Adds tile to player's tiles.

        Args:
            tile:

        Returns:
            None if tile was added successfully, otherwise the tile is
            returned.
        """
        if len(self.tiles) < HAND_MAX and tile not in self.tiles:
            self.tiles.append(tile)
            tile = None
        return tile

    def show_tiles(self):
        """Shows and returns the tiles the player can play.
        """
        print(f'{self.name} currently has the following tile(s):')
        for index, tile in enumerate(self.tiles, start=1):
            print(f'    {index}) {tile}')

    def select_tile(self):
        """Selects tile: player selects tile to play.
        """
        tile = None
        # If there is something in the larder, it MUST be played next
        if self.larder:
            tile = self.larder
            self.larder = None
        elif not self.tiles:
            print(f'{self.name} has no tiles to play!  Skipping turn.')
        else:
            while not tile:
                self.show_tiles()
                valid_options = list(range(1, len(self.tiles) + 1))
                try:
                    answer = int(input(f'Tile to play? {valid_options} '))
                except:
                    answer = 0
                if answer in valid_options:
                    tile = self.tiles[answer - 1]
                    self.tiles.remove(tile)
                else:
                    print('That was not a valid option.  Try again.')
        return tile

    def add_to_larder(self, tile):
        """Puts a tile into the larder.

        Args:
            tile:

        Returns:
            None if tile was added to larder properly, else the tile.
        """
        if tile:
            if not self.larder:
                self.larder = tile
                tile = None
                print(f"{tile} added to {self.name}'s larder.")
            else:
                print('add_to_larder: Something went wrong; already full?')
        else:
            print('add_to_larder: Tile is empty?')
        return tile


class Pile:
    def __init__(self, remove=0):
        """Returns a shuffled pile of tiles.

        Args:
            remove: Number of tiles to remove prior to shuffling.

        Returns:
            A shuffled pile, with N tile optionally removed.
        """
        self.in_play = []
        tiles = list(TILES)
        self.pile, tiles = tiles[:2], tiles[2:]  # First two are key, chest
        for _ in range(remove):
            if len(tiles) > HAND_MAX * 2:
                tile = random.choice(tiles)
                tiles.remove(tile)
                print(f'Removed 1 tiles out of {remove}...')
            else:
                print(f'Not enough tiles {len(tiles)} to remove {remove}.')
        self.pile += tiles
        self.shuffle()

    def shuffle(self):
        """Shuffles pile tiles.
        """
        random.shuffle(self.pile)

    def deal(self):
        """Removes and returns the top tile from the pile.

        Returns:
            Top tile from the pile, or None if the pile is empty.
        """
        if self.pile:
            tile = self.pile[0]
            self.remove(tile)
        else:
            tile = None
            print('There are no more cards in the pile to deal!')
        return tile

    def play(self, tile):
        """Puts a tile 'in_play'.

        Args:
            tile:
        """
        print(f'You have played {tile}: {TILES[tile]}.')
        self.in_play.append(tile)

    def remove(self, tile):
        """Remove a tile from the pile.

        Args:
            tile:

        Returns:
            None if the tile was successfully removed; otherwise tile.
        """
        if tile in self.pile:
            self.pile.remove(tile)
            tile = None
        return tile

    def reintegrate(self):
        """Puts the in-play tiles back into the pile (at the bottom).
        """
        self.pile += self.in_play
        self.in_play = []

    def return_tile(self, tile):
        """Puts a tile at the top of the pile.

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
            print(f'    {tile}: {TILES[tile]}')


def verify_player(player):
    """Simple check to see if the current player is at the console.

    Additionally, a challenge prompt could be added.

    Args:
        player: The current player object
    """
    correct_player = False
    while not correct_player:
        print('\n' * 5)
        answer = input(f'Is this {player.name}? (y/n) ').lower()
        correct_player = answer in ('y', 'yes')


def verify_game_end(pile):
    """Checks to see if the key and chest are both in play.

    Args:
        pile:

    Returns:
        Boolean True if both key and chest are in play, False otherwise.
    """
    game_end = 'key' in pile.in_play and 'chest' in pile.in_play
    return game_end


def parse_args():
    """Augment argument parser with script-specific options.

    Returns:
        argparse Parser object with flags as attributes.
    """
    parser = argparse.ArgumentParser(
        description='Grackle: The Python Version')
    parser.add_argument(
        '-p', '--p1', default='Player 1',
        help='Name of Player 1.')
    parser.add_argument(
        '-P', '--p2', default='Player 2',
        help='Name of Player 2.')
    parser.add_argument(
        '-r', '--remove', default=0, type=int,
        help='Number of tiles to remove.')
    args = parser.parse_args()
    return args


def main():
    """Does the work.
    """
#    for image in TILES + TILES_KEY:
#        IMAGES.add(image)

    p1 = Player(ARGS.p1)
    p2 = Player(ARGS.p2)
    pile = Pile(remove=ARGS.remove)
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
            if current_player.add_tile(tile):
                pile.return_tile(tile)
        tile = current_player.select_tile()
        # Now determine the effects of each tile
        while tile:
            pile.play(tile)
            if tile == 'chest':
                tile = None
            elif tile == 'key':
                tile = None
            elif tile == 'arrow':
                tile = None
            elif tile == 'boot':
                print('You are moving so fast that you play the next tile on'
                      ' the pile as well immediately(!)')
                tile = pile.deal()
                # Goes around again; what happens if there are no more tiles?
            elif tile == 'hamhock':
                print('You pick up another card and put it in the larder.')
                tile = pile.deal()
                tile = current_player.add_to_larder(tile)
                tile = None
            elif tile == 'mirror':
                tile = pile.discard(tile)
            elif tile == 'coinpurse':
                tile = pile.discard(tile)
            elif tile == 'raven':
                tile = pile.discard(tile)
            elif tile == 'rope':
                bottom = pile.pile[-1]
                print(f'Bottom of pile: {TILES[bottom]}')
                answer = input('Do you want to move it to the top? (y/n) ')
                if answer.lower() in ('y', 'yes'):
                    pile.remove(bottom)
                    pile.return_tile(bottom)
                tile = pile.discard(tile)
            elif tile == 'shield':
                tile = pile.discard(tile)
            elif tile == 'shovel':
                tile = pile.discard(tile)
            elif tile == 'sickle':
                tile = pile.discard(tile)
            elif tile == 'sword':
                tile = pile.discard(tile)
            elif tile == 'wind':
                tile = pile.discard(tile)
                pile.reintegrate()
                pile.shuffle()
            print(f'Pile: {pile.pile}')
            print(f'In Play: {pile.in_play}')
            print(f'Discards: {pile.discards}')

        game_over = verify_game_end(pile)
        if game_over:
            print(f'{current_player.name} wins!')
        elif current_player == p1:
            current_player = p2
        else:
            current_player = p1
    print('Thanks for playing.')


if __name__ == '__main__':
    ARGS = parse_args()
#    pygame.init()
#    BOARD = pygame.display.set_mode(BOARD_SIZE)
#    CLOCK = pygame.time.Clock()
#    IMAGES = ImageStore()
    main()
#    pygame.quit()
