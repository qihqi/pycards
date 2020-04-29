import itertools
import json
import random
from dataclasses import dataclass, field
from typing import List, Dict, Set, Iterable, Optional, Tuple

NUM_CARDS_PER_DECK = 54


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
        random.shuffle(self._deck)
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
        return self._hands.get(name, set())

    def draw(self, name: str, count: int) -> List[int]:
        if count > len(self._deck):
            raise ValueError('draw to many')
        cards = self._deck[-count:]
        self._hands[name].update(cards)
        del self._deck[-count:]
        return cards

    def play(self, name: str, card_ids: Iterable[int]) -> Set[int]:
        card_ids = set(card_ids)
        played = self._hands[name] & card_ids
        if played:
            self._table.append(list(played))
            self._table_players.append(name)
            self._hands[name] -= played
        return played

    def take_back(self, name: str, card_ids: Iterable[int]) -> Set[int]:
        cards = set(card_ids)  # cards to remove
        all_table_cards = set(itertools.chain(*self._table))
        cards = cards & all_table_cards
        self._table = [
            list(filter(lambda x: x not in cards, ll)) for ll in self._table
        ]
        self._hands[name].update(cards)

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
        self._table_players.append('DECK')
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

    players: List[Player] = field(default_factory=list)
    game: Optional[GameState] = None
    observers: List[Player] = field(default_factory=list)
    _current_turn: int = 0
    _last_turns: List[Tuple[str, List[int]]] = field(default_factory=list)

    _exposed = ['players', 'game', 'observers', 'current_player']

    def __init__(self):
        self.players = []
        self.observers = []
        self._last_turns = []

    def new_game(self, num_decks):
        self.players += self.observers
        if not self.players:
            return
        for p in self.players:
            p.score = 0
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

    def leave_room(self, player):
        if player == self.current_player:
            self.end_turn(player)
        try:
            self.players.remove(player)
        except ValueError:
            pass
        try:
            self.observers.remove(player)
        except ValueError:
            pass
        if not self.players:
            self.game = None

    @property
    def current_player(self):
        if self.players:
            return self.players[self._current_turn]
        return None

    def handle_command(self, player: Player, command: str, arg_dict: Dict):
        reply_result = None
        bcommand = command
        barg = arg_dict
        bname = player.name

        if command == 'START':
            self.new_game(arg_dict['num_decks'])
            bcommand = 'SET_STATE'
            barg = { 'room': self, 'hand': []}
        elif command == 'DRAW':
            assert self.game
            res = self.game.draw(player.name, arg_dict['num_cards'])
            reply_result = {
               'name': player.name,
               'action': 'DRAWED',
               'arg': res,
            }
        elif command == 'CLEAN_TABLE':
            assert self.game
            self.game.clean_table()
        elif command == 'PLAY':
            assert self.game
            cards = self.game.play(player.name, arg_dict['cards'])
            barg = {'cards': cards}
        elif command == 'TAKE_BACK':
            assert self.game
            self.game.take_back(player.name, arg_dict['cards'])
            bcommand = 'SET_STATE'
            barg = { 'room': self,}
            reply_result = {
                'name': player.name,
                'action': 'SET_STATE',
                'arg': { 'hand': self.game.hand(player.name) }
            }
        elif command == 'END_TURN':
            assert self.game
            self.end_turn(player)
            bcommand = 'TAKE_TURN'
            bname = self.current_player.name
        elif command == 'RETURN_TO_DECK':
            assert self.game
            cards = self.game.return_to_deck(player.name, arg_dict['cards'])
            barg = {'num_cards': len(cards)}
        elif command == 'TAKE_TURN':
            assert self.game
            self.set_turn(player)
        elif command == 'DEAL':
            assert self.game
            self.game.deal(arg_dict['num_cards'])
            bcommand = 'SET_STATE'
            barg = { 'room': self, 'hand': self.game.hand(player.name) }
        elif command == 'ADD_POINTS':
            player.score += arg_dict['points']
        elif command == 'GET_STATE':
            reply_result = {
                'name': player.name,
                'action': 'SET_STATE',
                'arg': {
                    'room': self,
                    'hand': self.game.hand(player.name)
                }
            }
        elif command == 'JOIN_GAME':
            if player not in self.players:
                self.players.append(player)
            try:
                self.observers.remove(player)
            except ValueError:
                pass
            reply_result = {
                'name': player.name,
                'action': 'SET_STATE',
                'arg': {
                    'room': self,
                    'hand': self.game.hand(player.name)
                }
            }
        else:
            raise ValueError('{} is not valid command'.format(command))

        broadcast_result = {
            'name': bname,
            'action': bcommand,
            'arg': barg
        }

        return reply_result, broadcast_result


class ModelEncoder(json.JSONEncoder):

    def __init__(self, use_int_repr=False, decimal_places=2, *args, **kwargs):
        super(ModelEncoder, self).__init__(*args, **kwargs)
        self.use_int_repr = use_int_repr
        self.decimal_places = decimal_places

    def default(self, obj):
        if isinstance(obj, GameObj):
            res = {key: getattr(obj, key) for key in obj._exposed if not key.startswith('_')}
            return res
        if isinstance(obj, set):
            return list(obj)
        return super(ModelEncoder, self).default(obj)
