import logging
from datetime import datetime, timedelta

import pytz
from db_connection import get_db_connection

from flask import Blueprint, Flask, jsonify, request

logger = logging.getLogger(__name__)

attendance_bp = Blueprint('attendance', __name__)

def extract_time_from_datetime(datetime_str):
    """
    Extrae solo la parte de la hora de una cadena de fecha y hora en formato ISO 8601.
    """
    return datetime.fromisoformat(datetime_str).time()

def validate_schedule(class_schedule, register_date, entry_time, exit_time):
    # Verifica que la fecha de asistencia coincida con los DAYS_OF_WEEK del CLASS_SCHEDULE
    day_of_week = register_date.strftime('%A')
    if day_of_week not in class_schedule['DAYS_OF_WEEK'].split(', '):
        return False, f"El día {day_of_week} no coincide con los días de la semana permitidos para esta clase."

    # Extraer horas de START_TIME y END_TIME
    class_start_time = extract_time_from_datetime(class_schedule['START_TIME'])
    class_end_time = extract_time_from_datetime(class_schedule['END_TIME'])
    
    # Verifica que las horas registradas estén dentro del horario de la clase
    if not (class_start_time <= entry_time.time() <= class_end_time) or not (class_start_time <= exit_time.time() <= class_end_time):
        return False, "La hora de entrada o salida está fuera del horario permitido para esta clase."

    return True, ""

@attendance_bp.route('/attendance', methods=['POST'])
def register_attendance():
    data = request.json
    required_fields = ['CLASS_SCHEDULE_ID', 'PROFESSOR_ID', 'REGISTERDATE', 'TIME']
    
    # Validar campos requeridos
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f"Falta el campo requerido: {field}"}), 400
    
    try:
        # Convertir fechas y horas
        register_date = datetime.strptime(data['REGISTERDATE'], '%Y-%m-%d').date()
        time = datetime.strptime(data['TIME'], '%Y-%m-%dT%H:%M:%S.%fZ')

        # Obtener la conexión a la base de datos
        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar si existe el CLASS_SCHEDULE_ID y obtener detalles
        cur.execute("SELECT * FROM CLASS_SCHEDULE WHERE CLASS_SCHEDULE_ID = :1", (data['CLASS_SCHEDULE_ID'],))
        class_schedule = cur.fetchone()

        if not class_schedule:
            return jsonify({'error': "El CLASS_SCHEDULE_ID proporcionado no existe"}), 404

        # Validar horario y día de la clase
        valid, message = validate_schedule(class_schedule, register_date, time, time)
        if not valid:
            return jsonify({'error': message}), 400

        # Verificar si ya existe un registro de asistencia para esa clase y día
        cur.execute("""
            SELECT * FROM ATTENDANCE 
            WHERE CLASS_SCHEDULE_ID = :1 AND PROFESSOR_ID = :2 AND REGISTERDATE = :3
        """, (data['CLASS_SCHEDULE_ID'], data['PROFESSOR_ID'], register_date))
        existing_attendance = cur.fetchone()

        if existing_attendance:
            if existing_attendance['EXIT_TIME']:
                return jsonify({'error': "Ya existe un registro completo de asistencia para esta clase y día"}), 409
            
            # Es la salida, actualizar registro existente
            entry_time = existing_attendance['ENTRY_TIME']
            total_hours = (time - entry_time).total_seconds() / 3600

            cur.execute("""
                UPDATE ATTENDANCE
                SET EXIT_TIME = :1, TOTALHOURS = :2, LATE = :3
                WHERE CLASS_SCHEDULE_ID = :4 AND PROFESSOR_ID = :5 AND REGISTERDATE = :6
            """, (time, total_hours, entry_time.time() > extract_time_from_datetime(class_schedule['START_TIME']),
                  data['CLASS_SCHEDULE_ID'], data['PROFESSOR_ID'], register_date))
        else:
            # Es la entrada, registrar nuevo
            cur.execute("""
                INSERT INTO ATTENDANCE (CLASS_SCHEDULE_ID, PROFESSOR_ID, REGISTERDATE, ENTRY_TIME)
                VALUES (:1, :2, :3, :4)
            """, (data['CLASS_SCHEDULE_ID'], data['PROFESSOR_ID'], register_date, time))

        conn.commit()
        return jsonify({'message': "Asistencia registrada exitosamente"}), 201

    except Exception as e:
        logger.error(f"Error al registrar asistencia: {e}")
        return jsonify({'error': "Ocurrió un error al registrar la asistencia"}), 500

    finally:
        cur.close()
        conn.close()
