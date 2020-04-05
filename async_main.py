import asyncio
import json
import aiohttp
import aiohttp_jinja2
from aiohttp import web
import jinja2

from pycards import game


async def spread_cards(game, sockets, cards):
    for i in range(cards):
        if not game.deck:
            break
        waitables = []
        for name, ws in sockets.items():
            game.draw(name, 1)
            waitables.append(ws.send_json( {
                'hand': game.get_hand(name) 
            }))
        await asyncio.gather(*waitables)
        await asyncio.sleep(1)



async def index(request):
    ws_current = web.WebSocketResponse()
    ws_ready = ws_current.can_prepare(request)

    if not ws_ready.ok:
        return aiohttp_jinja2.render_template('index.html', request, {})

    # Does this means I have connected in js?
    await ws_current.prepare(request)
    g = request.app['games']
    name = None

    while True:
        msg = await ws_current.receive()
        broadcast_result = {}
        cur_result = {}
        if msg.type == aiohttp.WSMsgType.text:
            try:
                parsed = json.loads(msg.data)
                action, arg = parsed['action'], parsed['arg']
                print(name, action, arg)
                if action == 'NEW_PLAYER':
                    request.app['websockets'][arg] = ws_current
                    g.new_player(arg)
                    name = arg
                    cur_result['player_id'] = g.get_player_id(name)
                    cur_result['hand'] = g.get_hand(name)
                elif action == 'START':
                    g.start(arg['num_decks'])
                    g.clean_table()
                    broadcast_result['draw_until'] = arg['draw_until']
                    broadcast_result['hand'] = []
                elif action == 'DRAW':
                    g.draw(name, arg)
                    cur_result['hand'] = g.get_hand(name)
                elif action == 'CLEAN_TABLE':
                    g.clean_table()
                elif action == 'PLAY':
                    arg = map(int, arg)
                    g.play(name, arg)
                    cur_result['hand'] = g.get_hand(name)
                elif action == 'TAKE_BACK':
                    arg = map(int, arg)
                    g.take_back(name, arg)
                    cur_result['hand'] = g.get_hand(name)
                elif action == 'END_TURN':
                    g.end_turn(name)
                elif action == 'RETURN_TO_DECK':
                    arg = list(map(int, arg))
                    g.return_to_deck(name, arg)
                    cur_result['hand'] = g.get_hand(name)
                elif action == 'END_DRAW':
                    g.end_draw()
                elif action == 'TAKE_TURN':
                    g.set_turn(name)
                elif action == 'MESSAGE':
                    broadcast_result['msg'] = arg
                elif action == 'SPREAD_CARDS':
                    count = int(arg)
                    await spread_cards(g, request.app['websockets'], count)
                elif action == 'DEAL':
                    count = int(arg)
                    g.deal(count)
                elif action == 'SET_POINTS':
                    broadcast_result['points'] = arg
                else:
                    raise ValueError('{} is not valid action'.format(action))
            except ValueError as e:
                print(e)
                import traceback
                traceback.print_exc()
                await ws_current.send_json({'error': str(e)})
            else:
                broadcast_result.update(g.visible_state())
                for ws in request.app['websockets'].values():
                    await ws.send_json(broadcast_result)
                if cur_result:
                    await ws_current.send_json(cur_result)
            print('result:', cur_result)
        else:
            break

    del request.app['websockets'][name]
    g.remove_player(name)
    for ws in request.app['websockets'].values():
        await ws.send_json({'players': g.players() })

    return ws_current


async def test(request):
    ws_current = web.WebSocketResponse()
    ws_ready = ws_current.can_prepare(request)

    assert ws_ready.ok

    # Does this means I have connected in js?
    await ws_current.prepare(request)
    request.app['websockets_test'].append(ws_current)
    while True:
        msg = await ws_current.receive()
        broadcast_result = {}
        cur_result = {}
        if msg.type == aiohttp.WSMsgType.text:
            parsed = json.loads(msg.data)
            action, arg = parsed['action'], parsed['arg']
            if action == 'VERBATIM':
                for w in request.app['websockets_test']:
                    if w != ws_current:
                        print('send', arg)
                        await w.send_json(arg)
        else:
            break
    pass



async def init_app():
    app = web.Application()
    app['websockets'] = {}
    app['websockets_test'] = []
    app['games'] = game.Game()
    app.on_shutdown.append(shutdown)
    aiohttp_jinja2.setup(
            app, loader=jinja2.FileSystemLoader('templates'))  # directories relative
    app.router.add_get('/', index)
    app.router.add_get('/test', test)
    app.router.add_routes([web.static('/static', 'static')])
    return app


async def shutdown(app):
    for ws in app['websockets'].values():
        await ws.close()
    app['websockets'].clear()


def main():
    app = init_app()
    web.run_app(app)


if __name__ == '__main__':
    main()
