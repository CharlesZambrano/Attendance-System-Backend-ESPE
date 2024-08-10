from deepface import DeepFace

# Analizar la imagen para obtener representaciones de los rostrosresult = DeepFace.analyze(img_path="test.jpg", actions=['age', 'gender', 'race', 'emotion'])
result = DeepFace.analyze(img_path="real_face.jpg", actions=['age', 'gender', 'race', 'emotion'])
# Imprimir los resultados
print("Result:", result)
