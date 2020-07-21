from flask import (Blueprint, Flask, Response, redirect, render_template,
                   request, url_for)

from .apps import create_app, socketio
from .apps.mmv1 import app as mmv1_app

app = create_app(debug=True)
app.template_folder = '../templates'
app.static_folder = '../static'

main_bp = Blueprint('main', __name__)
app.register_blueprint(main_bp)

# other blueprints
app.register_blueprint(mmv1_app, url_prefix='/mmv1')


@app.route('/')
def index():
    return redirect(url_for('mmv1.index'))


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080)
