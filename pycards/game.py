import random

NUM_CARDS_PER_DECK = 54


class Game(object):

    def __init__(self, num_cards_per_deck=None):
        self._num_cards = num_cards_per_deck or NUM_CARDS_PER_DECK
        self.deck = []
        self.status = 'NEW'
        self._players = {}  # id -> player obj
        self._table = []
        self._player_hands = {}

    def new_player(self, player):
        if self.status != 'NEW':
            raise ValueError('')
        self._players[player.uid] = player
        self._player_hands[player.uid] = []

    def start(self, num_decks):
        self.deck = list(range(num_decks * self._num_cards))
        random.shuffle(self.deck)
        self._player_hands = {pid: [] for pid in self._players}

    def draw(self, player_id, count):
        if count > len(self.deck):
            raise ValueError('draw to many')
        cards = self.deck[-count:]
        self._player_hands[player_id].extend(cards)
        del self.deck[-count:]
        return cards

    def play(self, player_id, card_id):
        self._player_hands[player_id].remove(card_id)
        self._table.append(card_id)

    def clean_table(self):
        self._table = []

    def get_state(self, player_id):
        return  {
                'table': self._table,
                'hand': self._player_hands[player_id]
                }

