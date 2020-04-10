import json
import unittest
from pycards import game

class GameTest(unittest.TestCase):

    def test_game_state(self):
        g = game.GameState(2, ['a', 'b'])
        self.assertEqual(g.deck_count,  108)
        self.assertEqual(g.hand('a'), set())
        p = g.draw('a', 3)
        self.assertEqual(len(p), 3)
        self.assertEqual(g.hand('a'), set(p))
        self.assertEqual(g.deck_count, 105)
        g.play('a', p)
        self.assertEqual(g.hand('a'), set())
        self.assertEqual(g._table, [p])
        g.take_back('a', p[0:1])
        self.assertEqual(len(g._table[0]), 2)
        p2 = g.draw('a', 1)
        self.assertEqual(len(g.take_back('a', p2)), 0)
        p3 = g.return_to_deck('a', p2)
        self.assertCountEqual(p2, p3)

    def test_game_room(self):
        room = game.GameRoom()
        self.assertEqual(
            json.dumps(room, cls=game.ModelEncoder),
            '{"players": [], "game": null, "observers": [], "current_player": null}')
        player = game.Player('a', 0)
        room.handle_command(player, 'JOIN', {})
        print(json.dumps(room, cls=game.ModelEncoder))
        self.assertEqual(
            json.dumps(room, cls=game.ModelEncoder),
        '{"players": [], "game": null, "observers": [{"name": "a", "team": 0, "score": 0, "total_score": 0}], "current_player": null}')
        room.handle_command(player, 'START', {'num_decks': 2})
        res, _ = room.handle_command(player, 'DRAW', {'num_cards': 2})
        room.handle_command(player, 'PLAY', {'cards': res['drawed']})
        print(json.dumps(room, cls=game.ModelEncoder))


if __name__ == '__main__':
    unittest.main()
