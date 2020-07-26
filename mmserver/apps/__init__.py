import os

from engineio.payload import Payload
from flask import Flask
from flask_socketio import SocketIO

Payload.max_decode_packets = 512
socketio = SocketIO()


def create_app(debug=False):
    app = Flask(__name__)
    app.debug = debug
    app.secret_key = os.urandom(8)

    socketio.init_app(app)
    return app
