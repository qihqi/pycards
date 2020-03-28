import random

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
        self._players = set()
        self._player_hands = {}
        self.status = 'NEW'
        self._turn_number = 0

    def visible_state(self):  # what everyone can see
        return {
            'players': self.players(),
            'table': self.table(),
            'deck_cards': len(self.deck),
            'turn_number': self._turn_number,
            'status': self.status,
        }


    def incr_turn_number(self):
        self._turn_number += 1

    def set_turn(self, player_name):
        pid = self._player_to_id[player_name]
        self._turn_number = pid

    def turn_number(self):
        return self._turn_number

    def new_player(self, name):
        if name not in self._player_hands:
            self._player_hands[name] = set()
        if name not in self._player_to_id:
            self._player_to_id[name] = len(self._player_to_id)
        self._players.add(name)

    def get_player_id(self, name):
        return self._player_to_id[name]

    def start(self, num_decks):
        self.deck = list(range(num_decks * self._num_cards))
        random.shuffle(self.deck)
        self.status = 'STARTED'
        self._turn_number = 0
        self._player_hands = {name: set() for name in self._players}

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
        return sorted(self._players, key=self._player_to_id.get)

    def remove_player(self, player):
        self._players.remove(player)

    def end_draw(self):
        self.status = 'PLAYING'


