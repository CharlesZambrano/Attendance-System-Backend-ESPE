import logging
from datetime import datetime

import cx_Oracle
from db_connection import get_db_connection
from werkzeug.security import generate_password_hash

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

appuser_bp = Blueprint('appuser', __name__)

def generate_unique_teachercode(cursor):
    while True:
        random_number = random.randint(1, 999)
        teachercode = f"TC{random_number:03}"
        
        cursor.execute(
            "SELECT COUNT(*) FROM TEACHER WHERE TEACHERCODE = :teachercode", 
            {'teachercode': teachercode}
        )
        if cursor.fetchone()[0] == 0:
            return teachercode

@appuser_bp.route('/appuser', methods=['POST'])
def create_appuser():
    try:
        data = request.json
        
        # Validación del formato de la fecha
        try:
            registrationdate = datetime.strptime(data['REGISTRATIONDATE'], '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Se espera 'YYYY-MM-DD'."}), 400

        # Hash de la contraseña antes de almacenarla
        hashed_password = generate_password_hash(data['PASSWORD'])

        conn = get_db_connection()
        cursor = conn.cursor()

        # Verificar si el email ya existe en APPUSER
        cursor.execute(
            "SELECT COUNT(*) FROM APPUSER WHERE EMAIL = :email", 
            {'email': data['EMAIL']}
        )
        if cursor.fetchone()[0] > 0:
            return jsonify({"error": "El email ya está registrado en el sistema."}), 400

        # Variable para capturar el USERID generado
        cursor.execute(
            """
            DECLARE
                v_userid NUMBER;
            BEGIN
                INSERT INTO APPUSER (FIRSTNAME, LASTNAME, EMAIL, PASSWORD, ROLEID, REGISTRATIONDATE, TEACHERID) 
                VALUES (:firstname, :lastname, :email, :password, :roleid, TO_DATE(:registrationdate, 'YYYY-MM-DD'), NULL)
                RETURNING USERID INTO v_userid;

                :user_id := v_userid;
            END;
            """, 
            {
                'firstname': data['FIRSTNAME'],
                'lastname': data['LASTNAME'],
                'email': data['EMAIL'],
                'password': hashed_password,
                'roleid': data['ROLEID'],
                'registrationdate': registrationdate,
                'user_id': cursor.var(int)
            }
        )

        # Obtener el ID del usuario recién creado
        user_id = cursor.bindvars['user_id'].getvalue()

        # Generar un código de maestro único
        teachercode = generate_unique_teachercode(cursor)

        # Inserción en la tabla TEACHER con RETURNING INTO
        cursor.execute(
            """
            DECLARE
                v_teacherid NUMBER;
            BEGIN
                INSERT INTO TEACHER (USERID, TEACHERCODE, FIRSTNAME, LASTNAME, EMAIL, REGISTRATIONDATE, PHOTO) 
                VALUES (:userid, :teachercode, :firstname, :lastname, :email, TO_DATE(:registrationdate, 'YYYY-MM-DD'), NULL)
                RETURNING TEACHERID INTO v_teacherid;

                :teacher_id := v_teacherid;
            END;
            """,
            {
                'userid': user_id,
                'teachercode': teachercode,  # Código único generado
                'firstname': data['FIRSTNAME'],
                'lastname': data['LASTNAME'],
                'email': data['EMAIL'],
                'registrationdate': registrationdate,
                'teacher_id': cursor.var(int)
            }
        )

        # Obtener el ID del maestro recién creado
        teacher_id = cursor.bindvars['teacher_id'].getvalue()

        # Actualizar el AppUser con el TEACHERID
        cursor.execute(
            """
            UPDATE APPUSER
            SET TEACHERID = :teacherid
            WHERE USERID = :userid
            """,
            {
                'teacherid': teacher_id,
                'userid': user_id
            }
        )

        conn.commit()
        return jsonify({"message": "AppUser y Teacher creados exitosamente", "teachercode": teachercode}), 201
    except cx_Oracle.IntegrityError as e:
        logger.exception("Error de integridad de base de datos creando AppUser y Teacher")
        conn.rollback()  # Hacer rollback en caso de error
        return jsonify({"error": "Error de integridad: " + str(e)}), 400
    except Exception as e:
        logger.exception("Error creando AppUser y Teacher")
        conn.rollback()  # Hacer rollback en caso de error
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@appuser_bp.route('/appuser/<int:userid>', methods=['GET'])
def get_appuser(userid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM APPUSER WHERE USERID = :userid", {'userid': userid})
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

@appuser_bp.route('/appuser/<int:userid>', methods=['PUT'])
def update_appuser(userid):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        # Hash de la contraseña antes de actualizarla (si es que se va a actualizar)
        hashed_password = generate_password_hash(data['PASSWORD'])

        cursor.execute(
            """
            UPDATE APPUSER 
            SET FIRSTNAME = :firstname, LASTNAME = :lastname, EMAIL = :email, PASSWORD = :password, 
                ROLEID = :roleid, TEACHERID = :teacherid
            WHERE USERID = :userid
            """,
            {
                'firstname': data['FIRSTNAME'],
                'lastname': data['LASTNAME'],
                'email': data['EMAIL'],
                'password': hashed_password,
                'roleid': data['ROLEID'],
                'teacherid': data.get('TEACHERID'),
                'userid': userid
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

@appuser_bp.route('/appuser/<int:userid>', methods=['DELETE'])
def delete_appuser(userid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM APPUSER WHERE USERID = :userid", {'userid': userid})
        conn.commit()
        return jsonify({"message": "AppUser eliminado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error eliminando AppUser")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()