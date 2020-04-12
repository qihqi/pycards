import asyncio
import json
import aiohttp
import aiohttp_jinja2
from aiohttp import web
import jinja2

from typing import Dict
from dataclasses import dataclass, field

from pycards import game

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
    room: game.GameRoom = game.GameRoom()


async def index(request):
    ws_current = web.WebSocketResponse()
    ws_ready = ws_current.can_prepare(request)

    if not ws_ready.ok:
        return aiohttp_jinja2.render_template('index.html', request, {})

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
                    if current_player in state.room.players:
                        if state.room.game:
                            reply_result = {
                                'name': '',
                                'action': 'SET_STATE',
                                'arg': {
                                    'hand': state.room.game.hand(name)
                                }
                            }
                    else:
                        if current_player not in state.room.observers:
                            state.room.observers.append(current_player)
                    broadcast = {
                        'name': '',
                        'action': 'SET_STATE',
                        'arg': {
                            'room': state.room,
                        }
                    }
                elif action == 'SPREAD_CARDS':
                    count = int(arg)
                    await spread_cards(state.room.game, state.ws_by_name, count)
                elif action == 'MESSAGE':
                    broadcast['msg'] = arg
                else:
                    assert new_name is None or current_player.name == new_name
                    reply_result, broadcast = state.room.handle_command(current_player, action, arg)
            except ValueError as e:
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

    del state.ws_by_name[current_player.name]
    to_send = []
    for ws in state.ws_by_name.values():
        to_send.append(ws.send_json({'player_left': current_player.name}))
    await asyncio.gather(*to_send)

    return ws_current


async def init_app():
    app = web.Application()
    app['state'] = State()
    app.on_shutdown.append(shutdown)
    aiohttp_jinja2.setup(
            app, loader=jinja2.FileSystemLoader('templates'))  # directories relative
    app.router.add_get('/', index)
    app.router.add_routes([web.static('/static', 'static')])
    return app


async def shutdown(app):
    for ws in app['state'].ws_by_name.values():
        await ws.close()
    app['state'].ws_by_name.clear()


def main():
    app = init_app()
    web.run_app(app)


if __name__ == '__main__':
    main()
