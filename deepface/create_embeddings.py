from deepface import DeepFace
import os
import pickle

# Directorio con las imágenes de entrenamiento
dataset_path = "ZAMBRANO_CHARLES/CHARLES"
db_path = "database"

# Crear la carpeta de la base de datos si no existe
if not os.path.exists(db_path):
    os.makedirs(db_path)

# Procesar cada imagen en el dataset
for img_name in os.listdir(dataset_path):
    img_path = os.path.join(dataset_path, img_name)
    try:
        # Obtener representación facial
        embedding = DeepFace.represent(img_path=img_path, model_name='VGG-Face', enforce_detection=False)

        # Guardar la representación en la base de datos
        with open(os.path.join(db_path, img_name + ".pkl"), "wb") as f:
            pickle.dump(embedding, f)
    except Exception as e:
        print(f"Error processing {img_name}: {e}")