# Import necessary modules
import logging

import cx_Oracle
import numpy as np
import pandas as pd
from db_connection import get_db_connection

from flask import Blueprint, jsonify, request

# Configure the blueprint
class_schedule_bp = Blueprint('class_schedule', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Function to get PROFESSOR_ID using UNIVERSITYID
def get_professor_id(connection, university_id):
    cursor = connection.cursor()
    query = """
    SELECT PROFESSORID FROM PROFESSOR
    WHERE UNIVERSITYID = :university_id
    """
    logger.debug(f"Executing query with: UNIVERSITYID={university_id}")
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
    # Map of days in Excel to their full English names
    days_map = {'L': 'Monday', 'M': 'Tuesday', 'I': 'Wednesday', 'J': 'Thursday', 'V': 'Friday', 'S': 'Saturday', 'D': 'Sunday'}
    days_of_week = []
    
    # Iterate over each day in the map and check if it's marked in the row
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

                # Handle NaN values and validate data before insertion
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

                # Convert and format the time values
                start_time_str = convert_time(row[expected_columns['HI']])
                end_time_str = convert_time(row[expected_columns['HF']])
                
                # Format the start_time and end_time with a dummy date
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
                        "nrc": str(row[expected_columns['NRC']]),  # Ensure NRC is a string
                        "status": row[expected_columns['STATUS']],
                        "section": str(row[expected_columns['SECCION']]),  # Ensure SECTION is a string
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
                    if error_code == 1:  # ORA-00001: unique constraint violated
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
