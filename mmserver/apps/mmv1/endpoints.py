import json

from flask import (Blueprint, Flask, Response, redirect,
                   request, url_for)
from flask import render_template as _render_template

from .db import SimpleFsDB
from .teammaker import FriendMatcher, str2matcher

DB = SimpleFsDB()
app = Blueprint('mmv1', __name__, template_folder='templates')


def render_template(*args, **kwargs):
    # is this a hack or is it legit?
    # no idea!
    args = list(args)
    args[0] = 'mmv1_' + args[0]
    return _render_template(*args, **kwargs)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/create')
def create_prompt():
    return render_template('create_room.html')


@app.route('/create', methods=['POST'])
def create_go():
    players = [request.form.get(f'p{i + 1}').strip() for i in range(10)]
    if not all(players) or len(set(players)) != 10:
        return redirect(url_for('.index'))
    room_id = DB.create_room(players, request.form.get('mm_mode'))
    return redirect(url_for('.room_view', room_id=room_id))


@app.route('/room/<room_id>')
def room_view(room_id):
    info = DB.get_room_info(room_id)
    if info is None:
        return redirect(url_for('.index'))
    maxlen = max(len(p) for p in info['player_info'])
    fecpy = '\\n'.join(p + ' ' * (maxlen - len(p) + 2) + r
                      for r, p in info['response_ids'].items())
    return render_template('view_room.html', info=info, room_id=room_id,
                           all_ready=all(info['player_info'].values()),
                           copy_info=fecpy)


@app.route('/room/<room_id>/quickrespond')
def room_quickresponse(room_id):
    info = DB.get_room_info(room_id)
    if info is None:
        return redirect(url_for('.index'))
    return render_template('quickresponse.html', info=info, room_id=room_id)


@app.route('/api/suggest/<room_id>')
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
    matcher = str2matcher(info['mode'])()
    (t1, t2), bonus_info = matcher.generate_teams(prefs)
    team1 = [info['players'][x] for x in t1]
    team2 = [info['players'][x] for x in t2]
    return Response(json.dumps({'success': True, 'team1': team1,
                                'team2': team2, 'facts': bonus_info}),
                               mimetype='text/plain')


@app.route('/respond')
def respond_prompt():
    return render_template('respond_prompt.html',
                           error=request.args.get('error'))


@app.route('/respond/<response_id>')
def respond_page(response_id):
    if not DB.response_exists(response_id):
        return redirect(url_for('.respond_prompt', error='Bad response ID'))
    room_info = DB.get_room_info(DB.response_id_to_room(response_id))
    hint, extra, query, template, bonus = str2matcher(room_info['mode']
                                                      ).get_query(room_info,
                                                                  response_id)
    return render_template(template,
                           name=room_info['response_ids'][response_id],
                           hint=hint, extra=extra, query=query, bonus=bonus)


@app.route('/respond/<response_id>', methods=['POST'])
def respond_submit(response_id):
    if not DB.response_exists(response_id):
        return redirect(url_for('.respond_prompt', error='Bad response ID'))
    room_info = DB.get_room_info(DB.response_id_to_room(response_id))
    prefs = str2matcher(room_info['mode']).read_response(request.form)
    DB.set_response(response_id, prefs)
    return redirect(url_for('.respond_prompt', error='Done!'))
