import json
import logging

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

# Cargar el modelo YOLOv8 desde el directorio correcto
model = YOLO('/app/yolov8l-face-lindevs.pt')

@app.route('/detect', methods=['POST'])
def detect_faces():
    try:
        # Recibir la imagen enviada desde el frontend
        file = request.files['image'].read()
        np_img = np.frombuffer(file, np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        
        # Detección de rostros con YOLO
        results = model(img)
        
        # Extraer el rostro con la mayor confianza
        best_face = None
        max_confidence = 0
        
        for result in results[0].boxes.data.cpu().numpy():
            x1, y1, x2, y2, conf, cls = result
            if conf > max_confidence:
                max_confidence = conf
                best_face = {
                    'x1': int(x1),
                    'y1': int(y1),
                    'x2': int(x2),
                    'y2': int(y2),
                    'confidence': float(conf),
                    'class': int(cls)
                }
        
        if best_face:
            response = {"faces": [best_face]}
        else:
            response = {"faces": []}
        
        logger.info(f"/detect response: {response}")
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error in /detect: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/recognize', methods=['POST'])
def recognize_faces():
    try:
        # Recibir la imagen
        file = request.files['image'].read()
        np_img = np.frombuffer(file, np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        
        # Recibir las coordenadas del rostro desde form-data como texto y convertirlas a JSON
        faces = json.loads(request.form['faces'])
        
        match_counts = {}  # Diccionario para contar coincidencias por identidad
        
        for face in faces:
            x1, y1, x2, y2 = face['x1'], face['y1'], face['x2'], face['y2']
            
            # Recortar la región de la imagen donde está el rostro
            face_img = img[y1:y2, x1:x2]
            
            # Realizar el reconocimiento facial
            try:
                results = DeepFace.find(face_img, db_path='/app/employes_database', enforce_detection=False)
                if results:  # Verifica que la lista no esté vacía
                    for df in results:
                        if not df.empty:
                            for index, row in df.iterrows():
                                identity = row['identity']  # Extraer el valor de la serie
                                identity_name = identity.split('/')[-2]  # Extraer el nombre del subdirectorio (identidad)
                                if identity_name in match_counts:
                                    match_counts[identity_name] += 1
                                else:
                                    match_counts[identity_name] = 1
            except Exception as e:
                logger.error(f"Error in face recognition: {str(e)}")
                return jsonify({"identities": ["Error: " + str(e)]})
        
        # Verificar si hay alguna identidad con 10 o más coincidencias
        for identity_name, count in match_counts.items():
            if count >= 10:
                response = {"identities": [identity_name]}
                logger.info(f"/recognize response: {response}")
                return jsonify(response)
        
        response = {"identities": ["Desconocido"]}
        logger.info(f"/recognize response: {response}")
        return jsonify(response)
    
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in /recognize: {str(e)}")
        return jsonify({"error": f"JSON decoding error: {str(e)}"}), 400
    except Exception as e:
        logger.error(f"Error in /recognize: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')