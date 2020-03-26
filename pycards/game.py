import random

NUM_CARDS_PER_DECK = 54


def make_standard_deck():
    cards = []
    for suite in ('C', 'D', 'H', 'S'):
        for val in range(2, 15):
            cards.append((suite, val))
    cards.append(('JOKER', 1))
    cards.append(('JOKER', 2))
    return cards

STANDARD_DECK = make_standard_deck()

def get_card(cid):
    return {'id': cid, 'value': STANDARD_DECK[cid % 54]}


class Game(object):

    def __init__(self, num_cards_per_deck=None):
        self._num_cards = num_cards_per_deck or NUM_CARDS_PER_DECK
        self.deck = []
        self._table = []
        self._players = []
        self._player_hands = {}
        self.status = 'NEW'
        self._turn_number = 0

    def incr_turn_number(self):
        self._turn_number += 1

    def turn_number(self):
        return self._turn_number

    def new_player(self, name):
        self._players.append(name)
        if name not in self._player_hands:
            self._player_hands[name] = set()

    def start(self, num_decks):
        self.deck = list(range(num_decks * self._num_cards))
        random.shuffle(self.deck)
        self.status = 'STARTED'
        self._turn_number = 0
        self._player_hands = {name: set() for name in self._players}

    def draw(self, player_id, count):
        if count > len(self.deck):
            raise ValueError('draw to many')
        cards = self.deck[-count:]
        self._player_hands[player_id].update(cards)
        del self.deck[-count:]
        return cards

    def play(self, player_id, card_ids):
        card_ids = set(card_ids)
        print(card_ids)
        if not card_ids: 
            return
        self._player_hands[player_id] -= card_ids
        self._table.append((player_id, card_ids))

    def take_back(self, player_id, card_ids):
        cards = set(card_ids)
        for i, (k, v) in enumerate(self._table):
            v -= cards
            if not v:
                del self._table[i]
        self._player_hands[player_id].update(cards)

    def clean_table(self):
        del self._table[:]

    def get_hand(self, player_id):
        return list(map(get_card, self._player_hands[player_id]))

    def table(self):
        res = []
        for k, v in self._table:
            res.append((k, list(map(get_card, v))))
        return res

    def players(self):
        return self._players

    def remove_player(self, player):
        self._players.remove(player)

