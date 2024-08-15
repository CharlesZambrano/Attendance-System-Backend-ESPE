import json
import logging
import os

import cv2
import numpy as np
from deepface import DeepFace
from utils import detect_liveness

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

# Configurar el blueprint
recognize_bp = Blueprint('recognize', __name__)

DEEPFACE_DB_PATH = '/app/academic_staff_database'
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')

@recognize_bp.route('/recognize', methods=['POST'])
def recognize_faces():
    try:
        # Verificar si se ha enviado un archivo de imagen
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

        # Verificar si se proporcionan las coordenadas de los rostros
        if 'faces' not in request.form:
            logger.error("No se proporcionaron las coordenadas de los rostros en la solicitud.")
            return jsonify({"error": "No se proporcionaron las coordenadas de los rostros."}), 400

        try:
            faces = json.loads(request.form['faces'])
        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar JSON: {str(e)}")
            return jsonify({"error": "Las coordenadas de los rostros no están en un formato JSON válido."}), 400

        if not faces:
            logger.error("La lista de rostros proporcionada está vacía.")
            return jsonify({"error": "No se proporcionaron rostros para reconocer."}), 400

        match_counts = {}  # Diccionario para contar coincidencias por identidad

        for face in faces:
            x1, y1, x2, y2 = face.get('x1'), face.get('y1'), face.get('x2'), face.get('y2')

            # Validar que las coordenadas existan y sean enteros
            if None in [x1, y1, x2, y2]:
                logger.error(f"Coordenadas incompletas o inválidas para el rostro: {face}")
                continue

            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # Asegurarse de que las coordenadas estén dentro de los límites de la imagen
            x1, y1 = max(x1, 0), max(y1, 0)
            x2, y2 = min(x2, img.shape[1] - 1), min(y2, img.shape[0] - 1)

            if x1 >= x2 or y1 >= y2:
                logger.error(f"Coordenadas inválidas después de la validación para el rostro: {face}")
                continue

            # Recortar la región de la imagen donde está el rostro
            face_img = img[y1:y2, x1:x2]

            if not detect_liveness(face_img, eye_cascade):
                logger.info("No se detectó vida en el rostro.")
                return jsonify({"identities": ["No se detectó un rostro real."]})

            # Preprocesamiento opcional: redimensionar el rostro para estandarizar (por ejemplo, a 224x224)
            face_img_resized = cv2.resize(face_img, (224, 224))

            # Realizar el reconocimiento facial usando "Facenet512"
            try:
                results = DeepFace.find(face_img_resized, db_path=DEEPFACE_DB_PATH, model_name="Facenet512", enforce_detection=False)
                if results and isinstance(results, list):
                    for df in results:
                        if not df.empty:
                            for _, row in df.iterrows():
                                identity = row.get('identity', '')
                                if identity:
                                    identity_name = os.path.basename(os.path.dirname(identity))
                                    match_counts[identity_name] = match_counts.get(identity_name, 0) + 1
                        else:
                            logger.info("No se encontraron coincidencias para el rostro actual.")
                else:
                    logger.info("DeepFace no devolvió resultados para el rostro actual.")
            except Exception as e:
                logger.exception(f"Error en el reconocimiento facial: {str(e)}")
                continue  # Continuar con el siguiente rostro en caso de error

        # Determinar la identidad con el mayor número de coincidencias
        if match_counts:
            recognized_identity = max(match_counts, key=match_counts.get)
            response = {"identities": [recognized_identity]}
        else:
            response = {"identities": ["Desconocido"]}

        logger.info(f"/recognize response: {response}")
        return jsonify(response), 200

    except Exception as e:
        logger.exception(f"Error en /recognize: {str(e)}")
        return jsonify({"error": "Ocurrió un error interno en el servidor."}), 500
