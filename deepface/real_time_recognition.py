from deepface import DeepFace
import os
from datetime import datetime

# Ruta de la imagen a analizar
image_path = "input_image.jpg"  # Cambia esto al nombre de tu imagen

# Ruta de la base de datos
db_path = "database"
output_file = "recognition_results.txt"

# Verificar que la imagen existe
if not os.path.exists(image_path):
    print(f"La imagen {image_path} no existe.")
    exit()

# Abrir archivo de salida
with open(output_file, "w") as file:
    file.write("Fecha y Hora, Resultado\n")

    # Realizar la detección y el reconocimiento
    try:
        result = DeepFace.find(img_path=image_path, db_path=db_path, model_name='VGG-Face', enforce_detection=False)
        
        # Si se reconoce a Charles
        if result.shape[0] > 0:
            output_text = "CHARLES"
        else:
            output_text = "NO SE RECONOCE"
    
    except Exception as e:
        output_text = "NO SE RECONOCE"
        print(f"Error during recognition: {e}")
    
    # Escribir el resultado en el archivo
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file.write(f"{timestamp}, {output_text}\n")

print("Proceso completado. Revisa el archivo 'recognition_results.txt' para ver los resultados.")
