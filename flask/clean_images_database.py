import os
import unicodedata


def clean_filename(filename):
    nfkd_form = unicodedata.normalize('NFKD', filename)
    clean_name = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    clean_name = clean_name.replace(" ", "_")  # Opcional: Reemplazar espacios con guiones bajos
    clean_name = clean_name.encode('ascii', 'ignore').decode('ascii')  # Eliminar cualquier carácter no ASCII
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

# Path to your employee images database
employee_db_path = '/app/employes_database'

# Clean the directory and files
clean_directory(employee_db_path)