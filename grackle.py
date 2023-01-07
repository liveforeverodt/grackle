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

COINS = {  # Ordering is important!  These two are required at all times:
    'key': 'Nothing; hopefully you will win the game.',
    'chest': 'Take one more turn; hopefully you will win the game',
    # The coins below can be removed prior to game play
    'arrow': "Bury the coin in opponent's hand under pile",
    'boot': 'Play the boot then the top coin immediately',
    'coinpurse': 'Draw a coin and place one in your hand back on top',
    'hamhock': 'Get new coin and put into larder for one turn',
    'knife': 'Trade coins with opponent',
    'mirror': 'Re-use any coin in play',
    'raven': "Look at opponent's coin",
    'rope': 'Look at bottom pile coin and optionally move it to the top',
    'shield': 'Protect player from any effects of coins in play',  # except wind, shovel
    'shovel': 'Bury a coin in play under pile (removing its effect)',
    'sickle': "Kill the effect of the coin in opponent's hand",
    'wind': 'Shuffle all coins in play into the pile (except wind)',
    }
HAND_MAX = 1


class Player:
    """Player class
    """
    def __init__(self, name):
        """Create a player with name and password.

        Args:
            name: Default name to use (can be changed)
        """
        keep_going = True
        while keep_going:
            new_name = input(f'{name}, what do you want to be called? ({name}) ')
            if not new_name:
                new_name = name
            answer = input(f'"{new_name}": Is this correct? (y/n) ')
            if answer.lower().startswith('y'):
                keep_going = False
        self.name = new_name
        print(f'Welcome, {self.name}!')
        keep_going = True
        while keep_going:
            password = input(f'{self.name}, pick a simple password: ')
            if password:
                verify = input(f'Please re-enter the password: ')
                if verify == password:
                    keep_going = False
                else:
                    print(f'{self.name}, your password verification failed.')
            else:
                print(f'{self.name}, your password cannot be blank.')
        self.password = password
        self.coins = []
        self.shield = False
        self.larder = None
        self.note = []  # messages based on previous turn or action

    def verify(self):
        """Simple check to see if the current player is at the console.
        """
        hide_previous()
        verified = False
        while not verified:
            answer = input(f'{self.name}, what is your password? ')
            verified = answer == self.password
        print(f'Welcome back, {self.name}.')

    def show_status(self):
        """Show current player status.
        """
        print(f'{self.name}:')
        print(f'    Coins: {self.coins}')
        print(f'    Shielded: {self.shield}')
        print(f'    Larder: {self.larder}')

    def add_note(self, line):
        """Add a line of text to the player note.

        Args:
            line: Line of text to be added to the note.
        """
        if line:
            self.note.append(line)

    def show_note(self):
        """Shows note, and clears it...
        """
        if self.note:
            print('=' * 80)
            print(f'{self.name} notes:')
            for line in self.note:
                print(line)
            print('=' * 80)
            self.note = []

    def add_coin(self, coin):
        """Adds coin to player's coins.

        Args:
            coin:

        Returns:
            None if coin was added successfully, otherwise the coin is
            returned.
        """
        if len(self.coins) < HAND_MAX and coin not in self.coins:
            self.coins.append(coin)
            coin = None
        return coin

    def get_coin(self):
        """Get coin from player, removing it from their coins.

        Returns:
            First coin, if any, otherwise None.
        """
        if self.coins:
            coin = self.coins[0]
            self.coins.remove(coin)
        else:
            coin = None
            print(f'{self.name} has no coins to get.')
        return coin

    def show_coins(self):
        """Shows and returns the coins the player can play.
        """
        print(f'{self.name} currently has the following coin(s):')
        for index, coin in enumerate(self.coins, start=1):
            print(f'    {index}) {coin}')

    def select_coin(self):
        """Selects coin: player selects coin to play.
        """
        coin = None
        # If there is something in the larder, it MUST be played next
        if self.larder:
            coin = self.remove_larder()
        elif not self.coins:
            print(f'{self.name} has no coins to play!  Skipping turn.')
        else:
            coin = select_from_list(self.coins)
        return coin

    def enable_shield(self):
        """Enables shield for a player.
        """
        if self.shield:
            print(f'{self.name} already has a shield...')
        else:
            self.shield = True
            print(f'{self.name} has enabled a shield!')

    def disable_shield(self):
        """Disables shield for a player.
        """
        if self.shield:
            self.shield = False
            print(f'{self.name} has shield removed!')
        else:
            print(f'{self.name} has no shield to disable...')

    def add_larder(self, coin):
        """Puts a coin into the larder.

        Args:
            coin:

        Returns:
            None if coin was added to larder properly, else the coin.
        """
        if coin:
            if not self.larder:
                self.larder = coin
                print(f"{coin} added to {self.name}'s larder.")
                coin = None
            else:
                print('add_larder: Larder already full?')
        else:
            print('add_larder: Nothing to add?')
        return coin

    def remove_larder(self):
        """Remove coin from larder.

        Returns:
            coin that was in larder, if any.
        """
        if self.larder:
            print(f'{self.name} uses the coin in the larder.')
        coin = self.larder
        self.larder = None
        return coin


class Pile:
    def __init__(self, remove=0):
        """Creates a shuffled pile of coins.

        Args:
            remove: Number of coins to remove prior to shuffling.
        """
        self.in_play = []
        coins = list(COINS)
        self.coins, coins = coins[:2], coins[2:]  # First two are key, chest
        for _ in range(remove):
            if len(coins) > HAND_MAX * 2:
                coin = random.choice(coins)
                coins.remove(coin)
                print(f'Removed 1 coins out of {remove}...')
            else:
                print(f'Not enough coins {len(coins)} to remove {remove}.')
        self.coins += coins
        self.shuffle_coins()

    def shuffle_coins(self, stack='coins'):
        """Shuffles coins.

        Args:
            stack: Coins to shuffle, either 'coins' or 'in_play'.
        """
        coins = getattr(self, stack)
        random.shuffle(coins)

    def get_coin(self):
        """Get coin from top of pile.

        Returns:
            First coin, if any, otherwise None.
        """
        if self.coins:
            coin = self.coins[0]
            self.remove_coin(coin)
        else:
            coin = None
            print('There are no more coins in the pile to get!')
        return coin

    def play_coin(self, coin):
        """Puts a coin 'in_play'.

        Args:
            coin:
        """
        print(f'You have played {coin}: {COINS[coin]}.')
        self.in_play.append(coin)

    def remove_coin(self, coin):
        """Remove a coin from the pile.

        Args:
            coin:

        Returns:
            None if the coin was successfully removed; otherwise coin.
        """
        if coin in self.coins:
            self.coins.remove(coin)
            coin = None
        return coin

    def reintegrate(self):
        """Puts the in-play coins back into the pile (at the bottom).
        """
        self.coins += self.in_play
        self.in_play = []

    def put_coin(self, coin):
        """Puts a coin at the top of the pile.

        Args:
            coin:
        """
        self.coins.insert(0, coin)

    def bury_coin(self, coin):
        """Buries a coin at the bottom of the pile.

        Args:
            coin:
        """
        self.coins.append(coin)

    def put_in_play(self, coin):
        """Put a coin into the in_play pile.

        Args:
            coin:
        """
        self.remove_coin(coin)
        self.in_play.append(coin)

    def show_coins(self, stack='in_play'):
        """Shows coins that are in a given pile.

        Args:
            stack: Either 'pile' or 'in_play'
        """
        coins = getattr(self, stack)
        if coins:
            print(f'{stack.title()}:')
            for coin in coins:
                print(f'    {coin}: {COINS[coin]}')


def select_from_list(item_list):
    """Select an item from a list, removing it from the list.

    Args:
        item_list: List of items from which to select.

    Returns:
        item selected; item_list is updated in place.
    """
    item = None
    while not item:
        print('Select from the following items:')
        for index, selection in enumerate(item_list, start=1):
            if selection in COINS:
                selection = f'{selection}: {COINS[selection]}'
            print(f'    {index}) {selection}')
        options = list(range(1, len(item_list) + 1))
        try:
            answer = int(input(f'Item to select? {options} '))
        except:
            answer = 0
        if answer in options:
            item = item_list[answer - 1]
            item_list.remove(item)
        else:
            print('That was not a valid option.  Try again.')
    return item


def hide_previous():
    """Hide previous text...
    """
    print(f'{"* hidden " * 10}*\n' * 5)


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
        help='Number of coins to remove.')
    args = parser.parse_args()
    return args


def main():
    """Does the work.
    """
#    for image in COINS:
#        IMAGES.add(image)

    p1 = Player(ARGS.p1)
    hide_previous()
    p2 = Player(ARGS.p2)
    pile = Pile(remove=ARGS.remove)
    # Set up each player with one coin
    p1.add_coin(pile.get_coin())
    p2.add_coin(pile.get_coin())
    p_cur, p_oth = p2, p1
    go_again = False
    game_over = False
    while not game_over:
        if not go_again:
            p_cur, p_oth = p_oth, p_cur  # swap players
            p_cur.verify()
            p_cur.show_status()
            p_cur.show_note()
        else:
            print(f'{p_cur.name}, please go again.')
            go_again = False
        pile.show_coins()
        if not p_cur.larder:
            coin = pile.get_coin()
            if coin:
                print(f'You drew {coin}: {COINS[coin]}')
                if p_cur.add_coin(coin):
                    pile.put_coin(coin)
        coin = p_cur.select_coin()
        # Now determine the effects of each coin
        while coin:
            pile.play_coin(coin)
            p_oth.add_note(f'{p_cur.name} used {coin}')
            if coin == 'chest':
                go_again = True
                coin = None
            elif coin == 'key':
                coin = None
            elif coin == 'arrow':
                if not p_oth.shield:
                    coin = p_oth.get_coin()
                    if coin:
                        pile.bury_coin(coin)
                        print("You bury your opponent's coin in the pile.")
                        p_oth.add_note(f'{p_cur.name} buried your {coin}')
                        coin = pile.get_coin()
                        p_oth.add_coin(coin)
                        p_oth.add_note(f'You drew replacement: {coin}')
                else:
                    print(f'{p_oth.name} is shielded!')
                coin = None
            elif coin == 'boot':
                print('You play the next coin on the pile immediately(!)')
                coin = pile.get_coin()
            elif coin == 'coinpurse':
                coin = pile.get_coin()
                print(f'You drew {coin}: {COINS[coin]}')
                if coin:
                    p_cur.add_coin(coin)
                if p_cur.coins:
                    print('Now select a coin to put back on the pile.')
                    coin = select_from_list(p_cur.coins)
                    print(f'You put {coin} back on top of the pile.')
                    pile.put_coin(coin)
                coin = None
            elif coin == 'hamhock':
                print('You pick another coin and put it in the larder.')
                coin = pile.get_coin()
                coin = p_cur.add_larder(coin)
                coin = None
            elif coin == 'mirror':
                # Pretty sloppy, this
                coin_orig = coin
                pile.in_play.remove(coin)
                if pile.in_play:
                    coin = select_from_list(pile.in_play)
                else:
                    print('There are no coins in play!')
                    coin = None
                pile.in_play.append(coin_orig)
            elif coin == 'raven':
                if not p_oth.shield:
                    if p_oth.coins:
                        coin = p_oth.coins[0]
                        print(f'{p_oth.name} has {coin}: {COINS[coin]}')
                    else:
                        print(f'{p_oth.name} does not have any coins!')
                    p_oth.add_note(f'{p_cur.name} saw your hand.')
                else:
                    print(f'{p_oth.name} is shielded!')
                coin = None
            elif coin == 'rope':
                bottom = pile.coins[-1]
                print(f'Bottom of pile: {bottom}: {COINS[bottom]}')
                answer = input('Do you want to move it to the top? (y/n) ')
                if answer.lower() in ('y', 'yes'):
                    pile.remove_coin(bottom)
                    pile.put_coin(bottom)
                coin = None
            elif coin == 'shield':
                p_cur.enable_shield()
                coin = None
            elif coin == 'shovel':
                print('Which in-play coin would you like to bury?')
                # Pretty sloppy, this
                coin_orig = coin
                pile.in_play.remove(coin)
                if pile.in_play:
                    coin = select_from_list(pile.in_play)
                    pile.bury_coin(coin)
                    if coin == 'shield':
                        p_cur.disable_shield()
                        p_oth.disable_shield()
                    p_oth.add_note(f'{p_cur.name} buried {coin}')
                else:
                    print('There are no coins in play!')
                pile.in_play.append(coin_orig)
                coin = None
            elif coin == 'sickle':
                if not p_oth.shield:
                    coin = p_oth.get_coin()
                    if coin:
                        pile.in_play.append(coin)
                        print(f'You kill the coin of your opponent: {coin}')
                        p_oth.add_note(f'{p_cur.name} killed your {coin}')
                        coin = pile.get_coin()
                        p_oth.add_coin(coin)
                        p_oth.add_note(f'You drew replacement: {coin}')
                else:
                    print(f'{p_oth.name} is shielded!')
                coin = None
            elif coin == 'knife':
                if not p_oth.shield:
                    to_give = p_cur.get_coin()
                    to_get = p_oth.get_coin()
                    print(f'You swap {to_give} for {to_get}.')
                    p_oth.add_note(f'{p_cur.name} swapped {to_get} for {to_give}')
                    if to_get:
                        p_cur.add_coin(to_get)
                    if to_give:
                        p_oth.add_coin(to_give)
                else:
                    print(f'{p_oth.name} is shielded!')
                coin = None
            elif coin == 'wind':
                pile.reintegrate()
                pile.put_in_play(coin)
                pile.shuffle_coins()
                p_cur.disable_shield()
                p_oth.disable_shield()
                coin = None

        game_over = verify_game_end(pile)
        if game_over:
            print(f'{p_cur.name} wins!')
        elif not go_again:
            print(f'Pile: {pile.coins}')
            pile.show_coins()
            input(f'{p_cur.name}, press return to end your turn.')
    print('Thanks for playing.')


if __name__ == '__main__':
    ARGS = parse_args()
#    pygame.init()
#    BOARD = pygame.display.set_mode(BOARD_SIZE)
#    CLOCK = pygame.time.Clock()
#    IMAGES = ImageStore()
    main()
#    pygame.quit()
