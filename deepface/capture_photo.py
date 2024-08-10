import cv2

# Inicializar la cámara (dispositivo 0 por defecto)
cap = cv2.VideoCapture(0)

# Capturar una imagen
ret, frame = cap.read()

# Liberar la cámara
cap.release()

# Verificar si la captura fue exitosa
if ret:
    # Guardar la imagen capturada en el archivo 'captured_image.jpg'
    cv2.imwrite("captured_image.jpg", frame)
    print("Imagen capturada y guardada como 'captured_image.jpg'")
else:
    print("No se pudo capturar la imagen.")
