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
        self._table = {}
        self._player_hands = {}

    def new_player(self, name):
        self._player_hands[name] = set()
        self._table[name] = []

    def start(self, num_decks):
        self.deck = list(range(num_decks * self._num_cards))
        random.shuffle(self.deck)

    def draw(self, player_id, count):
        if count > len(self.deck):
            raise ValueError('draw to many')
        cards = self.deck[-count:]
        self._player_hands[player_id].update(cards)
        del self.deck[-count:]
        return cards

    def play(self, player_id, card_ids):
        for c in card_ids:
            print(c)
            self._player_hands[player_id].remove(c)
            self._table[player_id].append(c)

    def clean_table(self):
        for l in self._table.values():
            del l[:]

    def get_hand(self, player_id):
        return list(map(get_card, self._player_hands[player_id]))

    def table(self):
        res = []
        for k, v in self._table.items():
            res.append((k, list(map(get_card, v))))
        return res

    def players(self):
        return list(self._player_hands.keys())

    def remove_player(self, player):
        del self._player_hands[player]
