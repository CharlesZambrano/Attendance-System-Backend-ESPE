# app.py
import cv2
import numpy as np
import torch

from flask import Flask, jsonify, request

app = Flask(__name__)

# Cargar el modelo YOLO desde el volumen compartido
model = torch.hub.load('ultralytics/yolov5', 'custom', path='/app/yolo_workspace/yolov8l-face-lindevs.pt')

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
    for result in results.xyxy[0]:
        x1, y1, x2, y2, conf, cls = map(float, result)
        faces.append({
            'x1': int(x1),
            'y1': int(y1),
            'x2': int(x2),
            'y2': int(y2),
            'confidence': conf,
            'class': int(cls)
        })
    
    return jsonify({"faces": faces})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')