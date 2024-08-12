import json

import cv2
import numpy as np
from ultralytics import YOLO

from deepface import DeepFace
from flask import Flask, jsonify, request

app = Flask(__name__)

# Cargar el modelo YOLOv8 desde el directorio correcto
model = YOLO('/app/yolov8l-face-lindevs.pt')

@app.route('/detect', methods=['POST'])
def detect_faces():
    # Recibir la imagen enviada desde el frontend
    file = request.files['image'].read()
    np_img = np.frombuffer(file, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    
    # Detección de rostros con YOLO
    results = model(img)
    
    # Extraer coordenadas de los rostros detectados
    faces = []
    for result in results[0].boxes.data.cpu().numpy():
        x1, y1, x2, y2, conf, cls = result
        faces.append({
            'x1': int(x1),
            'y1': int(y1),
            'x2': int(x2),
            'y2': int(y2),
            'confidence': float(conf),
            'class': int(cls)
        })
    
    return jsonify({"faces": faces})

@app.route('/recognize', methods=['POST'])
def recognize_faces():
    # Recibir la imagen
    file = request.files['image'].read()
    np_img = np.frombuffer(file, np.uint8)
    img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
    
    # Recibir las coordenadas del rostro desde form-data como texto y convertirlas a JSON
    faces = json.loads(request.form['faces'])
    
    identities = []
    
    for face in faces:
        x1, y1, x2, y2 = face['x1'], face['y1'], face['x2'], face['y2']
        
        # Recortar la región de la imagen donde está el rostro
        face_img = img[y1:y2, x1:x2]
        
        # Realizar el reconocimiento facial
        try:
            results = DeepFace.find(face_img, db_path='/app/employes_database', enforce_detection=False)
            if results:  # Verifica que la lista de resultados no esté vacía
                identity = results[0]['identity']  # Esto es probablemente una serie de Pandas
                identities.append(str(identity))  # Convertir la identidad a cadena de texto
            else:
                identities.append("Unknown")
        except Exception as e:
            identities.append("Error: " + str(e))
    
    return jsonify({"identities": identities})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')