import json
import uuid

import bottle
from pycards import game

class Player(object):
    pass

games = {}

@bottle.post('/game/<decks>')
def make_game(decks):
    global games
    g = game.Game()
    g.start(int(decks))
    uid = uuid.uuid4().hex
    games[uid] = g
    return uid


@bottle.post('/game/<game_id>/player/<name>')
def new_player(game_id, name):
    g = games[game_id]
    p = Player()
    p.uid = uuid.uuid4().hex
    p.name = name
    g.new_player(p)
    return {'pid': p.uid}



@bottle.get('/game/<game_id>/player/<player_id>')
def get_player_view(game_id, player_id):
    return games[game_id].get_state(player_id)


@bottle.post('/game/<game_id>/player/<player_id>/draw')
def draw(game_id, player_id):
    g = games[game_id]
    cards = g.draw(player_id, 1)
    return json.dumps(cards)


@bottle.post('/game/<game_id>/player/<player_id>/play')
def play(game_id, player_id, card_id):
    card_id = json.loads(bottle.requests.body.read())['card_id']
    g = games[game_id]
    cards = g.play(player_id, card_id)
    return {'status': 'success'}


if __name__ == '__main__':
    bottle.run(host='localhost', port=8080)


