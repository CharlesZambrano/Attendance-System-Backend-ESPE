from flask import Flask

from .routes import routes_app


def create_app():
    app = Flask(__name__)
    app.config['UPLOAD_FOLDER'] = '/app/uploads'

    with app.app_context():
        app.register_blueprint(routes_app)
        return app
