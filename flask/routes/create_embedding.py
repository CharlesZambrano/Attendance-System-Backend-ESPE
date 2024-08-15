import json
import logging

import cv2
import numpy as np
from db_connection import insert_face_data
from deepface import DeepFace

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)
embedding_bp = Blueprint('create_embedding', __name__)

@embedding_bp.route('/create_embedding', methods=['POST'])
def create_embedding():
    try:
        if 'image' not in request.files:
            logger.error("No se proporcionó ningún archivo de imagen en la solicitud.")
            return jsonify({"error": "No se proporcionó ningún archivo de imagen."}), 400

        file = request.files['image'].read()
        if not file:
            logger.error("El archivo de imagen está vacío.")
            return jsonify({"error": "El archivo de imagen está vacío."}), 400

        np_img = np.frombuffer(file, np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        if img is None:
            logger.error("No se pudo decodificar la imagen. Asegúrate de que el archivo sea una imagen válida.")
            return jsonify({"error": "No se pudo decodificar la imagen."}), 400

        maestro_id = request.form.get('maestro_id')
        if not maestro_id:
            logger.error("No se proporcionó el ID del maestro en la solicitud.")
            return jsonify({"error": "El ID del maestro es requerido."}), 400

        embedding_objs = DeepFace.represent(img_path=img, model_name="Facenet512")
        if not embedding_objs:
            logger.error("No se pudo generar el embedding del rostro.")
            return jsonify({"error": "No se pudo generar el embedding del rostro."}), 500

        embedding = embedding_objs[0]['embedding']
        embedding_str = json.dumps(embedding)

        insert_face_data(maestro_id, file, embedding_str)

        response = {"message": "Embedding creado y almacenado con éxito."}
        return jsonify(response), 200

    except Exception as e:
        logger.exception(f"Error en /create_embedding: {str(e)}")
        return jsonify({"error": "Ocurrió un error interno en el servidor."}), 500
