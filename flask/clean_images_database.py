import os
import re
import unicodedata


def clean_filename(filename):
    # Normalizar el nombre del archivo para eliminar acentos
    nfkd_form = unicodedata.normalize('NFKD', filename)
    clean_name = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    
    # Reemplazar espacios con guiones bajos
    clean_name = clean_name.replace(" ", "_")
    
    # Eliminar cualquier carácter no ASCII
    clean_name = clean_name.encode('ascii', 'ignore').decode('ascii')
    
    # Eliminar caracteres inválidos en Windows
    clean_name = re.sub(r'[<>:"/\\|?*]', '', clean_name)
    
    # Asegurarse de que el nombre no termine con un espacio o punto
    clean_name = clean_name.rstrip(' .')
    
    return clean_name

def clean_directory(directory):
    for root, dirs, files in os.walk(directory, topdown=False):
        # Renombrar archivos
        for file in files:
            original_file_path = os.path.join(root, file)
            clean_file_name = clean_filename(file)
            clean_file_path = os.path.join(root, clean_file_name)
            if original_file_path != clean_file_path:
                os.rename(original_file_path, clean_file_path)
                print(f"Renamed file: {original_file_path} -> {clean_file_path}")

# Ruta a tu base de datos de imágenes de empleados
employee_db_path = '/app/academic_staff_database'

# Limpiar el directorio y los archivos
clean_directory(employee_db_path)