import json
from base64 import b64decode

from flask import Flask, Response, redirect, render_template, request, url_for

from db import SimpleDB as LocalDB
from teammaker import FriendMatcher

DB = LocalDB()
APP = Flask(__name__)


@APP.route('/')
def index():
    return render_template('index.html')


@APP.route('/create')
def create_prompt():
    return render_template('create_room.html')


@APP.route('/create/<players_b64>')
def create_go(players_b64):
    players = b64decode(players_b64.encode()).decode().split(',')
    if len(set(players)) != 10:
        return redirect(url_for('.index'))
    room_id = DB.create_room(players)
    return redirect(url_for('.room_view', room_id=room_id))


@APP.route('/room/<room_id>')
def room_view(room_id):
    info = DB.get_room_info(room_id)
    if info is None:
        return redirect(url_for('.index'))
    return render_template('view_room.html', info=info, room_id=room_id,
                           all_ready=all(info['player_info'].values()))


@APP.route('/api/suggest/<room_id>')
def api_room_suggest(room_id):
    info = DB.get_room_info(room_id)
    if info is None:
        return Response(json.dumps({'success': False,
                                    'reason': 'Room does not exist'}),
                        mimetype='text/plain')
    if not all(info['player_info'].values()):
        return Response(json.dumps({'success': False,
                                    'reason': 'Not all players responded'}),
                        mimetype='text/plain')
    # do matching
    # prepare info for the matcher
    prefs = []
    for player in info['players']:
        prefs.append(info['player_info'][player])
    fm = FriendMatcher()
    (t1, t2), _ = fm.generate_teams(prefs)
    team1 = [info['players'][x] for x in t1]
    team2 = [info['players'][x] for x in t2]
    return Response(json.dumps({'success': True, 'team1': team1,
                                'team2': team2}), mimetype='text/plain')


@APP.route('/respond')
def respond_prompt():
    return render_template('respond_prompt.html',
                           error=request.args.get('error'))


@APP.route('/respond/<response_id>')
def respond_page(response_id):
    if not DB.response_exists(response_id):
        return redirect(url_for('.respond_prompt', error='Bad response ID'))
    room_id = DB.response_id_to_room(response_id)
    us = DB.response_id_to_player(response_id)
    them = DB.get_room_info(room_id)['players']
    them.remove(us)
    return render_template('respond_page.html',
                           name=us, others=them)


@APP.route('/respond/<response_id>', methods=['POST'])
def respond_submit(response_id):
    if not DB.response_exists(response_id):
        return redirect(url_for('.respond_prompt', error='Bad response ID'))
    _prefs = [request.form.get(f'p{i}') for i in range(1, 10)]
    # normalalise
    prefs = []
    for pref in _prefs:
        try:
            prefs.append(max(0, int(pref)))
        except ValueError:
            prefs.append(0)
    prefs_l1 = max(sum(prefs), 1e-3)  # avoid divide by zero
    prefs = [x / prefs_l1 for x in prefs]
    # insert ourselves as a 1 in the right spot
    players = DB.get_room_info(DB.response_id_to_room(response_id))['players']
    prefs.insert(players.index(DB.response_id_to_player(response_id)), 1)
    DB.set_response(response_id, prefs)
    return redirect(url_for('.respond_prompt', error='Done!'))


if __name__ == '__main__':
    try:
        APP.run('0.0.0.0', 80, True)
    except PermissionError:
        _PORT = int(os.environ.get('PORT', 17995))
        APP.run('0.0.0.0', _PORT, False)
