import os
import subprocess

from flask import Blueprint, Flask, jsonify, request
from werkzeug.utils import secure_filename

routes_app = Blueprint('routes_app', __name__)

UPLOAD_FOLDER = '/app/uploads'
MODEL_FOLDER = '/app/models'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def create_folders():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(MODEL_FOLDER):
        os.makedirs(MODEL_FOLDER)


create_folders()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@routes_app.route('/upload-dataset', methods=['POST'])
def upload_file():
    dataset_name = request.form.get('dataset_name')
    if not dataset_name:
        return jsonify({"error": "Dataset name is required"}), 400

    dataset_folder = os.path.join(UPLOAD_FOLDER, dataset_name)
    if not os.path.exists(dataset_folder):
        os.makedirs(dataset_folder)

    if 'files' not in request.files:
        return jsonify({"error": "No file part"}), 400
    files = request.files.getlist('files')
    for file in files:
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(dataset_folder, filename))
    return jsonify({"message": "Files uploaded successfully"}), 200


@routes_app.route('/train-model', methods=['POST'])
def train_model():
    data = request.get_json()
    dataset_name = data.get('dataset_name')
    if not dataset_name:
        return jsonify({"error": "Dataset name is required"}), 400

    dataset_folder = os.path.join(UPLOAD_FOLDER, dataset_name)
    if not os.path.exists(dataset_folder):
        return jsonify({"error": "Dataset folder does not exist"}), 400

    try:
        # Comando para ejecutar el entrenamiento con TAO Toolkit
        training_command = [
            'tao', 'facenet', 'train',
            # Ruta a tu archivo de especificación de entrenamiento
            '-e', '/app/specs/train_spec.cfg',
            '-r', MODEL_FOLDER,
            '-k', 'tu_clave_tao',  # Clave de usuario del TAO Toolkit
            '-d', dataset_folder,
            '--gpus', 'all'
        ]
        result = subprocess.run(
            training_command, capture_output=True, text=True)

        if result.returncode != 0:
            return jsonify({"error": result.stderr}), 500

        return jsonify({"message": "Model training started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@routes_app.route('/process-recognition', methods=['POST'])
def process_recognition():
    data = request.get_json()
    image_path = data.get('image_path')
    if not image_path:
        return jsonify({"error": "Image path is required"}), 400

    try:
        # Comando para ejecutar la inferencia con TAO Toolkit
        inference_command = [
            'tao', 'detectnet_v2', 'inference',
            '-m', os.path.join(MODEL_FOLDER, 'model.etlt'),
            '-i', image_path,
            '-o', '/app/inference_output',
            '--output_label', '/app/inference_output/labels.txt',
            '--batch_size', '1'
        ]
        result = subprocess.run(
            inference_command, capture_output=True, text=True)

        if result.returncode != 0:
            return jsonify({"error": result.stderr}), 500

        return jsonify({"message": "Inference completed", "output": result.stdout}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@routes_app.route('/results/<image_id>', methods=['GET'])
def get_results(image_id):
    try:
        with open(f'/app/inference_output/labels.txt', 'r') as file:
            results = file.read()
        return jsonify({"image_id": image_id, "results": results}), 200
    except FileNotFoundError:
        return jsonify({"error": "Results not found"}), 404


@routes_app.route('/register', methods=['POST'])
def register_person():
    data = request.get_json()
    person_name = data.get('name')
    image_path = data.get('image_path')
    if not person_name or not image_path:
        return jsonify({"error": "Name and image path are required"}), 400
    # Aquí deberías implementar la lógica para registrar a una nueva persona
    return jsonify({"message": "Person registered successfully"}), 200
