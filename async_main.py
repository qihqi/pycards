import json
import aiohttp
import aiohttp_jinja2
from aiohttp import web
import jinja2

from pycards import game

# messages are tuples:
# (DRAW, n)
# (PLAY, list-of-cards)

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
                if action == 'NEW_PLAYER':
                    request.app['websockets'][arg] = ws_current
                    g.new_player(arg)
                    name = arg
                    broadcast_result['players'] = g.players()
                    cur_result['table'] = g.table()
                    cur_result['hand'] = g.get_hand(name)
                elif action == 'START':
                    g.start(arg)
                    g.clean_table()
                elif action == 'DRAW':
                    g.draw(name, arg)
                    cur_result['hand'] = g.get_hand(name)
                elif action == 'CLEAN_TABLE':
                    g.clean_table()
                    broadcast_result['table'] = g.table()
                elif action == 'PLAY':
                    arg = map(int, arg)
                    g.play(name, arg)
                    broadcast_result['table'] = g.table()
                    cur_result['hand'] = g.get_hand(name)
                else:
                    raise ValueError('{} is not valid action'.format(action))
            except ValueError as e:
                print(e)
                import traceback
                traceback.print_exc()
                await ws_current.send_json({'error': str(e)})
            else:
                if broadcast_result:
                    for ws in request.app['websockets'].values():
                        await ws.send_json(broadcast_result)
                if cur_result:
                    await ws_current.send_json(cur_result)
        else:
            break

    del request.app['websockets'][name]
    g.remove_player(name)
    for ws in request.app['websockets'].values():
        await ws.send_json({'players': g.players() })

    return ws_current



async def init_app():
    app = web.Application()
    app['websockets'] = {}
    app['games'] = game.Game()
    app.on_shutdown.append(shutdown)
    aiohttp_jinja2.setup(
            app, loader=jinja2.FileSystemLoader('templates'))  # directories relative
    app.router.add_get('/', index)
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
