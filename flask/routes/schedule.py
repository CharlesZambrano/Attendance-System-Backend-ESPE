import logging

from db_connection import get_db_connection

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

schedule_bp = Blueprint('schedule', __name__)

@schedule_bp.route('/schedule', methods=['POST'])
def create_schedule():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO SCHEDULE (TEACHERID, DAYOFWEEK, STARTTIME, ENDTIME, TOTALHOURS) 
            VALUES (:teacherid, :dayofweek, :starttime, :endtime, :totalhours)
            """, 
            {
                'teacherid': data['TEACHERID'],
                'dayofweek': data['DAYOFWEEK'],
                'starttime': data['STARTTIME'],
                'endtime': data['ENDTIME'],
                'totalhours': data['TOTALHOURS']
            }
        )
        conn.commit()
        return jsonify({"message": "Schedule creado exitosamente"}), 201
    except Exception as e:
        logger.exception("Error creando Schedule")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@schedule_bp.route('/schedule/<int:scheduleid>', methods=['GET'])
def get_schedule(scheduleid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM SCHEDULE WHERE SCHEDULEID = :scheduleid", {'scheduleid': scheduleid})
        schedule = cursor.fetchone()
        
        if schedule is None:
            return jsonify({"error": "Schedule no encontrado"}), 404
        
        return jsonify(dict(zip([key[0] for key in cursor.description], schedule))), 200
    except Exception as e:
        logger.exception("Error obteniendo Schedule")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@schedule_bp.route('/schedule/<int:scheduleid>', methods=['PUT'])
def update_schedule(scheduleid):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            UPDATE SCHEDULE 
            SET DAYOFWEEK = :dayofweek, STARTTIME = :starttime, ENDTIME = :endtime, TOTALHOURS = :totalhours
            WHERE SCHEDULEID = :scheduleid
            """,
            {
                'dayofweek': data['DAYOFWEEK'],
                'starttime': data['STARTTIME'],
                'endtime': data['ENDTIME'],
                'totalhours': data['TOTALHOURS'],
                'scheduleid': scheduleid
            }
        )
        conn.commit()
        return jsonify({"message": "Schedule actualizado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error actualizando Schedule")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@schedule_bp.route('/schedule/<int:scheduleid>', methods=['DELETE'])
def delete_schedule(scheduleid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM SCHEDULE WHERE SCHEDULEID = :scheduleid", {'scheduleid': scheduleid})
        conn.commit()
        return jsonify({"message": "Schedule eliminado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error eliminando Schedule")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
