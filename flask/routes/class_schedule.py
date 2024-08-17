import logging

import pandas as pd
from db_connection import get_db_connection

from flask import Blueprint, jsonify, request

# Configuración del blueprint
class_schedule_bp = Blueprint('class_schedule', __name__)

# Configuración del logger
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Función para obtener el PROFESSOR_ID
def get_professor_id(connection, university_id, id_card, full_name):
    cursor = connection.cursor()
    query = """
    SELECT PROFESSORID FROM PROFESSOR
    WHERE UNIVERSITYID = :university_id AND IDCARD = :id_card AND (FIRSTNAME || ' ' || LASTNAME) = :full_name
    """
    # Logging para verificar los valores antes de la consulta
    logger.debug(f"Executing query with: UNIVERSITYID={university_id}, IDCARD={id_card}, FULLNAME={full_name}")
    
    cursor.execute(query, {
        "university_id": university_id.strip(),  # Asegurar que no haya espacios extraños
        "id_card": int(id_card),  # Convertir a entero si es numérico
        "full_name": full_name.strip()  # Asegurar que no haya espacios extraños
    })
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

# Función para encontrar la fila de encabezado correcta
def find_header_row(df):
    for i, row in df.iterrows():
        if "ID DOCENTE" in row.values:
            return i
    return None

# API para subir el archivo de Excel
@class_schedule_bp.route('/upload_class_schedule', methods=['POST'])
def upload_class_schedule():
    logger.debug("Received request to upload class schedule.")
    
    if 'file' not in request.files:
        logger.error("No file part in the request.")
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        logger.error("No selected file.")
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.xlsx'):
        logger.debug("Loading Excel file.")
        df = pd.read_excel(file, header=None)  # Cargar el archivo sin encabezados predefinidos

        # Buscar la fila correcta de encabezado
        header_row = find_header_row(df)
        if header_row is None:
            logger.error("Could not find the header row in the Excel file.")
            return jsonify({"error": "Could not find the header row in the Excel file."}), 400

        # Leer el archivo de nuevo, usando la fila correcta como encabezado
        df = pd.read_excel(file, header=header_row)
        df.columns = df.columns.str.strip()  # Limpiar nombres de columnas

        # Log columnas detectadas
        logger.debug(f"Columns detected in Excel file: {df.columns.tolist()}")

        # Verificar nombres de las columnas de manera flexible
        expected_columns = {
            'ID DOCENTE': None,
            'CÉDULA': None,
            'DOCENTE': None,
            'ÁREA DE CONOCIMIENTO': None, 
            'NIVEL FORMACION': None, 
            'CODIGO': None, 
            'ASIGNATURA': None, 
            'NRC': None, 
            'STATUS': None, 
            'SECCION': None, 
            '# CRED': None, 
            'TIPO': None, 
            'EDIFICIO': None, 
            'AULA': None, 
            'CAPACIDAD': None, 
            'HI': None, 
            'HF': None, 
            'L': None, 
            'M': None, 
            'I': None, 
            'J': None, 
            'V': None, 
            'S': None, 
            'D': None
        }

        # Asignar columnas encontradas en el DataFrame
        for key in expected_columns.keys():
            if key in df.columns:
                expected_columns[key] = key
            else:
                logger.error(f"Column {key} is missing in the Excel file.")
                return jsonify({"error": f"Column {key} is missing in the Excel file."}), 400

        logger.debug(f"All expected columns found: {expected_columns}")

        # Procesar cada fila del archivo de Excel
        connection = None
        try:
            connection = get_db_connection()

            for index, row in df.iterrows():
                university_id = row[expected_columns['ID DOCENTE']]
                id_card = row[expected_columns['CÉDULA']]
                full_name = row[expected_columns['DOCENTE']]

                # Log datos procesados
                logger.debug(f"Processing row {index}: ID DOCENTE={university_id}, CÉDULA={id_card}, DOCENTE={full_name}")

                # Obtener el PROFESSOR_ID
                professor_id = get_professor_id(connection, university_id, id_card, full_name)
                if not professor_id:
                    logger.warning(f"Professor ID not found for row {index}. Skipping row.")
                    continue  # Si no se encuentra el profesor, omitir la fila

                # Insertar el horario en la tabla CLASS_SCHEDULE
                cursor = connection.cursor()
                insert_query = """
                INSERT INTO CLASS_SCHEDULE (
                    PROFESSOR_ID, KNOWLEDGE_AREA, EDUCATION_LEVEL, CODE, SUBJECT, NRC,
                    STATUS, SECTION, CREDITS, TYPE, BUILDING, CLASSROOM, CAPACITY,
                    START_TIME, END_TIME, DAYS_OF_WEEK
                ) VALUES (
                    :professor_id, :knowledge_area, :education_level, :code, :subject, :nrc,
                    :status, :section, :credits, :type, :building, :classroom, :capacity,
                    :start_time, :end_time, :days_of_week
                )
                """
                days_of_week = "".join([day for day in ['L', 'M', 'I', 'J', 'V', 'S', 'D'] if row[expected_columns[day]] == 'X'])
                cursor.execute(insert_query, {
                    "professor_id": professor_id,
                    "knowledge_area": row[expected_columns['ÁREA DE CONOCIMIENTO']],
                    "education_level": row[expected_columns['NIVEL FORMACION']],
                    "code": row[expected_columns['CODIGO']],
                    "subject": row[expected_columns['ASIGNATURA']],
                    "nrc": row[expected_columns['NRC']],
                    "status": row[expected_columns['STATUS']],
                    "section": row[expected_columns['SECCION']],
                    "credits": row[expected_columns['# CRED']],
                    "type": row[expected_columns['TIPO']],
                    "building": row[expected_columns['EDIFICIO']],
                    "classroom": row[expected_columns['AULA']],
                    "capacity": row[expected_columns['CAPACIDAD']],
                    "start_time": row[expected_columns['HI']],
                    "end_time": row[expected_columns['HF']],
                    "days_of_week": days_of_week
                })
                connection.commit()
                cursor.close()

            logger.info("File processed successfully.")
            return jsonify({"message": "File processed successfully"}), 200
        except Exception as e:
            logger.exception("Error processing file.")
            if connection:
                connection.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            if connection:
                connection.close()
    else:
        logger.error("Invalid file type, only .xlsx is allowed.")
        return jsonify({"error": "Invalid file type, only .xlsx is allowed"}), 400

