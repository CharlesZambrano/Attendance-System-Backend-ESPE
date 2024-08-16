import logging
from datetime import datetime

from db_connection import get_db_connection

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

teacher_bp = Blueprint('teacher', __name__)

@teacher_bp.route('/teacher', methods=['POST'])
def create_teacher():
    try:
        data = request.json

        # Validación del formato de la fecha
        try:
            registrationdate = datetime.strptime(data['REGISTRATIONDATE'], '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Se espera 'YYYY-MM-DD'."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO TEACHER (USERID, TEACHERCODE, FIRSTNAME, LASTNAME, EMAIL, REGISTRATIONDATE, PHOTO) 
            VALUES (:userid, :teachercode, :firstname, :lastname, :email, TO_DATE(:registrationdate, 'YYYY-MM-DD'), :photo)
            """,
            {
                'userid': data['USERID'],
                'teachercode': data['TEACHERCODE'],
                'firstname': data['FIRSTNAME'],
                'lastname': data['LASTNAME'],
                'email': data['EMAIL'],
                'registrationdate': registrationdate,
                'photo': data.get('PHOTO')  # Es opcional
            }
        )
        conn.commit()
        return jsonify({"message": "Teacher creado exitosamente"}), 201
    except Exception as e:
        logger.exception("Error creando Teacher")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@teacher_bp.route('/teacher/<int:teacherid>', methods=['GET'])
def get_teacher(teacherid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM TEACHER WHERE TEACHERID = :teacherid", {'teacherid': teacherid})
        teacher = cursor.fetchone()

        if teacher is None:
            return jsonify({"error": "Teacher no encontrado"}), 404

        return jsonify(dict(zip([key[0] for key in cursor.description], teacher))), 200
    except Exception as e:
        logger.exception("Error obteniendo Teacher")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@teacher_bp.route('/teacher/<int:teacherid>', methods=['PUT'])
def update_teacher(teacherid):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE TEACHER 
            SET TEACHERCODE = :teachercode, FIRSTNAME = :firstname, LASTNAME = :lastname, EMAIL = :email, 
                PHOTO = :photo
            WHERE TEACHERID = :teacherid
            """,
            {
                'teachercode': data['TEACHERCODE'],
                'firstname': data['FIRSTNAME'],
                'lastname': data['LASTNAME'],
                'email': data['EMAIL'],
                'photo': data.get('PHOTO'),
                'teacherid': teacherid
            }
        )
        conn.commit()
        return jsonify({"message": "Teacher actualizado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error actualizando Teacher")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@teacher_bp.route('/teacher/<int:teacherid>', methods=['DELETE'])
def delete_teacher(teacherid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM TEACHER WHERE TEACHERID = :teacherid", {'teacherid': teacherid})
        conn.commit()
        return jsonify({"message": "Teacher eliminado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error eliminando Teacher")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()