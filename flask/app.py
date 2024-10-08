from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask_cors import CORS
from routes.appuser import appuser_bp
from routes.class_schedule import class_schedule_bp
from routes.class_schedule_attendance import class_schedule_attendance_bp
from routes.create_embedding import embedding_bp
from routes.detect import detect_bp
from routes.professor import professor_bp
from routes.recognize import recognize_bp
from routes.role import role_bp
from routes.work_schedule import work_schedule_bp

from flask import Flask, jsonify

app = Flask(__name__)
CORS(app)

# Configuración de APISpec
spec = APISpec(
    title="Documentación de APIs",
    version="1.0.0",
    openapi_version="3.0.2",
    plugins=[FlaskPlugin(), MarshmallowPlugin()],
)

# Registrar los blueprints
app.register_blueprint(detect_bp)
app.register_blueprint(recognize_bp)
app.register_blueprint(embedding_bp)
app.register_blueprint(appuser_bp)
app.register_blueprint(role_bp)
app.register_blueprint(professor_bp)
app.register_blueprint(work_schedule_bp)
app.register_blueprint(class_schedule_attendance_bp)
app.register_blueprint(class_schedule_bp)

# Registrar los endpoints en APISpec
with app.test_request_context():
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            view_func = app.view_functions[rule.endpoint]
            spec.path(view=view_func)

# Endpoint para acceder a la documentación Swagger


@app.route("/swagger.json")
def swagger_json():
    return jsonify(spec.to_dict())


if __name__ == '__main__':
    import logging
    import time

    from utils import clean_directory, detect_directory_changes

    # Configuración de logging para mostrar más detalles
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    DEEPFACE_DB_PATH = '/app/academic_staff_database'

    # Detectar si hay cambios en el directorio y limpiar si es necesario
    last_mod_time = detect_directory_changes(DEEPFACE_DB_PATH)
    clean_directory(DEEPFACE_DB_PATH)

    # Continuamente revisar si hay cambios en el directorio
    while True:
        current_mod_time = detect_directory_changes(DEEPFACE_DB_PATH)
        if current_mod_time > last_mod_time:
            logger.info(
                "Cambios detectados en la base de datos. Ejecutando limpieza de nombres de archivos.")
            clean_directory(DEEPFACE_DB_PATH)
            last_mod_time = current_mod_time
        time.sleep(5)

    # Habilitar modo debug
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
