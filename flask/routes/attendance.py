import logging

from db_connection import get_db_connection

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/attendance', methods=['POST'])
def create_attendance():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO ATTENDANCE (TEACHERID, ATTENDANCECODE, REGISTERDATE, TOTALHOURS, LATE, DETECTIONCOORDINATES, TYPE) 
            VALUES (:teacherid, :attendancecode, :registerdate, :totalhours, :late, :detectioncoordinates, :type)
            """, 
            {
                'teacherid': data['TEACHERID'],
                'attendancecode': data['ATTENDANCECODE'],
                'registerdate': data['REGISTERDATE'],
                'totalhours': data['TOTALHOURS'],
                'late': data['LATE'],
                'detectioncoordinates': data.get('DETECTIONCOORDINATES'),
                'type': data['TYPE']
            }
        )
        conn.commit()
        return jsonify({"message": "Attendance creado exitosamente"}), 201
    except Exception as e:
        logger.exception("Error creando Attendance")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
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
