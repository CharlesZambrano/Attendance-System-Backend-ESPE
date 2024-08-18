import logging
from datetime import datetime

import cx_Oracle
import numpy as np
import pandas as pd
import pytz
from db_connection import get_db_connection

from flask import Blueprint, jsonify, request

# Configure the blueprint
class_schedule_bp = Blueprint('class_schedule', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Function to get PROFESSOR_ID using UNIVERSITY_ID
def get_professor_id(connection, university_id):
    cursor = connection.cursor()
    query = """
    SELECT PROFESSOR_ID FROM PROFESSOR
    WHERE UNIVERSITY_ID = :university_id
    """
    logger.debug(f"Executing query with: UNIVERSITY_ID={university_id}")
    cursor.execute(query, {"university_id": university_id.strip()})
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

# Function to find the correct header row
def find_header_row(df):
    for i, row in df.iterrows():
        if "ID DOCENTE" in row.values:
            return i
    return None

# Function to map and format days of the week
def format_days_of_week(row):
    days_map = {'L': 'Monday', 'M': 'Tuesday', 'I': 'Wednesday', 'J': 'Thursday', 'V': 'Friday', 'S': 'Saturday', 'D': 'Sunday'}
    days_of_week = []
    for day, full_name in days_map.items():
        if pd.notnull(row[day]) and row[day].strip().upper() in ['M', 'T', 'W', 'R', 'F', 'S', 'U']:
            days_of_week.append(full_name)
    return ', '.join(days_of_week)

# Function to safely convert time values to the correct format
def convert_time(value):
    if pd.notnull(value):
        value = str(int(value)).zfill(4)  # Convert to integer, then to string, and pad with zeros if necessary
        return f"{value[:2]}:{value[2:]}:00"
    return None

# API to upload Excel file
@class_schedule_bp.route('/upload_class_schedule', methods=['POST'])
def upload_class_schedule():
    logger.debug("Received request to upload class schedule.")
    
    if 'file' not in request.files:
        logger.error("No file part in the request.")
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        logger.error("No selected file.")
        return jsonify({"error": "No selected file."}), 400

    if file and file.filename.endswith('.xlsx'):
        logger.debug("Loading Excel file.")
        df = pd.read_excel(file, header=None)
        header_row = find_header_row(df)
        if header_row is None:
            logger.error("Could not find the header row in the Excel file.")
            return jsonify({"error": "Could not find the header row in the Excel file."}), 400
        
        df = pd.read_excel(file, header=header_row)
        df.columns = df.columns.str.strip()

        logger.debug(f"Columns detected in Excel file: {df.columns.tolist()}")

        expected_columns = {
            'ID DOCENTE': None, 'ÁREA DE CONOCIMIENTO': None, 'NIVEL FORMACION': None, 
            'CODIGO': None, 'ASIGNATURA': None, 'NRC': None, 'STATUS': None, 
            'SECCION': None, '# CRED': None, 'TIPO': None, 'EDIFICIO': None, 
            'AULA': None, 'CAPACIDAD': None, 'HI': None, 'HF': None, 
            'L': None, 'M': None, 'I': None, 'J': None, 'V': None, 'S': None, 'D': None
        }

        for key in expected_columns.keys():
            if key in df.columns:
                expected_columns[key] = key
            else:
                logger.error(f"Column {key} is missing in the Excel file.")
                return jsonify({"error": f"Column {key} is missing in the Excel file."}), 400

        logger.debug(f"All expected columns found: {expected_columns}")

        connection = None
        try:
            connection = get_db_connection()
            for index, row in df.iterrows():
                university_id = row[expected_columns['ID DOCENTE']]
                logger.debug(f"Processing row {index}: ID DOCENTE={university_id}")
                professor_id = get_professor_id(connection, university_id)
                if not professor_id:
                    logger.warning(f"Professor ID not found for row {index}. Skipping row.")
                    continue

                knowledge_area = row[expected_columns['ÁREA DE CONOCIMIENTO']] if not pd.isnull(row[expected_columns['ÁREA DE CONOCIMIENTO']]) else 'UNKNOWN'
                education_level = row[expected_columns['NIVEL FORMACION']] if not pd.isnull(row[expected_columns['NIVEL FORMACION']]) else 'UNKNOWN'
                
                credits = row[expected_columns['# CRED']] if not pd.isnull(row[expected_columns['# CRED']]) else 0
                capacity = row[expected_columns['CAPACIDAD']] if not pd.isnull(row[expected_columns['CAPACIDAD']]) else None
                
                try:
                    credits = float(credits)
                    if capacity is not None:
                        capacity = int(capacity)
                except ValueError:
                    logger.error(f"Invalid numeric value in row {index}. Skipping row.")
                    continue

                start_time_str = convert_time(row[expected_columns['HI']])
                end_time_str = convert_time(row[expected_columns['HF']])
                
                start_time = f"2024-08-17 {start_time_str}" if start_time_str else None
                end_time = f"2024-08-17 {end_time_str}" if end_time_str else None
                
                days_of_week = format_days_of_week(row)
                
                building = row[expected_columns['EDIFICIO']] if not pd.isnull(row[expected_columns['EDIFICIO']]) else None
                classroom = row[expected_columns['AULA']] if not pd.isnull(row[expected_columns['AULA']]) else None

                logger.debug(f"Data to insert: PROFESSOR_ID={professor_id}, KNOWLEDGE_AREA={knowledge_area}, EDUCATION_LEVEL={education_level}, CODE={row[expected_columns['CODIGO']]}, SUBJECT={row[expected_columns['ASIGNATURA']]}, NRC={str(row[expected_columns['NRC']])}, STATUS={row[expected_columns['STATUS']]}, SECTION={str(row[expected_columns['SECCION']])}, CREDITS={credits}, TYPE={row[expected_columns['TIPO']]}, BUILDING={building}, CLASSROOM={classroom}, CAPACITY={capacity}, START_TIME={start_time}, END_TIME={end_time}, DAYS_OF_WEEK={days_of_week}")

                cursor = connection.cursor()
                try:
                    insert_query = """
                    INSERT INTO CLASS_SCHEDULE (
                        PROFESSOR_ID, KNOWLEDGE_AREA, EDUCATION_LEVEL, CODE, SUBJECT, NRC,
                        STATUS, SECTION, CREDITS, TYPE, BUILDING, CLASSROOM, CAPACITY,
                        START_TIME, END_TIME, DAYS_OF_WEEK
                    ) VALUES (
                        :professor_id, :knowledge_area, :education_level, :code, :subject, :nrc,
                        :status, :section, :credits, :type, :building, :classroom, :capacity,
                        TO_DATE(:start_time, 'YYYY-MM-DD HH24:MI:SS'), TO_DATE(:end_time, 'YYYY-MM-DD HH24:MI:SS'), :days_of_week
                    )
                    """
                    cursor.execute(insert_query, {
                        "professor_id": professor_id,
                        "knowledge_area": knowledge_area,
                        "education_level": education_level,
                        "code": row[expected_columns['CODIGO']],
                        "subject": row[expected_columns['ASIGNATURA']],
                        "nrc": str(row[expected_columns['NRC']]),  
                        "status": row[expected_columns['STATUS']],
                        "section": str(row[expected_columns['SECCION']]),  
                        "credits": credits,
                        "type": row[expected_columns['TIPO']],
                        "building": building,
                        "classroom": classroom,
                        "capacity": capacity,
                        "start_time": start_time,
                        "end_time": end_time,
                        "days_of_week": days_of_week
                    })
                    connection.commit()
                except cx_Oracle.IntegrityError as e:
                    error_code = e.args[0].code
                    if error_code == 1:  
                        error_message = f"Duplicate schedule detected for row {index}. The following data caused the conflict: {row.to_dict()}"
                        logger.error(error_message)
                        return jsonify({"error": error_message}), 400
                    else:
                        logger.error(f"Error inserting row {index}: {e}")
                        logger.debug(f"Failed data: {row.to_dict()}")
                        raise

                finally:
                    cursor.close()

            logger.info("File processed successfully.")
            return jsonify({"message": "Archivo procesado correctamente"}), 200
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
        return jsonify({"error": "Archivo de tipo invalido, solo .xlsx es permitido"}), 400


@class_schedule_bp.route('/create_class_schedule', methods=['POST'])
def create_class_schedule():
    logger.debug("Received request to create class schedule.")
    
    data = request.json
    if not data:
        logger.error("No JSON data provided in the request.")
        return jsonify({"error": "No JSON data provided in the request"}), 400
    
    expected_keys = [
        'PROFESSOR_ID', 'KNOWLEDGE_AREA', 'EDUCATION_LEVEL', 'CODE', 'SUBJECT', 'NRC', 
        'STATUS', 'SECTION', 'CREDITS', 'TYPE', 'BUILDING', 'CLASSROOM', 'CAPACITY', 
        'START_TIME', 'END_TIME', 'DAYS_OF_WEEK'
    ]
    
    for key in expected_keys:
        if key not in data:
            logger.error(f"Missing key '{key}' in JSON data.")
            return jsonify({"error": f"Missing key '{key}' in JSON data."}), 400
    
    connection = None
    try:
        connection = get_db_connection()
        
        # Prepare data for insertion
        professor_id = data['PROFESSOR_ID']
        knowledge_area = data.get('KNOWLEDGE_AREA', 'UNKNOWN')
        education_level = data.get('EDUCATION_LEVEL', 'UNKNOWN')
        credits = float(data['CREDITS']) if data['CREDITS'] else 0
        capacity = int(data['CAPACITY']) if data['CAPACITY'] else None
        
        # Convert and format the start_time and end_time
        start_time = pd.to_datetime(data['START_TIME']).strftime('%Y-%m-%d %H:%M:%S')
        end_time = pd.to_datetime(data['END_TIME']).strftime('%Y-%m-%d %H:%M:%S')
        
        days_of_week = data['DAYS_OF_WEEK']
        
        # Insert data into the database
        cursor = connection.cursor()
        try:
            insert_query = """
            INSERT INTO CLASS_SCHEDULE (
                PROFESSOR_ID, KNOWLEDGE_AREA, EDUCATION_LEVEL, CODE, SUBJECT, NRC,
                STATUS, SECTION, CREDITS, TYPE, BUILDING, CLASSROOM, CAPACITY,
                START_TIME, END_TIME, DAYS_OF_WEEK
            ) VALUES (
                :professor_id, :knowledge_area, :education_level, :code, :subject, :nrc,
                :status, :section, :credits, :type, :building, :classroom, :capacity,
                TO_DATE(:start_time, 'YYYY-MM-DD HH24:MI:SS'), TO_DATE(:end_time, 'YYYY-MM-DD HH24:MI:SS'), :days_of_week
            )
            """
            cursor.execute(insert_query, {
                "professor_id": professor_id,
                "knowledge_area": knowledge_area,
                "education_level": education_level,
                "code": data['CODE'],
                "subject": data['SUBJECT'],
                "nrc": str(data['NRC']),
                "status": data['STATUS'],
                "section": str(data['SECTION']),
                "credits": credits,
                "type": data['TYPE'],
                "building": data['BUILDING'],
                "classroom": data['CLASSROOM'],
                "capacity": capacity,
                "start_time": start_time,
                "end_time": end_time,
                "days_of_week": days_of_week
            })
            connection.commit()
            logger.info("Class schedule created successfully.")
            return jsonify({"message": "Class schedule created successfully"}), 201
        
        except cx_Oracle.IntegrityError as e:
            error_code = e.args[0].code
            if error_code == 1:  
                error_message = "Duplicate schedule detected. The following data caused the conflict: {}".format(data)
                logger.error(error_message)
                return jsonify({"error": error_message}), 400
            else:
                logger.error(f"Error inserting schedule: {e}")
                raise
        
        finally:
            cursor.close()
    
    except Exception as e:
        logger.exception("Error processing request.")
        if connection:
            connection.rollback()
        return jsonify({"error": str(e)}), 500
    
    finally:
        if connection:
            connection.close()

@class_schedule_bp.route('/class-schedules/<int:professor_id>', methods=['GET'])
def get_class_schedules(professor_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Obtener la zona horaria de Ecuador
        ecuador_tz = pytz.timezone('America/Guayaquil')
        # Obtener la fecha y hora actual en la zona horaria de Ecuador
        now_ecuador = datetime.now(ecuador_tz)
        # Obtener el día de la semana actual en Ecuador
        today = now_ecuador.strftime('%A')  # Esto devuelve el nombre del día de la semana en inglés

        # Consulta SQL para obtener los horarios de clase del profesor para el día actual
        query = """
        SELECT *
        FROM CLASS_SCHEDULE
        WHERE PROFESSOR_ID = :professor_id
        AND INSTR(DAYS_OF_WEEK, :today) > 0
        """

        cursor.execute(query, {'professor_id': professor_id, 'today': today})
        class_schedules = cursor.fetchall()

        if not class_schedules:
            return jsonify({"message": "No se encontraron horarios de clase para el profesor en el día actual."}), 404

        # Obtener los nombres de las columnas para estructurar la respuesta
        column_names = [desc[0] for desc in cursor.description]

        # Construir la respuesta como una lista de diccionarios
        result = [dict(zip(column_names, schedule)) for schedule in class_schedules]

        return jsonify(result), 200

    except Exception as e:
        logger.exception("Error obteniendo los horarios de clase.")
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()