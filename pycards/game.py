import random
from dataclasses import dataclass
from typing import List, Dict, Set

NUM_CARDS_PER_DECK = 54


def make_standard_deck():
    cards = []
    for suite in ('C', 'D', 'H', 'S'):
        for val in range(2, 15):
            cards.append((suite, val))
    cards.append(('JOKER', 20))
    cards.append(('JOKER', 21))
    return cards

STANDARD_DECK = make_standard_deck()

def get_card(cid):
    return {'id': cid, 'value': STANDARD_DECK[cid % 54]}


class Game(object):

    # Status: NEW -> STARTED -> PLAYING

    def __init__(self, num_cards_per_deck=None):
        self._num_cards = num_cards_per_deck or NUM_CARDS_PER_DECK
        self.deck = []
        self._table = []
        self._player_to_id = {}
        self._players = []
        self._player_hands = {}
        self.status = 'NEW'
        self._turn_number = 0
        self._current_player = None

    def visible_state(self):  # what everyone can see
        return {
            'players': self.players(),
            'table': self.table(),
            'deck_cards': len(self.deck),
            'current_player': self._current_player,
            'status': self.status,
        }


    def end_turn(self, player_name):
        if player_name == self._current_player:
            self._turn_number += 1
            self._turn_number = self._turn_number % len(self._players)
            self._current_player = self._players[self._turn_number]
            

    def set_turn(self, player_name):
        pid = self._player_to_id[player_name]
        self._turn_number = pid
        self._current_player = player_name

    def turn_number(self):
        return self._turn_number

    def current_player(self):
        return self._current_player

    def new_player(self, name):
        if name not in self._player_hands:
            self._player_hands[name] = set()
        if name not in self._player_to_id:
            self._player_to_id[name] = len(self._player_to_id)
        self._players.append(name)
        if self._current_player is None:
            self._current_player = name

    def get_player_id(self, name):
        return self._player_to_id[name]

    def start(self, num_decks):
        self.deck = list(range(num_decks * self._num_cards))
        random.shuffle(self.deck)
        self.status = 'STARTED'
        self._turn_number = 0
        self._player_hands = {name: set() for name in self._players}
        if self._players:
            self._current_player = self._players[0]

    def draw(self, name, count):
        if count > len(self.deck):
            raise ValueError('draw to many')
        cards = self.deck[-count:]
        self._player_hands[name].update(cards)
        del self.deck[-count:]
        return cards

    def play(self, name, card_ids):
        card_ids = set(card_ids)
        print(card_ids)
        if not card_ids: 
            return
        self._player_hands[name] -= card_ids
        self._table.append((name, card_ids))

    def take_back(self, name, card_ids):
        cards = set(card_ids)
        for i, (k, v) in enumerate(self._table):
            v -= cards
            if not v:
                del self._table[i]
        self._player_hands[name].update(cards)

    def return_to_deck(self, name, card_ids):
        self._player_hands[name] -= set(card_ids)
        self.deck.extend(card_ids)

    def clean_table(self):
        del self._table[:]

    def get_hand(self, name):
        return list(map(get_card, self._player_hands[name]))

    def table(self):
        res = []
        for k, v in self._table:
            res.append((k, list(map(get_card, v))))
        return res

    def players(self):
        return self._players

    def remove_player(self, player):
        self._players.remove(player)

    def end_draw(self):
        self.status = 'PLAYING'

    def deal(self, number):
        if not self.deck:
            return 
        if number >= len(self.deck):
            number = len(self.deck) - 1
        self._table.append(('DECK', set(self.deck[-number:])))
        del self.deck[-number:]


@dataclass
class GameState(object):

    deck: List[int]
    table: List[List[int]]
    hands: Dict[str, Set[int]]


    def visible_state(self):  # what everyone can see
        return {
            'players': self.players(),
            'table': self.table(),
            'deck_cards': len(self.deck),
            'current_player': self._current_player,
            'status': self.status,
        }


    def end_turn(self, player_name):
        if player_name == self._current_player:
            self._turn_number += 1
            self._turn_number = self._turn_number % len(self._players)
            self._current_player = self._players[self._turn_number]
            

    def set_turn(self, player_name):
        pid = self._player_to_id[player_name]
        self._turn_number = pid
        self._current_player = player_name

    def turn_number(self):
        return self._turn_number

    def current_player(self):
        return self._current_player

    def new_player(self, name):
        if name not in self._player_hands:
            self._player_hands[name] = set()
        if name not in self._player_to_id:
            self._player_to_id[name] = len(self._player_to_id)
        self._players.append(name)
        if self._current_player is None:
            self._current_player = name

    def get_player_id(self, name):
        return self._player_to_id[name]

    def start(self, num_decks):
        self.deck = list(range(num_decks * self._num_cards))
        random.shuffle(self.deck)
        self.status = 'STARTED'
        self._turn_number = 0
        self._player_hands = {name: set() for name in self._players}
        if self._players:
            self._current_player = self._players[0]

    def draw(self, name, count):
        if count > len(self.deck):
            raise ValueError('draw to many')
        cards = self.deck[-count:]
        self._player_hands[name].update(cards)
        del self.deck[-count:]
        return cards

    def play(self, name, card_ids):
        card_ids = set(card_ids)
        print(card_ids)
        if not card_ids: 
            return
        self._player_hands[name] -= card_ids
        self._table.append((name, card_ids))

    def take_back(self, name, card_ids):
        cards = set(card_ids)
        for i, (k, v) in enumerate(self._table):
            v -= cards
            if not v:
                del self._table[i]
        self._player_hands[name].update(cards)

    def return_to_deck(self, name, card_ids):
        self._player_hands[name] -= set(card_ids)
        self.deck.extend(card_ids)

    def clean_table(self):
        del self._table[:]

    def get_hand(self, name):
        return list(map(get_card, self._player_hands[name]))

    def table(self):
        res = []
        for k, v in self._table:
            res.append((k, list(map(get_card, v))))
        return res

    def players(self):
        return self._players

    def remove_player(self, player):
        self._players.remove(player)

    def end_draw(self):
        self.status = 'PLAYING'

    def deal(self, number):
        if not self.deck:
            return 
        if number >= len(self.deck):
            number = len(self.deck) - 1
        self._table.append(('DECK', set(self.deck[-number:])))
        del self.deck[-number:]



