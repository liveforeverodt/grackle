#!/usr/bin/env python3
"""Grackle game (is that even the name?)
Coin of the Realm (CotR)

This supports:
- multiple players

1: In order to support different hand sizes, need to consider:
=====
If player gets to see an opponent's coin and they have more than one:
  - Does it default to first coin in opponent's hand?
    - this is easiest
    - In a physical game, this can easily be forced by opponent
  - Does player get to pick which one?
    - this is not hard
  - Does the opponent get to pick?
    - increases times control must be passed back and forth
First two options are implement(ed/able), but not selectable as of now.

SUGGESTED REMEDY:
Always let the player decide which ooponent coin to target.
This also works better in real life when there is no clear "first" coin.
There should not be an option here, and this is what is implemented.

2: If a hand has more than 2 coins, what happens when there are not
   enough coins to keep the hand "full"?
=====
If there is no policy on keeping the hand "full" the hand size will
eventually dwindle to 2.
  - BUT BUT wind and other cards can increase the pile again, making
    more coins available
Not addressing this issue will reduce game play to hands of HAND_MAX=2
once there are no more cards on the pile.

SUGGESTED REMEDY:
At the start of a player's turn, they will draw one additional coin if
they have fewer than a "full" hand and there are coins in the draw pile.
This is what was implemented, enabled by -f future flag.
### This would be a place to get a 'full' hand if policy was made
### #  if len(p_cur.coins) < ARGS.coins and pile.coins:
### #      add another coin to player's hand
"""
__author__ = 'Kevin'
__copyright__ = 'Copyright (c) 2014-2023, CloudCage'
__version__ = '0.9.0'


import argparse
import random


NAME_BASE = 'Player'
COINS = {  # Ordering is important!  These two are required at all times:
    '[chest]': 'Take one more turn; hopefully you will get the key and win',
    '[key]': 'No effect; hopefully you will win the game if you play this',
    # Coins below can be removed prior to game play via -r flag
    '[arrow]': "Bury an opponent's coin under the pile, if they have one",
    '[boots]': 'Play this then the top coin from pile immediately',
    '[coin_purse]': 'Draw new coin and put one in your hand on top of pile',
    '[ham_hock]': 'Draw new coin and put it into your larder for one turn',
    '[knife]': 'Trade coins with an opponent, if they have one',
    '[lantern]': 'Look at top two coins in pile, returning them in any order',
    '[mirror]': 'Re-use any coin in play, if there are any',
    '[raven]': "Look at an opponent's coin, if they have one",
    '[rope]': 'Look at bottom coin of pile and optionally move it to the top',
    '[shield]': 'Protects player from effects of coins except wind, shovel',
    '[shovel]': 'Bury a coin in play under pile, removing its effect',
    '[sickle]': "Put an opponent's coin in play without any effect",
    '[wind]': 'Shuffle all coins in play into the pile (except wind)',
    }
HAND_MIN = 2  # number of coins players can have: held coin + drawn coin
HAND_MAX = 3  #   (not including larder, which is a separate thing)
PLAYER_MIN = 2
PLAYER_MAX = len(COINS) // HAND_MIN  # Does not take into account removal
REMOVE_MAX = 5  # Does not take into account other parameters
SELECTION_MODES = (  # Not selectable; only 'first' and 'player' implemented
    'first',  # Always selects first coin in opponent's hand
    'player',  # Player picks which coin in opponent's hand
    'opponent', # Opponent picks which coin in their hand -- will not do?
    )
SELECTION_MODE = SELECTION_MODES[0]


class Player:
    """Player class
    """
    def __init__(self, name, prefix=None):
        """Create a player with name and password.

        Args:
            name: Default name to use (can be changed)
            prefix: Optional prefix to preface player name
        """
        if prefix:
            show_name = f'{prefix}_{name}'
        else:
            show_name = name
        keep_going = True
        while keep_going:
            new_name = input(f'What do you want to be called? ({show_name}) ')
            if not new_name:
                new_name = name
            if prefix:
                print(f'Required prefix {prefix}_ added...')
                new_name = f'{prefix}_{new_name}'
            answer = input(f'"{new_name}": Is this correct? (y/n) ')
            if answer.lower().startswith('y'):
                keep_going = False
        self.name = new_name
        print(f'Welcome, {self.name}!')
        keep_going = True
        while keep_going:
            password = input(f'{self.name}, pick a simple password: ')
            if password:
                verify = input('Please re-enter the password: ')
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
        self.note = []  # ephemeral messages based on previous actions

    def verify(self):
        """Simple check to see if the current player is at the console.
        """
        hide_previous()
        verified = False
        while not verified:
            answer = input(f'{self.name}, what is your password? ')
            verified = answer == self.password
        print(f'Welcome back, {self.name}.')

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
            print('Which coin would you like to play?')
            coin = select_from_list(self.coins)
        return coin

    def show_status(self, clear_note=True):
        """Show current player status, including ephemeral notes...

        Args:
            clear_note: Boolean; clears note if True, keeps otherwise.
        """
        print('=' * 80)
        print(f'{self.name} status:')
        print(f'  Coins: {self.coins}')
        print(f'  Shield: {self.shield}')
        print(f'  Larder: {self.larder}')
        if self.note:
            print('  Notes:')
            for line in self.note:
                print(f'  - {line}')
            if clear_note:
                self.note = []
        print('=' * 80)

    def add_note(self, line):
        """Add a line of text to the player note.

        Args:
            line: Line of text to be added to the note.
        """
        if line:
            self.note.append(line)

    def add_coin(self, coin):
        """Adds coin to player's coins.

        Args:
            coin:

        Returns:
            None if coin was added successfully, otherwise the coin is
            returned.
        """
        if len(self.coins) < ARGS.coins and coin not in self.coins:
            self.coins.append(coin)
            coin = None
        return coin

    def get_coin(self, index=None, by_name=False):
        """Get coin from player, removing it from their coins.

        Arguments are only needed when there is more than one coin held.

        Args:
            index: Optional integer index of coin requested.
            by_name: Select coin by name rather than index.

        Returns:
            A coin object, if any, otherwise None.
        """
        if by_name and len(self.coins) > 1:
            coin = select_from_list(self.coins)
        else:
            index = self.get_coin_index(index)
            if index is not None:
                coin = self.coins[index]
                self.coins.remove(coin)
            else:
                coin = None
                print(f'{self.name} has no coins to get.')
        return coin

    def show_coin(self, index=None):
        """Show a coin given by index, or else ask which coin.

        If there is one coin, just show it regardless of index.
        If there are no coins, tell that.

        Args:
            index: Integer index into list of coins in hand.
        """
        index = self.get_coin_index(index)
        if index is not None:
            coin = self.coins[index]
            print(f'{self.name} has {coin}: {COINS[coin]}')
        else:
            print(f'{self.name} has no coins to show!')

    def get_coin_index(self, index=None):
        """Gets the index of a coin; used when opponent asks for a coin.

        Returns:
            Index of coin in hand, or None if there are no coins.
        """
        if index:
            if self.coins and index > len(self.coins):
                index = None
            if index < 0 and abs(index) > len(self.coins):
                index = None
            if index is None:
                print('Requested index was out of range.')
        if index is None:
            if len(self.coins) > 1:
                print(f"Which of {self.name}'s coins do you want index of?")
                options = [index+1 for index in range(len(self.coins))]
                index = select_from_list(options)
                index = int(index) - 1
            elif len(self.coins) == 1:
                index = 0
        return index

    def enable_shield(self):
        """Enables shield for a player.
        """
        if self.shield:
            print(f'{self.name} already has shield...')
        else:
            self.shield = True
            print(f'{self.name} has enabled shield!')

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
    """Pile/Stack class
    """
    def __init__(self, remove=0):
        """Creates a shuffled pile of coins.

        Args:
            remove: Number of coins to remove prior to shuffling.
        """
        self.in_play = []
        coins = list(COINS)
        self.coins, coins = coins[:2], coins[2:]  # First two are chest, key
        for _ in range(remove):
            if len(coins) > ARGS.coins * ARGS.players:  # 1 hand per player
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

    def unlock_chest(self):
        """Checks if both chest and key are in play.

        Returns:
            Boolean; True if chest and key are in play, False otherwise.
        """
        unlocked = '[key]' in self.in_play and '[chest]' in self.in_play
        return unlocked


def select_from_list(item_list):
    """Select an item from a list, removing it from the list.

    If there is only one item in the list, it is automatically chosen.
    REMEMBER: This removes the chosen item from the list!

    Args:
        item_list: List of items from which to select.

    Returns:
        item selected, or None; item_list is updated in place.
    """
    if len(item_list) == 1:
        item = item_list[0]
        item_list.remove(item)  # This removes the chosen item from the list!
    else:
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
        except ValueError:
            answer = 0
        if answer in options:
            item = item_list[answer - 1]
            item_list.remove(item)
        else:
            print('That was not a valid option.  Try again.')
    return item


def select_player(players, exclude=None):
    """Select a player from list of player objects.

    Args:
        players: List of all player objects.
        exclude: player object to be excluded (from this player)

    Returns:
        Player object from list.
    """
    options = [player.name for player in players if player is not exclude]
    if len(options) > 1:
        player_name = select_from_list(options)
    else:  # There are only 2 players (there has to be at least 2)
        player_name = options[0]
    options = [player for player in players if player.name == player_name]
    player = options[0]
    return player


def add_notes(note, players, exclude=None):
    """Add notes to other players, other than current player.

    Args:
        players: List of all player objects.
        exclude: player object to be excluded (from this player)
    """
    for player in players:
        if player is not exclude:
            player.add_note(note)


def hide_previous(lines=5):
    """Hide previous text...

    Args:
        lines: Number of lines to fill...
    """
    print()
    print(f'{"* hidden " * 10}*\n' * lines)


def validate_state(players, pile, coin=None):
    """Checks if all coins are accounted for/duplicates/

    This is only for debugging.

    Args:
        players: Players list of all player objects
        pile: Pile object.

    Returns:
        True for consistent, False otherwise, with notes.
    """
    coins = []
    if coin:
        coins.append(coin)
    for player in players:
        if player.larder:
            coins.append(player.larder)
        if player.coins:
            coins += player.coins
    if pile.coins:
        coins += pile.coins
    if pile.in_play:
        coins += pile.in_play
    print(f'Coins found: {coins}')
    status = len(coins) == len(COINS)
    if not status:
        print('*' * 50)
        for coin2 in COINS:
            try:
                coins.remove(coin2)
            except ValueError:
                print(f'{coin2} not present!!!')
        for coin2 in coins:
            print(f'Additionsl {coin2}!!!')
        print('*' * 50)
    return status


def parse_args():
    """Augment argument parser with script-specific options.

    Returns:
        argparse Parser object with flags as attributes.
    """
    parser = argparse.ArgumentParser(
        description='Grackle: The Python Version',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-c', '--coins', default=HAND_MIN, type=int,
        choices=range(HAND_MIN, HAND_MAX+1),
        help='Number of coins to in each hand.')
    parser.add_argument(
        '-p', '--players', default=PLAYER_MIN, type=int,
        choices=range(PLAYER_MIN, PLAYER_MAX+1),
        help='Number of players.')
    parser.add_argument(
        '-r', '--remove', default=0, type=int,
        choices=range(REMOVE_MAX+1),
        help='Number of coins to remove prior to game start.')
    parser.add_argument(
        '-s', '--selection', default=SELECTION_MODE,
        choices=SELECTION_MODES,
        help="How opponent's coin is selected when it is needed."
            ' This is only needed when coins per hand is greater than 2.')

    parser.add_argument(
        '-f', '--future', action='store_true',
        help='Enable future features (hand padding).')
    parser.add_argument(
        '-d', '--debug', action='store_true',
        help='Set debug mode.')
    args = parser.parse_args()
    return args


def main():
    """Does the work.
    """
    # Prepare players
    players = []
    for index in range(ARGS.players):
        player = Player(NAME_BASE, index+1)
        players.append(player)
        hide_previous()
    # Prepare pile
    pile = Pile(remove=ARGS.remove)
    # Distribute coins
    for index in range(1, ARGS.coins):  # take into account drawn coin
        print(f'Getting coin {index} for each player...')
        for player in players:
            player.add_coin(pile.get_coin())

    p_index = len(players)
    go_again = False
    game_over = False
    while not game_over:
        if not go_again:
            p_index += 1  # Increment current player
            if p_index >= len(players):
                p_index = 0
            p_cur = players[p_index]
            p_cur.verify()
            p_cur.show_status()
        else:
            print()
            print(f'{p_cur.name}, please go again.')
            go_again = False
        pile.show_coins('in_play')
        print()
        if ARGS.future and len(p_cur.coins) < ARGS.coins - 1 and pile.coins:
            coin = pile.get_coin()
            print(f'Padding your hand with {coin}: {COINS[coin]}')
            p_cur.add_coin(coin)
        if not p_cur.larder:
            coin = pile.get_coin()
            if coin:
                print(f'You drew {coin}: {COINS[coin]}')
                p_cur.add_coin(coin)
        coin = p_cur.select_coin()
        # Now determine the effects of each coin
        while coin:
            print()
            print(f'You play {coin}: {COINS[coin]}.')
            add_notes(f'{p_cur.name} played {coin}', players, p_cur)
            if coin == '[chest]':
                # Take one more turn; hopefully you will get the key and win
                go_again = True
                pile.play_coin(coin)
                coin = None
            elif coin == '[key]':
                # No effect; hopefully you will win the game if you play this
                pile.play_coin(coin)
                coin = None
            elif coin == '[arrow]':
                # Bury an opponent's coin under the pile, if they have one
                pile.play_coin(coin)
                p_oth = select_player(players, p_cur)
                if not p_oth.shield:
                    ### choose opponent coin
                    coin = p_oth.get_coin()
                    if coin:
                        pile.bury_coin(coin)
                        print("You bury your opponent's coin in the pile.")
                        ### Should we show the player which coin it was?  No...
                        p_oth.add_note(f'{p_cur.name} buried your {coin}')
                        coin = pile.get_coin()
                        p_oth.add_note(f'You drew replacement: {coin}')
                        p_oth.add_coin(coin)
                else:
                    print(f'{p_oth.name} is shielded!')
                coin = None
            elif coin == '[boots]':
                # Play this then the top coin from pile immediately
                pile.play_coin(coin)
                print('You play the next coin on the pile immediately(!)')
                coin = pile.get_coin()
            elif coin == '[coin_purse]':
                # Draw new coin and put one in your hand on top of the pile
                pile.play_coin(coin)
                coin = pile.get_coin()
                if coin:
                    print(f'You drew {coin}: {COINS[coin]}')
                    p_cur.add_coin(coin)
                if p_cur.coins:
                    print('Now select a coin to put back on top of the pile.')
                    coin = select_from_list(p_cur.coins)
                    print(f'You put {coin} back on top of the pile.')
                    pile.put_coin(coin)
                coin = None
            elif coin == '[ham_hock]':
                # Draw new coin and put it into your larder for one turn
                pile.play_coin(coin)
                print('You draw another coin for your larder.')
                coin = pile.get_coin()
                if coin:
                    p_cur.add_larder(coin)
                coin = None
            elif coin == '[knife]':
                # Trade coins with an opponent, if they have one
                pile.play_coin(coin)
                p_oth = select_player(players, p_cur)
                if not p_oth.shield:
                    if len(p_cur.coins) > 1:
                        print('Which one of your coins do you want to trade?')
                    coin = p_cur.get_coin(by_name=True)
                    ### choose opponent coin
                    coin2 = p_oth.get_coin()
                    print(f'You trade {coin} for {coin2}')
                    p_oth.add_note(f'{p_cur.name} traded {coin2} for {coin}')
                    if coin2:
                        p_cur.add_coin(coin2)
                    if coin:
                        p_oth.add_coin(coin)
                else:
                    print(f'{p_oth.name} is shielded!')
                coin = coin2 = None
            elif coin == '[lantern]':
                # Look at top two coins in pile, returning them in any order
                pile.play_coin(coin)
                coins = []
                for index in range(2):
                    coin = pile.get_coin()
                    if coin:
                        print(f'  Coin {index+1} is: {coin}: {COINS[coin]}')
                        coins.append(coin)
                if len(coins) > 1:
                    print('Now choose the order to put them back on top.')
                    print('Which coin should be put on top first?')
                    print('(other coin will be placed on top of that one.)')
                elif len(coins) == 1:
                    print('There is only one coin left; it will be put back.')
                if coins:
                    coin = select_from_list(coins)
                    coins.insert(0, coin)
                    for coin in coins:
                        pile.put_coin(coin)
                else:
                    print('There were no coins in the pile to see!')
                coin = None
            elif coin == '[mirror]':
                # Re-use any coin in play, if there are any
                if pile.in_play:
                    coin2 = select_from_list(pile.in_play)
                else:
                    print('There are no coins in play!')
                    coin2 = None
                pile.play_coin(coin)
                coin = coin2
            elif coin == '[raven]':
                # Look at an opponent's coin, if they have one
                pile.play_coin(coin)
                p_oth = select_player(players, p_cur)
                if not p_oth.shield:
                    ### show opponent coin
                    p_oth.show_coin()
                    p_oth.add_note(f'{p_cur.name} saw your hand')
                else:
                    print(f'{p_oth.name} is shielded!')
                coin = None
            elif coin == '[rope]':
                # Look at bottom coin of pile and optionally move it to the top
                pile.play_coin(coin)
                if pile.coins:
                    bottom = pile.coins[-1]
                    print(f'Bottom of pile: {bottom}: {COINS[bottom]}')
                    answer = input(f'Move {bottom} to the top of pile? (y/n) ')
                    if answer.lower() in ('y', 'yes'):
                        pile.remove_coin(bottom)
                        pile.put_coin(bottom)
                else:
                    print('There are no coins in the pile!')
                coin = None
            elif coin == '[shield]':
                # Protects player from effects of coins except wind, shovel
                pile.play_coin(coin)
                p_cur.enable_shield()
                coin = None
            elif coin == '[shovel]':
                # Bury a coin in play under pile, removing its effect
                print('Which in-play coin would you like to bury?')
                coin2 = select_from_list(pile.in_play)
                pile.play_coin(coin)
                if coin2:
                    print(f'You bury {coin2}: {COINS[coin2]}')
                    pile.bury_coin(coin2)
                    if coin2 == '[shield]':
                        for player in players:
                            player.disable_shield()
                    add_notes(f'{p_cur.name} buried {coin2}', players, p_cur)
                else:
                    print('There are no coins in play!')
                coin = None
            elif coin == '[sickle]':
                # Put an opponent's coin in play without any effect
                pile.play_coin(coin)
                p_oth = select_player(players, p_cur)
                if not p_oth.shield:
                    ### choose opponent coin
                    coin = p_oth.get_coin()
                    if coin:
                        print(f"You kill {p_oth.name}'s coin: {coin}")
                        pile.play_coin(coin)
                        p_oth.add_note(f'{p_cur.name} killed your {coin}')
                        coin = pile.get_coin()
                        if coin:
                            p_oth.add_note(f'You drew replacement: {coin}')
                            p_oth.add_coin(coin)
                else:
                    print(f'{p_oth.name} is shielded!')
                coin = None
            elif coin == '[wind]':
                # Shuffle all coins in play into the pile (except wind)
                pile.reintegrate()
                pile.shuffle_coins()
                pile.play_coin(coin)
                for player in players:
                    player.disable_shield()
                coin = None
            if ARGS.debug:
                validate_state(players, pile, coin)

        if pile.unlock_chest():
            print(f'*** {p_cur.name} wins! ***')
            game_over = True
        elif not go_again:
            print()
            p_cur.show_status()
            pile.show_coins('in_play')
            input(f'{p_cur.name}, press return to end your turn.')
    print('Thanks for playing.')


if __name__ == '__main__':
    ARGS = parse_args()
    main()
