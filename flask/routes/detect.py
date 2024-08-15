import logging
import os

import cv2
import numpy as np
from ultralytics import YOLO

from flask import Blueprint, jsonify, request

# Configuración del logger
logger = logging.getLogger(__name__)

# Configurar el blueprint
detect_bp = Blueprint('detect', __name__)

# Ruta del modelo YOLOv8
YOLO_MODEL_PATH = '/app/yolov8x-face-lindevs.pt'
MIN_CONFIDENCE = 0.8

# Verificar si el modelo existe
if not os.path.exists(YOLO_MODEL_PATH):
    logger.error(f"El modelo YOLO no se encontró en la ruta: {YOLO_MODEL_PATH}")
    raise FileNotFoundError(f"El modelo YOLO no se encontró en la ruta: {YOLO_MODEL_PATH}")

# Cargar el modelo YOLOv8
model = YOLO(YOLO_MODEL_PATH)

@detect_bp.route('/detect', methods=['POST'])
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

        # Leer el parámetro opcional save_image
        save_image = request.form.get('save_image', 'false').lower() == 'true'

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

        response = {"faces": [best_face]} if best_face else {"faces": []}

        if best_face and save_image:
            # Dibujar un rectángulo alrededor del rostro en la imagen original
            x1, y1, x2, y2 = best_face['x1'], best_face['y1'], best_face['x2'], best_face['y2']
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

            # Opcional: Dibujar puntos clave en el rostro (si los tienes)
            # Ejemplo de puntos clave ficticios
            landmarks = [(int(x1 + (x2 - x1) * 0.3), int(y1 + (y2 - y1) * 0.3)),
                         (int(x1 + (x2 - x1) * 0.7), int(y1 + (y2 - y1) * 0.3)),
                         (int(x1 + (x2 - x1) * 0.5), int(y1 + (y2 - y1) * 0.6))]

            for point in landmarks:
                cv2.circle(img, point, 5, (0, 0, 255), -1)

            # Guardar la imagen del rostro detectado con el rectángulo y puntos clave
            output_path = "/app/detected_face_with_landmarks.jpg"  # Cambia la ruta si lo deseas
            cv2.imwrite(output_path, img)
            logger.info(f"Imagen del rostro guardada en {output_path}")
            
            # Incluir la ruta de la imagen en la respuesta si se guardó
            response["image_path"] = output_path

        logger.info(f"/detect response: {response}")
        return jsonify(response), 200

    except Exception as e:
        logger.exception(f"Error en /detect: {str(e)}")
        return jsonify({"error": "Ocurrió un error interno en el servidor."}), 500