import logging
from datetime import datetime, timedelta

from db_connection import get_db_connection

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

class_schedule_attendance_bp = Blueprint('class_schedule_attendance', __name__)


def extract_time_from_datetime(datetime_obj):
    """
    Extrae solo la parte de la hora de un objeto datetime.
    Si el argumento ya es un objeto datetime.time, simplemente lo retorna.
    """
    if isinstance(datetime_obj, str):
        return datetime.fromisoformat(datetime_obj).time()
    elif isinstance(datetime_obj, datetime):
        return datetime_obj.time()
    return datetime_obj  # En caso de que ya sea un objeto datetime.time


def generate_attendance_code(class_schedule_id, professor_id, register_date):
    """
    Genera un código único para el registro de asistencia.
    """
    return f"{class_schedule_id}-{professor_id}-{register_date.strftime('%Y%m%d')}"


def validate_schedule(class_schedule, register_date, entry_time, exit_time):
    """
    Valida que la hora de entrada y salida estén dentro del rango permitido.
    Se permite registrar la entrada hasta 10 minutos antes del inicio y la salida hasta 5 minutos después del final.
    """
    # Verifica que la fecha de asistencia coincida con los DAYS_OF_WEEK del CLASS_SCHEDULE
    day_of_week = register_date.strftime('%A')
    # DAYS_OF_WEEK es el 17º campo en tu esquema
    allowed_days = class_schedule[16].split(', ')

    if day_of_week not in allowed_days:
        return False, f"El día {day_of_week} no coincide con los días de la semana permitidos para esta clase."

    # Extraer horas de START_TIME y END_TIME
    class_start_time = extract_time_from_datetime(
        class_schedule[14])  # START_TIME es el 15º campo
    class_end_time = extract_time_from_datetime(
        class_schedule[15])  # END_TIME es el 16º campo

    # Ajustar los tiempos permitidos (5 minutos antes o después)
    allowed_start_time = (datetime.combine(
        register_date, class_start_time) - timedelta(minutes=10)).time()
    allowed_end_time = (datetime.combine(
        register_date, class_end_time) + timedelta(minutes=10)).time()

    # Verifica que las horas registradas estén dentro del horario permitido
    if not (allowed_start_time <= entry_time.time() <= allowed_end_time) or not (allowed_start_time <= exit_time.time() <= allowed_end_time):
        return False, "La hora de entrada o salida está fuera del horario permitido para esta clase."

    return True, ""


@class_schedule_attendance_bp.route('/class_schedule_attendance', methods=['POST'])
def register_attendance():
    """
    Registrar asistencia a una clase
    ---
    summary: Registrar asistencia
    description: Endpoint para registrar la asistencia a una clase.
    requestBody:
      required: true
      content:
        application/json:
          schema: ClassScheduleAttendanceSchema
    responses:
      201:
        description: Asistencia registrada exitosamente
        content:
          application/json:
            schema: ClassScheduleAttendanceResponseSchema
      400:
        description: Error en los datos proporcionados
      500:
        description: Error interno del servidor
    """
    data = request.json
    required_fields = ['CLASS_SCHEDULE_ID',
                       'PROFESSOR_ID', 'REGISTER_DATE', 'TIME']

    # Validar campos requeridos
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f"Falta el campo requerido: {field}"}), 400

    try:
        # Convertir fechas y horas
        register_date = datetime.strptime(
            data['REGISTER_DATE'], '%Y-%m-%d').date()
        time = datetime.strptime(data['TIME'], '%Y-%m-%dT%H:%M:%S.%fZ')

        # Obtener la conexión a la base de datos
        conn = get_db_connection()
        cur = conn.cursor()

        # Verificar si existe el CLASS_SCHEDULE_ID y obtener detalles
        cur.execute("SELECT * FROM CLASS_SCHEDULE WHERE CLASS_SCHEDULE_ID = :1",
                    (data['CLASS_SCHEDULE_ID'],))
        class_schedule = cur.fetchone()

        if not class_schedule:
            return jsonify({'error': "El CLASS_SCHEDULE_ID proporcionado no existe"}), 404

        # Validar horario y día de la clase
        valid, message = validate_schedule(
            class_schedule, register_date, time, time)
        if not valid:
            return jsonify({'error': message}), 400

        # Determinar si es una entrada tarde
        class_start_time = extract_time_from_datetime(class_schedule[14])
        late_entry = "SI" if time.time() > class_start_time else "NO"

        # Generar un código único para el registro de asistencia
        attendance_code = generate_attendance_code(
            data['CLASS_SCHEDULE_ID'], data['PROFESSOR_ID'], register_date)

        # Verificar si ya existe un registro de asistencia para esa clase y día
        cur.execute("""
            SELECT ENTRY_TIME, EXIT_TIME FROM CLASS_SCHEDULE_ATTENDANCE 
            WHERE CLASS_SCHEDULE_ID = :1 AND PROFESSOR_ID = :2 AND REGISTER_DATE = :3
        """, (data['CLASS_SCHEDULE_ID'], data['PROFESSOR_ID'], register_date))
        existing_attendance = cur.fetchone()

        if existing_attendance:
            if existing_attendance[1]:  # EXIT_TIME ya registrado
                return jsonify({'error': "Ya existe un registro completo de asistencia para esta clase y día"}), 409

            # Es la salida, actualizar registro existente
            # ENTRY_TIME es el primer campo
            entry_time = existing_attendance[0]
            total_hours = (time - entry_time).total_seconds() / 3600

            # Determinar si es una salida tarde
            class_end_time = extract_time_from_datetime(class_schedule[15])
            late_exit = "SI" if time.time() > class_end_time else "NO"

            cur.execute("""
                UPDATE CLASS_SCHEDULE_ATTENDANCE
                SET EXIT_TIME = :1, TOTAL_HOURS = :2, LATE_EXIT = :3, REGISTER_EXIT = :4
                WHERE CLASS_SCHEDULE_ID = :5 AND PROFESSOR_ID = :6 AND REGISTER_DATE = :7
            """, (time, total_hours, late_exit, "SI", data['CLASS_SCHEDULE_ID'], data['PROFESSOR_ID'], register_date))
            message = f"Salida registrada para la clase '{class_schedule[5]}' - NRC: {int(float(class_schedule[6]))}"

        else:
            # Es la entrada, registrar nuevo con TOTAL_HOURS = 0
            cur.execute("""
                INSERT INTO CLASS_SCHEDULE_ATTENDANCE (CLASS_SCHEDULE_ID, PROFESSOR_ID, REGISTER_DATE, ENTRY_TIME, ATTENDANCE_CODE, TOTAL_HOURS, TYPE, REGISTER_ENTRY, REGISTER_EXIT, LATE_ENTRY)
                VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9, :10)
            """, (data['CLASS_SCHEDULE_ID'], data['PROFESSOR_ID'], register_date, time, attendance_code, 0,
                  class_schedule[11],  # TYPE del CLASS_SCHEDULE
                  "SI", "NO", late_entry))
            message = f"Entrada registrada para la clase '{class_schedule[5]}' - NRC: {int(float(class_schedule[6]))}"

        conn.commit()
        return jsonify({'message': message}), 201

    except Exception as e:
        logger.error(f"Error al registrar asistencia: {e}")
        return jsonify({'error': "Ocurrió un error al registrar la asistencia"}), 500

    finally:
        cur.close()
        conn.close()


@class_schedule_attendance_bp.route('/class_schedule_attendance/<int:class_schedule_id>', methods=['GET'])
def get_class_schedule_attendance_by_schedule_id(class_schedule_id):
    """
    Obtener registros de asistencia por ID de horario de clase
    ---
    summary: Obtener registros de asistencia
    description: Endpoint para obtener registros de asistencia por ID de horario de clase.
    parameters:
      - name: class_schedule_id
        in: path
        required: true
        schema:
          type: integer
        description: ID del horario de clase
    responses:
      200:
        description: Registros de asistencia obtenidos exitosamente
        content:
          application/json:
            schema: ClassScheduleAttendanceResponseSchema
      404:
        description: No se encontraron registros de asistencia
      500:
        description: Error interno del servidor
    """
    try:
        # Obtener la conexión a la base de datos
        conn = get_db_connection()
        cur = conn.cursor()

        # Ejecutar la consulta para obtener el registro de asistencia por CLASS_SCHEDULE_ID
        cur.execute("""
            SELECT CLASS_SCHEDULE_ATTENDANCE_ID, PROFESSOR_ID, ATTENDANCE_CODE, REGISTER_DATE, ENTRY_TIME, 
                   EXIT_TIME, TOTAL_HOURS, LATE_ENTRY, TYPE, REGISTER_ENTRY, REGISTER_EXIT, LATE_EXIT 
            FROM CLASS_SCHEDULE_ATTENDANCE
            WHERE CLASS_SCHEDULE_ID = :1
        """, (class_schedule_id,))

        attendance_records = cur.fetchall()

        if not attendance_records:
            return jsonify({'error': "No se encontraron registros de asistencia para el CLASS_SCHEDULE_ID proporcionado"}), 404

        # Estructurar los resultados en formato JSON
        attendance_list = []
        for record in attendance_records:
            attendance_list.append({
                'CLASS_SCHEDULE_ATTENDANCE_ID': record[0],
                'PROFESSOR_ID': record[1],
                'ATTENDANCE_CODE': record[2],
                'REGISTER_DATE': record[3].strftime('%Y-%m-%d'),
                'ENTRY_TIME': record[4].strftime('%H:%M:%S') if record[4] else None,
                'EXIT_TIME': record[5].strftime('%H:%M:%S') if record[5] else None,
                'TOTAL_HOURS': record[6],
                'LATE_ENTRY': record[7],
                'TYPE': record[8],
                'REGISTER_ENTRY': record[9],
                'REGISTER_EXIT': record[10],
                'LATE_EXIT': record[11]
            })

        return jsonify(attendance_list), 200

    except Exception as e:
        logger.error(f"Error al obtener asistencia: {e}")
        return jsonify({'error': "Ocurrió un error al obtener la asistencia"}), 500

    finally:
        cur.close()
        conn.close()
