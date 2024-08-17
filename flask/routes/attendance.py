import logging
from datetime import datetime, timedelta

import pytz
from db_connection import get_db_connection

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

attendance_bp = Blueprint('attendance', __name__)

# Mapeo de días de la semana en inglés a español
days_mapping = {
    'MONDAY': 'LUNES',
    'TUESDAY': 'MARTES',
    'WEDNESDAY': 'MIÉRCOLES',
    'THURSDAY': 'JUEVES',
    'FRIDAY': 'VIERNES',
    'SATURDAY': 'SÁBADO',
    'SUNDAY': 'DOMINGO'
}

def dict_factory(cursor, row):
    """
    Convert the row to a dictionary using cursor description.
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0].lower()] = row[idx]
    return d

@attendance_bp.route('/attendance', methods=['POST'])
def create_attendance():
    cursor = None
    conn = None
    try:
        data = request.json
        logger.info(f"Datos recibidos en la solicitud: {data}")

        teacher_id = data['TEACHERID']
        
        # Obtener la hora actual en la zona horaria de Ecuador
        ecuador_tz = pytz.timezone('America/Guayaquil')
        current_time = datetime.now(ecuador_tz)
        logger.info(f"Hora actual en Ecuador: {current_time}")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Obtener el día de la semana en inglés y mapearlo al español
        day_of_week_english = current_time.strftime('%A').upper()
        day_of_week = days_mapping.get(day_of_week_english, None)
        logger.info(f"Día de la semana mapeado: {day_of_week_english} -> {day_of_week}")

        if day_of_week is None:
            error_message = f"No se pudo mapear el día de la semana {day_of_week_english}"
            logger.error(error_message)
            return jsonify({"error": error_message}), 500

        cursor.execute(
            """
            SELECT * FROM SCHEDULE WHERE TEACHERID = :teacherid AND DAYOFWEEK = :dayofweek
            """,
            {'teacherid': teacher_id, 'dayofweek': day_of_week}
        )
        rows = cursor.fetchall()
        logger.info(f"Horarios obtenidos de la base de datos: {rows}")

        if not rows:
            error_message = f"No se encontraron horarios para el maestro hoy ({day_of_week})"
            logger.warning(error_message)
            return jsonify({"error": error_message}), 404

        schedules = [dict_factory(cursor, row) for row in rows]

        # Convertir las horas de inicio y fin a timezone-aware datetime en la zona horaria de Ecuador
        for schedule in schedules:
            start_time = schedule['starttime'].replace(tzinfo=ecuador_tz)
            end_time = schedule['endtime'].replace(tzinfo=ecuador_tz)

            logger.info(f"Comparando tiempos: current_time={current_time}, start_time={start_time}, end_time={end_time}")

            if start_time - timedelta(minutes=10) <= current_time <= start_time + timedelta(minutes=10):
                logger.info("Coincidencia encontrada: Entrada")
                attendance_type = "Entrada"
            elif end_time - timedelta(minutes=10) <= current_time <= end_time + timedelta(minutes=10):
                logger.info("Coincidencia encontrada: Salida")
                attendance_type = "Salida"
            else:
                continue

            late = 'N'
            if attendance_type == "Entrada" and current_time > start_time:
                late = 'Y'
                logger.info("Entrada tardía detectada")

            cursor.execute(
                """
                INSERT INTO ATTENDANCE (TEACHERID, ATTENDANCECODE, REGISTERDATE, TOTALHOURS, LATE, DETECTIONCOORDINATES, TYPE) 
                VALUES (:teacherid, :attendancecode, :registerdate, :totalhours, :late, :detectioncoordinates, :type)
                """, 
                {
                    'teacherid': teacher_id,
                    'attendancecode': data['ATTENDANCECODE'],
                    'registerdate': current_time,  # Usar current_time que ya tiene la zona horaria correcta
                    'totalhours': schedule['totalhours'],
                    'late': late,
                    'detectioncoordinates': data.get('DETECTIONCOORDINATES'),
                    'type': attendance_type
                }
            )
            
            conn.commit()
            logger.info(f"Asistencia de {attendance_type} registrada exitosamente para el maestro {teacher_id}")
            return jsonify({"message": f"Asistencia de {attendance_type} registrada exitosamente"}), 201

        error_message = "La hora actual no coincide con ninguna franja horaria permitida"
        logger.warning(error_message)
        return jsonify({"error": error_message}), 400

    except Exception as e:
        logger.exception("Error al crear Asistencia")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@attendance_bp.route('/attendance/<int:attendanceid>', methods=['GET'])
def get_attendance(attendanceid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM ATTENDANCE WHERE ATTENDANCEID = :attendanceid", {'attendanceid': attendanceid})
        attendance = cursor.fetchone()
        
        if attendance is None:
            return jsonify({"error": "Attendance no encontrado"}), 404
        
        return jsonify(dict(zip([key[0] for key in cursor.description], attendance))), 200
    except Exception as e:
        logger.exception("Error obteniendo Attendance")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@attendance_bp.route('/attendance/<int:attendanceid>', methods=['PUT'])
def update_attendance(attendanceid):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            UPDATE ATTENDANCE 
            SET ATTENDANCECODE = :attendancecode, REGISTERDATE = :registerdate, TOTALHOURS = :totalhours, 
                LATE = :late, DETECTIONCOORDINATES = :detectioncoordinates, TYPE = :type
            WHERE ATTENDANCEID = :attendanceid
            """,
            {
                'attendancecode': data['ATTENDANCECODE'],
                'registerdate': data['REGISTERDATE'],
                'totalhours': data['TOTALHOURS'],
                'late': data['LATE'],
                'detectioncoordinates': data.get('DETECTIONCOORDINATES'),
                'type': data['TYPE'],
                'attendanceid': attendanceid
            }
        )
        conn.commit()
        return jsonify({"message": "Attendance actualizado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error actualizando Attendance")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@attendance_bp.route('/attendance/<int:attendanceid>', methods=['DELETE'])
def delete_attendance(attendanceid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM ATTENDANCE WHERE ATTENDANCEID = :attendanceid", {'attendanceid': attendanceid})
        conn.commit()
        return jsonify({"message": "Attendance eliminado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error eliminando Attendance")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()