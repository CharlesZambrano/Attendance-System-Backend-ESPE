import logging
import random
from datetime import datetime

import cx_Oracle
from db_connection import get_db_connection
from werkzeug.security import generate_password_hash

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

appuser_bp = Blueprint('appuser', __name__)

def generate_unique_professor_code(cursor):
    while True:
        random_number = random.randint(1, 999)
        professor_code = f"PC{random_number:03}"
        
        cursor.execute(
            "SELECT COUNT(*) FROM PROFESSOR WHERE PROFESSOR_CODE = :professor_code", 
            {'professor_code': professor_code}
        )
        if cursor.fetchone()[0] == 0:
            return professor_code

@appuser_bp.route('/appuser', methods=['POST'])
def create_appuser():
    try:
        data = request.json
        
        # Validación del formato de la fecha
        try:
            registration_date = datetime.strptime(data['REGISTRATION_DATE'], '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Se espera 'YYYY-MM-DD'."}), 400

        # Hash de la contraseña antes de almacenarla
        hashed_password = generate_password_hash(data['PASSWORD'])

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verificar si el email ya existe en APP_USER
        cursor.execute(
            "SELECT COUNT(*) FROM APP_USER WHERE EMAIL = :email", 
            {'email': data['EMAIL']}
        )
        if cursor.fetchone()[0] > 0:
            return jsonify({"error": "El email ya está registrado en el sistema."}), 400

        # Variable para capturar el USER_ID generado
        cursor.execute(
            """
            DECLARE
                v_user_id NUMBER;
            BEGIN
                INSERT INTO APP_USER (FIRST_NAME, LAST_NAME, EMAIL, PASSWORD, ROLE_ID, REGISTRATION_DATE, PROFESSOR_ID) 
                VALUES (:first_name, :last_name, :email, :password, :role_id, TO_DATE(:registration_date, 'YYYY-MM-DD'), NULL)
                RETURNING USER_ID INTO v_user_id;

                :user_id := v_user_id;
            END;
            """, 
            {
                'first_name': data['FIRST_NAME'],
                'last_name': data['LAST_NAME'],
                'email': data['EMAIL'],
                'password': hashed_password,
                'role_id': data['ROLE_ID'],
                'registration_date': registration_date,
                'user_id': cursor.var(int)
            }
        )

        # Obtener el ID del usuario recién creado
        user_id = cursor.bindvars['user_id'].getvalue()

        # Generar un código de profesor único
        professor_code = generate_unique_professor_code(cursor)

        # Inserción en la tabla PROFESSOR con RETURNING INTO
        cursor.execute(
            """
            DECLARE
                v_professor_id NUMBER;
            BEGIN
                INSERT INTO PROFESSOR (USER_ID, PROFESSOR_CODE, FIRST_NAME, LAST_NAME, EMAIL, REGISTRATION_DATE, PHOTO, UNIVERSITY_ID, ID_CARD) 
                VALUES (:user_id, :professor_code, :first_name, :last_name, :email, TO_DATE(:registration_date, 'YYYY-MM-DD'), NULL, :university_id, :id_card)
                RETURNING PROFESSOR_ID INTO v_professor_id;

                :professor_id := v_professor_id;
            END;
            """,
            {
                'user_id': user_id,
                'professor_code': professor_code,  # Código único generado
                'first_name': data['FIRST_NAME'],
                'last_name': data['LAST_NAME'],
                'email': data['EMAIL'],
                'registration_date': registration_date,
                'university_id': data['UNIVERSITY_ID'],
                'id_card': data['ID_CARD'],
                'professor_id': cursor.var(int)
            }
        )

        # Obtener el ID del profesor recién creado
        professor_id = cursor.bindvars['professor_id'].getvalue()

        # Actualizar el AppUser con el PROFESSOR_ID
        cursor.execute(
            """
            UPDATE APP_USER
            SET PROFESSOR_ID = :professor_id
            WHERE USER_ID = :user_id
            """,
            {
                'professor_id': professor_id,
                'user_id': user_id
            }
        )

        conn.commit()
        return jsonify({"message": "AppUser y Professor creados exitosamente", "professor_code": professor_code}), 201
    except cx_Oracle.IntegrityError as e:
        logger.exception("Error de integridad de base de datos creando AppUser y Professor")
        conn.rollback()  # Hacer rollback en caso de error
        return jsonify({"error": "Error de integridad: " + str(e)}), 400
    except Exception as e:
        logger.exception("Error creando AppUser y Professor")
        conn.rollback()  # Hacer rollback en caso de error
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@appuser_bp.route('/appuser/<int:user_id>', methods=['GET'])
def get_appuser(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM APP_USER WHERE USER_ID = :user_id", {'user_id': user_id})
        appuser = cursor.fetchone()
        
        if appuser is None:
            return jsonify({"error": "AppUser no encontrado"}), 404
        
        return jsonify(dict(zip([key[0] for key in cursor.description], appuser))), 200
    except Exception as e:
        logger.exception("Error obteniendo AppUser")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@appuser_bp.route('/appuser/<int:user_id>', methods=['PUT'])
def update_appuser(user_id):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        # Hash de la contraseña antes de actualizarla (si es que se va a actualizar)
        hashed_password = generate_password_hash(data['PASSWORD'])

        cursor.execute(
            """
            UPDATE APP_USER 
            SET FIRST_NAME = :first_name, LAST_NAME = :last_name, EMAIL = :email, PASSWORD = :password, 
                ROLE_ID = :role_id, TEACHERID = :teacherid
            WHERE USER_ID = :user_id
            """,
            {
                'first_name': data['FIRST_NAME'],
                'last_name': data['LAST_NAME'],
                'email': data['EMAIL'],
                'password': hashed_password,
                'role_id': data['ROLE_ID'],
                'teacherid': data.get('TEACHERID'),
                'user_id': user_id
            }
        )
        conn.commit()
        return jsonify({"message": "AppUser actualizado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error actualizando AppUser")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@appuser_bp.route('/appuser/<int:user_id>', methods=['DELETE'])
def delete_appuser(user_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM APP_USER WHERE USER_ID = :user_id", {'user_id': user_id})
        conn.commit()
        return jsonify({"message": "AppUser eliminado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error eliminando AppUser")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()