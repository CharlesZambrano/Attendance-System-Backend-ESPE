import logging
from datetime import datetime

from db_connection import get_db_connection

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

work_schedule_bp = Blueprint('work_schedule', __name__)

# Función para validar y formatear los timestamps en formato requerido por Oracle


def validate_and_format_timestamp(timestamp_str):
    try:
        # Intentar parsear el timestamp usando un formato común
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        # Formatear el timestamp para Oracle con el formato adecuado
        return timestamp.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        raise ValueError(
            f"Timestamp inválido: {timestamp_str}. Debe estar en formato 'YYYY-MM-DD HH:MM:SS'.")


@work_schedule_bp.route('/work_schedule', methods=['POST'])
def create_schedule():
    """
    Crear un horario de trabajo
    ---
    summary: Crear un horario de trabajo
    description: Endpoint para crear un nuevo horario de trabajo en la base de datos.
    requestBody:
      required: true
      content:
        application/json:
          schema: WorkScheduleSchema
    responses:
      201:
        description: Horario de trabajo creado exitosamente
        content:
          application/json:
            schema: WorkScheduleResponseSchema
      400:
        description: Error en los datos proporcionados
      500:
        description: Error interno del servidor
    """
    try:
        data = request.json

        # Validar y formatear los timestamps
        start_time = validate_and_format_timestamp(data['START_TIME'])
        end_time = validate_and_format_timestamp(data['END_TIME'])

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO WORK_SCHEDULE (TEACHERID, DAYS_OF_WEEK, START_TIME, END_TIME, TOTAL_HOURS) 
            VALUES (:teacherid, :days_of_week, TO_DATE(:start_time, 'YYYY-MM-DD HH24:MI:SS'), TO_DATE(:end_time, 'YYYY-MM-DD HH24:MI:SS'), :total_hours)
            """,
            {
                'teacherid': data['TEACHERID'],
                'days_of_week': data['DAYS_OF_WEEK'],
                'start_time': start_time,
                'end_time': end_time,
                'total_hours': data['TOTAL_HOURS']
            }
        )
        conn.commit()
        return jsonify({"message": "Schedule creado exitosamente"}), 201
    except ValueError as ve:
        logger.warning(f"Error de validación: {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.exception("Error creando Schedule")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@work_schedule_bp.route('/work_schedule/<int:scheduleid>', methods=['GET'])
def get_schedule(scheduleid):
    """
    Obtener un horario de trabajo por ID
    ---
    summary: Obtener un horario de trabajo por ID
    description: Endpoint para obtener los detalles de un horario de trabajo por su ID.
    parameters:
      - name: scheduleid
        in: path
        required: true
        schema:
          type: integer
        description: ID del horario de trabajo
    responses:
      200:
        description: Horario de trabajo obtenido exitosamente
        content:
          application/json:
            schema: WorkScheduleResponseSchema
      404:
        description: Horario de trabajo no encontrado
      500:
        description: Error interno del servidor
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM WORK_SCHEDULE WHERE SCHEDULEID = :scheduleid", {'scheduleid': scheduleid})
        work_schedule = cursor.fetchone()

        if work_schedule is None:
            return jsonify({"error": "Schedule no encontrado"}), 404

        return jsonify(dict(zip([key[0] for key in cursor.description], work_schedule))), 200
    except Exception as e:
        logger.exception("Error obteniendo Schedule")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@work_schedule_bp.route('/work_schedule/<int:scheduleid>', methods=['PUT'])
def update_schedule(scheduleid):
    """
    Actualizar un horario de trabajo por ID
    ---
    summary: Actualizar un horario de trabajo por ID
    description: Endpoint para actualizar los detalles de un horario de trabajo por su ID.
    parameters:
      - name: scheduleid
        in: path
        required: true
        schema:
          type: integer
        description: ID del horario de trabajo
    requestBody:
      required: true
      content:
        application/json:
          schema: WorkScheduleSchema
    responses:
      200:
        description: Horario de trabajo actualizado exitosamente
        content:
          application/json:
            schema: WorkScheduleResponseSchema
      404:
        description: Horario de trabajo no encontrado
      500:
        description: Error interno del servidor
    """
    try:
        data = request.json

        # Validar y formatear los timestamps
        start_time = validate_and_format_timestamp(data['START_TIME'])
        end_time = validate_and_format_timestamp(data['END_TIME'])

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE WORK_SCHEDULE 
            SET DAYS_OF_WEEK = :days_of_week, START_TIME = TO_DATE(:start_time, 'YYYY-MM-DD HH24:MI:SS'), END_TIME = TO_DATE(:end_time, 'YYYY-MM-DD HH24:MI:SS'), TOTAL_HOURS = :total_hours
            WHERE SCHEDULEID = :scheduleid
            """,
            {
                'days_of_week': data['DAYS_OF_WEEK'],
                'start_time': start_time,
                'end_time': end_time,
                'total_hours': data['TOTAL_HOURS'],
                'scheduleid': scheduleid
            }
        )
        conn.commit()
        return jsonify({"message": "Schedule actualizado exitosamente"}), 200
    except ValueError as ve:
        logger.warning(f"Error de validación: {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        logger.exception("Error actualizando Schedule")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@work_schedule_bp.route('/work_schedule/<int:scheduleid>', methods=['DELETE'])
def delete_schedule(scheduleid):
    """
    Eliminar un horario de trabajo por ID
    ---
    summary: Eliminar un horario de trabajo por ID
    description: Endpoint para eliminar un horario de trabajo por su ID.
    parameters:
      - name: scheduleid
        in: path
        required: true
        schema:
          type: integer
        description: ID del horario de trabajo
    responses:
      200:
        description: Horario de trabajo eliminado exitosamente
      404:
        description: Horario de trabajo no encontrado
      500:
        description: Error interno del servidor
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM WORK_SCHEDULE WHERE SCHEDULEID = :scheduleid", {
                       'scheduleid': scheduleid})
        conn.commit()
        return jsonify({"message": "Schedule eliminado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error eliminando Schedule")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
