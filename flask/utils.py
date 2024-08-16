import logging
import os
import unicodedata

import cv2
import numpy as np

# Configuración del logger
logger = logging.getLogger(__name__)

def clean_filename(filename):
    nfkd_form = unicodedata.normalize('NFKD', filename)
    clean_name = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    clean_name = clean_name.replace(" ", "_")
    clean_name = clean_name.encode('ascii', 'ignore').decode('ascii')
    return clean_name

def clean_directory(directory):
    for root, dirs, files in os.walk(directory, topdown=False):
        for file in files:
            original_file_path = os.path.join(root, file)
            clean_file_name = clean_filename(file)
            clean_file_path = os.path.join(root, clean_file_name)
            if original_file_path != clean_file_path:
                os.rename(original_file_path, clean_file_path)
                print(f"Renamed file: {original_file_path} -> {clean_file_path}")

def detect_directory_changes(directory):
    current_mod_time = max(
        os.path.getmtime(root) for root, _, _ in os.walk(directory)
    )
    return current_mod_time

def eye_aspect_ratio(eye):
    if eye.shape[0] != 6:
        logger.info("EAR: Ojo con puntos insuficientes para cálculo de EAR")
        return None

    A = np.linalg.norm(eye[1] - eye[5])
    B = np.linalg.norm(eye[2] - eye[4])
    C = np.linalg.norm(eye[0] - eye[3])
    ear = (A + B) / (2.0 * C)
    
    logger.info(f"EAR: {ear}")
    return ear

def detect_blink(eyes):
    if len(eyes) == 2:
        left_eye = eyes[0]
        right_eye = eyes[1]
        
        left_ear = eye_aspect_ratio(left_eye)
        right_ear = eye_aspect_ratio(right_eye)

        if left_ear is None or right_ear is None:
            logger.info("Blink detection: EAR no se pudo calcular para uno o ambos ojos")
            return False

        ear = (left_ear + right_ear) / 2.0
        blink_threshold = 0.25
        blink_detected = ear < blink_threshold

        logger.info(f"Blink detection: EAR promedio = {ear}, Umbral = {blink_threshold}, Parpadeo detectado = {blink_detected}")
        return blink_detected
    else:
        logger.info(f"Blink detection: Número de ojos detectados = {len(eyes)}")
    return False

def detect_eye_reflection(face_img, eyes):
    gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
    for (ex, ey, ew, eh) in eyes:
        eye = gray[ey:ey+eh, ex:ex+ew]
        _, thresholded = cv2.threshold(eye, 42, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if len(contours) > 0:
            logger.info("Reflection detection: Reflejo detectado en el ojo")
            return True
    logger.info("Reflection detection: No se detectó reflejo en los ojos")
    return False

def detect_liveness(face_img, eye_cascade):
    eyes = eye_cascade.detectMultiScale(face_img, 1.3, 5)
    logger.info(f"Liveness detection: Número de ojos detectados = {len(eyes)}")
    if detect_blink(eyes):
        logger.info("Liveness detection: Parpadeo detectado, rostro vivo.")
        return True
    if detect_eye_reflection(face_img, eyes):
        logger.info("Liveness detection: Reflejo detectado en los ojos, rostro vivo.")
        return True
    logger.info("Liveness detection: No se detectó vida en el rostro.")
    return False