import cv2
import numpy as np
from ultralytics import \
    YOLO  # Importar la clase YOLO desde la librería ultralytics

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')