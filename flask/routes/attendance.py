import logging
from datetime import datetime, timedelta

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
        teacher_id = data['TEACHERID']
        current_time = datetime.now()

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener el día de la semana en inglés y mapearlo al español
        day_of_week_english = current_time.strftime('%A').upper()  # Ejemplo: "FRIDAY"
        day_of_week = days_mapping.get(day_of_week_english, None)

        if day_of_week is None:
            return jsonify({"error": f"No se pudo mapear el día de la semana {day_of_week_english}"}), 500
        
        cursor.execute(
            """
            SELECT * FROM SCHEDULE WHERE TEACHERID = :teacherid AND DAYOFWEEK = :dayofweek
            """,
            {'teacherid': teacher_id, 'dayofweek': day_of_week}
        )
        rows = cursor.fetchall()

        if not rows:
            return jsonify({"error": f"No se encontraron horarios para el maestro hoy ({day_of_week})"}), 404

        # Convertir cada fila en un diccionario
        schedules = [dict_factory(cursor, row) for row in rows]

        # Paso 2: Determinar la franja horaria correcta con ventana de 10 minutos antes y después
        for schedule in schedules:
            start_time = schedule['starttime']
            end_time = schedule['endtime']

            # Imprimir valores para depuración
            print(f"current_time={current_time}, start_time={start_time}, end_time={end_time}")

            # Verificar si la hora actual está dentro de la ventana de 10 minutos antes o después del inicio o fin
            if start_time - timedelta(minutes=10) <= current_time <= start_time + timedelta(minutes=10):
                print("Coincidencia encontrada: Entrada")
                attendance_type = "Entrada"
            elif end_time - timedelta(minutes=10) <= current_time <= end_time + timedelta(minutes=10):
                print("Coincidencia encontrada: Salida")
                attendance_type = "Salida"
            else:
                continue

            # Calcular tardanza
            late = 'N'
            if attendance_type == "Entrada" and current_time > start_time:
                late = 'Y'

            # Paso 3: Insertar el registro de asistencia
            cursor.execute(
                """
                INSERT INTO ATTENDANCE (TEACHERID, ATTENDANCECODE, REGISTERDATE, TOTALHOURS, LATE, DETECTIONCOORDINATES, TYPE) 
                VALUES (:teacherid, :attendancecode, SYSTIMESTAMP, :totalhours, :late, :detectioncoordinates, :type)
                """, 
                {
                    'teacherid': teacher_id,
                    'attendancecode': data['ATTENDANCECODE'],
                    'totalhours': schedule['totalhours'],
                    'late': late,
                    'detectioncoordinates': data.get('DETECTIONCOORDINATES'),
                    'type': attendance_type
                }
            )
            conn.commit()
            return jsonify({"message": f"Asistencia de {attendance_type} registrada exitosamente"}), 201
        
        return jsonify({"error": "La hora actual no coincide con ninguna franja horaria permitida"}), 400

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