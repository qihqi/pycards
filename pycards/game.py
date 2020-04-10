import json
import random
from dataclasses import dataclass
from typing import List, Dict, Set, Iterable, Optional, Tuple

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


class GameObj(object):
    _exposed: List[str]


@dataclass
class GameState(GameObj):

    _table: List[List[int]]
    _deck: List[int]
    _hands: Dict[str, Set[int]]
    _table_players: List[str]

    _exposed = ['table', 'deck_count']

    def __init__(self, num_decks: int, players: Iterable[str]):
        self._deck = list(range(num_decks * 54))
        self._table = []
        self._hands = {name: set() for name in players}
        self._table_players = []

    @property
    def deck_count(self) -> int:
        return len(self._deck)

    @property
    def table(self):
        return list(zip(self._table_players, self._table))

    def hand(self, name) -> Set[int]:
        return self._hands[name]

    def draw(self, name: str, count: int) -> List[int]:
        if count > len(self._deck):
            raise ValueError('draw to many')
        cards = self._deck[-count:]
        self._hands[name].update(cards)
        del self._deck[-count:]
        return cards

    def play(self, name: str, card_ids: Iterable[int]) -> Set[int]:
        card_ids = set(card_ids)
        if not card_ids:
            return card_ids
        played = self._hands[name] & card_ids
        self._table.append(list(played))
        self._table_players.append(name)
        self._hands[name] -= played
        return played

    def take_back(self, name: str, card_ids: Iterable[int]) -> Set[int]:
        cards = set(card_ids)
        removed_cards = set()
        for ll in self._table:
            for k in ll:
                if k in cards:
                    ll.remove(k)
                    removed_cards.add(k)
        self._table = list(filter(None, self._table))
        self._hands[name].update(removed_cards)
        return removed_cards

    def return_to_deck(self, name: str, card_ids: Iterable[int]) -> Set[int]:
        card_ids = self._hands[name] & set(card_ids)
        self._hands[name] -= card_ids
        self._deck.extend(card_ids)
        return card_ids

    def clean_table(self):
        self._table = []
        self._table_players = []

    def deal(self, number) -> List[int]:
        if not self._deck:
            return []
        if number >= len(self._deck):
            number = len(self._deck)
        res = self._deck[-number:]
        self._table.append(res)
        del self._deck[-number:]
        return res


@dataclass
class Player(GameObj):
    name: str
    team: int
    score: int = 0
    total_score: int = 0

    _exposed = ['name', 'team', 'score', 'total_score']


class GameRoom(GameObj):

    players: List[Player] = []
    game: Optional[GameState] = None
    observers: List[Player] = []
    _current_turn: int = 0
    _last_turns: List[Tuple[str, List[int]]] = []

    _exposed = ['players', 'game', 'observers', 'current_player']


    def new_game(self, num_decks):
        self.players += self.observers
        self.observers = []
        self.game = GameState(num_decks, [p.name for p in self.players])
        self._current_turn = 0
        self._last_turns = []

    def set_turn(self, player):
        self._current_turn = self.players.index(player)

    def end_turn(self, player):
        if player == self.current_player:
            self._current_turn += 1
            self._current_turn %= len(self.players)

    @property
    def current_player(self):
        if self.players:
            return self.players[self._current_turn]
        return None

    def handle_command(self, player: Player, command: str, arg_dict: Dict):
        return_val = None  # type: object
        if command == 'JOIN':
            self.observers.append(player)
        elif command == 'START':
            self.new_game(arg_dict['num_decks'])
        elif command == 'DRAW':
            assert self.game
            return_val = {'drawed': self.game.draw(player.name, arg_dict['num_cards'])}
        elif command == 'CLEAN_TABLE':
            assert self.game
            self.game.clean_table()
        elif command == 'PLAY':
            assert self.game
            self.game.play(player.name, arg_dict['cards'])
        elif command == 'TAKE_BACK':
            assert self.game
            self.game.take_back(player.name, arg_dict['cards'])
        elif command == 'END_TURN':
            assert self.game
            self.end_turn(player)
        elif command == 'RETURN_TO_DECK':
            assert self.game
            self.game.return_to_deck(player.name, arg_dict['cards'])
        elif command == 'TAKE_TURN':
            assert self.game
            self.set_turn(player)
        elif command == 'DEAL':
            assert self.game
            self.game.deal(arg_dict['num_cards'])
        elif command == 'ADD_POINTS':
            player.score += arg_dict['points']
        elif command == 'GET_STATE':
            return_val = self
        else:
            raise ValueError('{} is not valid command'.format(command))
        return return_val


class ModelEncoder(json.JSONEncoder):

    def __init__(self, use_int_repr=False, decimal_places=2, *args, **kwargs):
        super(ModelEncoder, self).__init__(*args, **kwargs)
        self.use_int_repr = use_int_repr
        self.decimal_places = decimal_places

    def default(self, obj):
        if isinstance(obj, GameObj):
            res = {key: getattr(obj, key) for key in obj._exposed if not key.startswith('_')}
            return res
        return super(ModelEncoder, self).default(obj)






