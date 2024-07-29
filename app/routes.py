# app/routes.py

import os

from flask import jsonify, request
from some_facial_recognition_library import \
    process_image  # Reemplaza con la biblioteca que utilices
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/app/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({"message": "File uploaded successfully"}), 200
    else:
        return jsonify({"error": "File type not allowed"}), 400


# app/routes.py


@app.route('/process', methods=['POST'])
def process_recognition():
    data = request.get_json()
    image_path = data.get('image_path')
    if not image_path:
        return jsonify({"error": "Image path is required"}), 400
    result = process_image(image_path)
    return jsonify({"result": result}), 200


# app/routes.py

@app.route('/results/<image_id>', methods=['GET'])
def get_results(image_id):
    # Supón que guardas los resultados en una base de datos o archivo
    # Implementa esta función según tu almacenamiento
    result = get_result_from_storage(image_id)
    if result:
        return jsonify(result), 200
    else:
        return jsonify({"error": "Result not found"}), 404


# app/routes.py

@app.route('/register', methods=['POST'])
def register_person():
    data = request.get_json()
    person_name = data.get('name')
    image_path = data.get('image_path')
    if not person_name or not image_path:
        return jsonify({"error": "Name and image path are required"}), 400
    # Procesa la imagen y registra a la persona en la base de datos
    register_new_person(person_name, image_path)  # Implementa esta función
    return jsonify({"message": "Person registered successfully"}), 200
