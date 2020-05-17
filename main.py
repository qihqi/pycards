import argparse
import asyncio
import json
import aiohttp
import aiohttp_jinja2
from aiohttp import web
import jinja2

from typing import Dict
from dataclasses import dataclass, field

from pycards import game

parser = argparse.ArgumentParser(description='dapai')
parser.add_argument('--port')


def json_dumps(content):
    return json.dumps(content, cls=game.ModelEncoder)


async def spread_cards(game, sockets, cards):
    for i in range(cards):
        if not game.deck_count:
            break
        waitables = []
        for name, ws in sockets.items():
            cards = game.draw(name, 1)
            waitables.append(ws.send_json({
                'action': 'DRAWED',
                'arg': cards,
                'name': name,
            }))
        await asyncio.gather(*waitables)
        await asyncio.sleep(1)


# things I need to in app context
@dataclass
class State(object):
    players: Dict[str, game.Player] = field(default_factory=dict)
    ws_by_name: Dict[str, object] = field(default_factory=dict)
    rooms_by_name: Dict[str, game.GameRoom] = field(default_factory=dict)
    # player name -> the room its in.
    player_to_room: Dict[str, game.GameRoom] = field(default_factory=dict)


async def index(request):
    return web.FileResponse('static/index2.html')


async def ws_handler(request):
    ws_current = web.WebSocketResponse()
    ws_ready = ws_current.can_prepare(request)

    if not ws_ready.ok:
        return web.Response(status=400)

    # Does this means I have connected in js?
    await ws_current.prepare(request)
    state = request.app['state']
    current_player = None

    while True:
        msg = await ws_current.receive()
        broadcast = {}
        reply_result = {}
        if msg.type == aiohttp.WSMsgType.text:
            try:
                parsed = json.loads(msg.data)
                new_name, action, arg = parsed.get('name'), parsed['action'], parsed['arg']
                print(new_name, action, arg)
                if action == 'NEW_PLAYER':
                    name = new_name
                    state.ws_by_name[name] = ws_current
                    if name in state.players:
                        current_player = state.players[name]
                    else:
                        current_player = game.Player(name, 0)
                        state.players[name] = current_player
                elif action == 'SPREAD_CARDS':
                    count = int(arg)
                    room = state.player_to_room[current_player.name]
                    await spread_cards(room.game, state.ws_by_name, count)
                elif action == 'MESSAGE':
                    broadcast = {
                        'name': current_player.name,
                        'action': 'MESSAGE',
                        'arg': arg
                    }
                    if arg.startswith('!'):
                        try:
                            score = int(arg[1:])
                            room = state.player_to_room[current_player.name]
                            reply, broad = room.handle_command(
                                    current_player, 'ADD_POINTS', {'points': score})
                            to_send = []
                            for ws in state.ws_by_name.values():
                                to_send.append(ws.send_json(broad, dumps=json_dumps))
                            asyncio.gather(*to_send)
                        except Exception as e:
                            print(e)

                elif action == 'NEW_ROOM':
                    if arg in state.rooms_by_name:
                        reply_result = {
                            'name': '',
                            'action': 'SET_STATE',
                            'arg': {}
                        }
                    else:
                        room = game.GameRoom(name)
                        state.rooms_by_name[arg] = room
                        state.player_to_room[name] = room
                        broadcast = {
                            'name': '',
                            'action': 'SET_STATE',
                            'arg': {
                                'room': room,
                            }
                        }
                    room.observers.append(current_player)
                elif action == 'JOIN_ROOM':
                    room = state.rooms_by_name.get(arg)
                    if room is None:
                        raise ValueError('Room does not exist')
                    state.player_to_room[name] = room
                    if current_player in room.players:
                        if room.game:
                            reply_result = {
                                'name': '',
                                'action': 'SET_STATE',
                                'arg': {
                                    'hand': state.room.game.hand(name)
                                }
                            }
                    else:
                        if current_player not in room.observers:
                            room.observers.append(current_player)
                    broadcast = {
                        'name': '',
                        'action': 'SET_STATE',
                        'arg': {
                            'room': room,
                        }
                    }
                else:
                    assert new_name is None or current_player.name == new_name
                    if new_name:
                        room = state.player_to_room[current_player.name]
                        reply_result, broadcast = room.handle_command(current_player, action, arg)
            except Exception as e:
                print(e)
                import traceback
                traceback.print_exc()
                await ws_current.send_json({'error': str(e)})
            else:
                to_send = []
                if broadcast:
                    for ws in state.ws_by_name.values():
                        to_send.append(ws.send_json(broadcast, dumps=json_dumps))
                if reply_result:
                    to_send.append(ws_current.send_json(reply_result, dumps=json_dumps))
                await asyncio.gather(*to_send)
        else:
            break

    if current_player is not None:
        room = state.player_to_room.get(current_player.name)
        if room:
            room.leave_room(current_player)
    del state.ws_by_name[current_player.name]
    to_send = []
    print('PLAYER_LEFT', current_player.name)
    for ws in state.ws_by_name.values():
        to_send.append(ws.send_json({
            'name': current_player.name,
            'action': 'PLAYER_LEFT',
            'arg': ''
        }))
    await asyncio.gather(*to_send)

    return ws_current


async def init_app():
    app = web.Application()
    app['state'] = State()
    app.on_shutdown.append(shutdown)
    aiohttp_jinja2.setup(
            app, loader=jinja2.FileSystemLoader('templates'))  # directories relative
    app.router.add_get('/', index)
    app.router.add_get('/ws', ws_handler)
    app.router.add_routes([web.static('/static', 'static')])
    return app


async def shutdown(app):
    for ws in app['state'].ws_by_name.values():
        await ws.close()
    app['state'].ws_by_name.clear()


def main():
    app = init_app()
    args = parser.parse_args()
    web.run_app(app, port=args.port)


if __name__ == '__main__':
    main()
