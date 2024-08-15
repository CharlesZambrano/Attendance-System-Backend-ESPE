from flask_cors import CORS
from routes.create_embedding import embedding_bp
from routes.detect import detect_bp
from routes.recognize import recognize_bp

from flask import Flask

app = Flask(__name__)
CORS(app)

# Registrar los blueprints
app.register_blueprint(detect_bp)
app.register_blueprint(recognize_bp)
app.register_blueprint(embedding_bp)

if __name__ == '__main__':
    import logging
    import time

    from utils import clean_directory, detect_directory_changes

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    DEEPFACE_DB_PATH = '/app/academic_staff_database'

    # Detectar si hay cambios en el directorio y limpiar si es necesario
    last_mod_time = detect_directory_changes(DEEPFACE_DB_PATH)
    clean_directory(DEEPFACE_DB_PATH)

    # Continuamente revisar si hay cambios en el directorio
    while True:
        current_mod_time = detect_directory_changes(DEEPFACE_DB_PATH)
        if current_mod_time > last_mod_time:
            logger.info("Cambios detectados en la base de datos. Ejecutando limpieza de nombres de archivos.")
            clean_directory(DEEPFACE_DB_PATH)
            last_mod_time = current_mod_time
        time.sleep(5)

    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)
