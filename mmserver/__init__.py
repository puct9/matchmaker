from flask import Blueprint, render_template

from .apps import create_app, socketio
from .apps.mmv1 import app as mmv1_app
from .apps.moneydraft import app as draftv1_app

app = create_app(debug=True)
app.template_folder = '../templates'
app.static_folder = '../static'

main_bp = Blueprint('main', __name__)
app.register_blueprint(main_bp)

# other blueprints
app.register_blueprint(mmv1_app, url_prefix='/mmv1')
app.register_blueprint(draftv1_app, url_prefix='/draftv1')


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080)
