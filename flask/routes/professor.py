import logging
from datetime import datetime

from db_connection import get_db_connection

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

professor_bp = Blueprint('professor', __name__)

@professor_bp.route('/professor', methods=['POST'])
def create_professor():
    try:
        data = request.json

        # Validación del formato de la fecha
        try:
            registration_date = datetime.strptime(data['REGISTRATION_DATE'], '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Se espera 'YYYY-MM-DD'."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO PROFESSOR (USER_ID, PROFESSOR_CODE, FIRST_NAME, LAST_NAME, EMAIL, REGISTRATION_DATE, PHOTO, UNIVERSITY_ID, ID_CARD) 
            VALUES (:user_id, :professor_code, :first_name, :last_name, :email, TO_DATE(:registration_date, 'YYYY-MM-DD'), :photo, :university_id, :id_card)
            """,
            {
                'user_id': data['USER_ID'],
                'professor_code': data['PROFESSOR_CODE'],
                'first_name': data['FIRST_NAME'],
                'last_name': data['LAST_NAME'],
                'email': data['EMAIL'],
                'registration_date': registration_date,
                'photo': data.get('PHOTO'),  # Es opcional
                'university_id': data['UNIVERSITY_ID'],
                'id_card': data['ID_CARD']
            }
        )
        conn.commit()
        return jsonify({"message": "Professor creado exitosamente"}), 201
    except Exception as e:
        logger.exception("Error creando Professor")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@professor_bp.route('/professor/<int:professor_id>', methods=['GET'])
def get_professor(professor_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM PROFESSOR WHERE PROFESSOR_ID = :professor_id", {'professor_id': professor_id})
        professor = cursor.fetchone()

        if professor is None:
            return jsonify({"error": "Professor no encontrado"}), 404

        return jsonify(dict(zip([key[0] for key in cursor.description], professor))), 200
    except Exception as e:
        logger.exception("Error obteniendo Professor")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@professor_bp.route('/professor/<int:professor_id>', methods=['PUT'])
def update_professor(professor_id):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE PROFESSOR 
            SET USER_ID = :user_id, PROFESSOR_CODE = :professor_code, FIRST_NAME = :first_name, LAST_NAME = :last_name, 
                EMAIL = :email, REGISTRATION_DATE = TO_DATE(:registration_date, 'YYYY-MM-DD'), 
                PHOTO = :photo, UNIVERSITY_ID = :university_id, ID_CARD = :id_card
            WHERE PROFESSOR_ID = :professor_id
            """,
            {
                'user_id': data['USER_ID'],
                'professor_code': data['PROFESSOR_CODE'],
                'first_name': data['FIRST_NAME'],
                'last_name': data['LAST_NAME'],
                'email': data['EMAIL'],
                'registration_date': datetime.strptime(data['REGISTRATION_DATE'], '%Y-%m-%d').strftime('%Y-%m-%d'),
                'photo': data.get('PHOTO'),
                'university_id': data['UNIVERSITY_ID'],
                'id_card': data['ID_CARD'],
                'professor_id': professor_id
            }
        )
        conn.commit()
        return jsonify({"message": "Professor actualizado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error actualizando Professor")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@professor_bp.route('/professor/<int:professor_id>', methods=['PATCH'])
def patch_professor(professor_id):
    try:
        data = request.json

        if not data:
            return jsonify({"error": "No se proporcionaron datos para actualizar"}), 400

        # Preparar la sentencia SQL dinámica para actualizar solo los campos proporcionados
        fields = []
        values = {}

        # Validación y asignación de campos
        if 'USER_ID' in data:
            fields.append("USER_ID = :user_id")
            values['user_id'] = data['USER_ID']
        
        if 'PROFESSOR_CODE' in data:
            fields.append("PROFESSOR_CODE = :professor_code")
            values['professor_code'] = data['PROFESSOR_CODE']
        
        if 'FIRST_NAME' in data:
            fields.append("FIRST_NAME = :first_name")
            values['first_name'] = data['FIRST_NAME']
        
        if 'LAST_NAME' in data:
            fields.append("LAST_NAME = :last_name")
            values['last_name'] = data['LAST_NAME']
        
        if 'EMAIL' in data:
            fields.append("EMAIL = :email")
            values['email'] = data['EMAIL']
        
        if 'REGISTRATION_DATE' in data:
            try:
                registration_date = datetime.strptime(data['REGISTRATION_DATE'], '%Y-%m-%d').strftime('%Y-%m-%d')
                fields.append("REGISTRATION_DATE = TO_DATE(:registration_date, 'YYYY-MM-DD')")
                values['registration_date'] = registration_date
            except ValueError:
                return jsonify({"error": "Formato de fecha inválido. Se espera 'YYYY-MM-DD'."}), 400
        
        if 'PHOTO' in data:
            fields.append("PHOTO = :photo")
            values['photo'] = data.get('PHOTO')
        
        if 'UNIVERSITY_ID' in data:
            fields.append("UNIVERSITY_ID = :university_id")
            values['university_id'] = data['UNIVERSITY_ID']
        
        if 'ID_CARD' in data:
            fields.append("ID_CARD = :id_card")
            values['id_card'] = data['ID_CARD']
        
        if not fields:
            return jsonify({"error": "No se proporcionaron campos válidos para actualizar"}), 400

        # Unir los campos para formar la sentencia SQL
        sql = f"UPDATE PROFESSOR SET {', '.join(fields)} WHERE PROFESSOR_ID = :professor_id"
        values['professor_id'] = professor_id

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(sql, values)
        conn.commit()

        return jsonify({"message": "Professor actualizado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error actualizando Professor")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@professor_bp.route('/professor/<int:professor_id>', methods=['DELETE'])
def delete_professor(professor_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM PROFESSOR WHERE PROFESSOR_ID = :professor_id", {'professor_id': professor_id})
        conn.commit()
        return jsonify({"message": "Professor eliminado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error eliminando Professor")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@professor_bp.route('/professor/id_card/<string:id_card>', methods=['GET'])
def get_professor_by_id_card(id_card):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM PROFESSOR WHERE ID_CARD = :id_card", {'id_card': id_card})
        professor = cursor.fetchone()

        if professor is None:
            return jsonify({"error": "Professor no encontrado"}), 404

        return jsonify(dict(zip([key[0] for key in cursor.description], professor))), 200
    except Exception as e:
        logger.exception("Error obteniendo Professor por ID_CARD")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()