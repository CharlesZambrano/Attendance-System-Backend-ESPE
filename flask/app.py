import json
import logging
import os

import cv2
import numpy as np
from deepface import DeepFace
from flask_cors import CORS
from ultralytics import YOLO

from flask import Flask, jsonify, request

app = Flask(__name__)
CORS(app)  # Habilitar CORS para aceptar solicitudes de cualquier origen

# Configuración del logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ruta del modelo YOLOv8
YOLO_MODEL_PATH = '/app/yolov8l-face-lindevs.pt'

# Verificar si el modelo existe
if not os.path.exists(YOLO_MODEL_PATH):
    logger.error(f"El modelo YOLO no se encontró en la ruta: {YOLO_MODEL_PATH}")
    raise FileNotFoundError(f"El modelo YOLO no se encontró en la ruta: {YOLO_MODEL_PATH}")

# Cargar el modelo YOLOv8
model = YOLO(YOLO_MODEL_PATH)

# Ruta de la base de datos de empleados para DeepFace
DEEPFACE_DB_PATH = '/app/employes_database'

# Verificar si la base de datos existe
if not os.path.exists(DEEPFACE_DB_PATH):
    logger.error(f"La base de datos de DeepFace no se encontró en la ruta: {DEEPFACE_DB_PATH}")
    raise FileNotFoundError(f"La base de datos de DeepFace no se encontró en la ruta: {DEEPFACE_DB_PATH}")

# Umbral mínimo de confianza para la detección de rostros
MIN_CONFIDENCE = 0.5

@app.route('/detect', methods=['POST'])
def detect_faces():
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

        # Detección de rostros con YOLO
        results = model(img)

        if not results or not results[0].boxes:
            logger.info("No se detectaron rostros en la imagen.")
            return jsonify({"faces": []}), 200

        # Extraer el rostro con la mayor confianza por encima del umbral
        best_face = None
        max_confidence = MIN_CONFIDENCE

        for result in results[0].boxes.data.cpu().numpy():
            x1, y1, x2, y2, conf, cls = result
            if conf > max_confidence:
                max_confidence = conf
                best_face = {
                    'x1': int(max(x1, 0)),
                    'y1': int(max(y1, 0)),
                    'x2': int(min(x2, img.shape[1] - 1)),
                    'y2': int(min(y2, img.shape[0] - 1)),
                    'confidence': float(conf),
                    'class': int(cls)
                }

        if best_face:
            response = {"faces": [best_face]}
        else:
            response = {"faces": []}

        logger.info(f"/detect response: {response}")
        return jsonify(response), 200

    except Exception as e:
        logger.exception(f"Error en /detect: {str(e)}")
        return jsonify({"error": "Ocurrió un error interno en el servidor."}), 500

@app.route('/recognize', methods=['POST'])
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

            # Preprocesamiento opcional: redimensionar el rostro para estandarizar (por ejemplo, a 224x224)
            face_img_resized = cv2.resize(face_img, (224, 224))

            # Realizar el reconocimiento facial
            try:
                results = DeepFace.find(face_img_resized, db_path=DEEPFACE_DB_PATH, enforce_detection=False, silent=True)
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

if __name__ == '__main__':
    # Ejecutar la aplicación Flask en modo de producción con waitress
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000)