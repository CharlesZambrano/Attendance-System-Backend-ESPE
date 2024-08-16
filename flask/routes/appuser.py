import logging
from datetime import datetime

from db_connection import get_db_connection
from werkzeug.security import generate_password_hash

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

appuser_bp = Blueprint('appuser', __name__)

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
        
        cursor.execute(
            """
            INSERT INTO APPUSER (FIRSTNAME, LASTNAME, EMAIL, PASSWORD, ROLEID, REGISTRATIONDATE, TEACHERID) 
            VALUES (:firstname, :lastname, :email, :password, :roleid, TO_DATE(:registrationdate, 'YYYY-MM-DD'), :teacherid)
            """, 
            {
                'firstname': data['FIRSTNAME'],
                'lastname': data['LASTNAME'],
                'email': data['EMAIL'],
                'password': hashed_password,
                'roleid': data['ROLEID'],
                'registrationdate': registrationdate,
                'teacherid': data.get('TEACHERID')  # Es opcional
            }
        )
        conn.commit()
        return jsonify({"message": "AppUser creado exitosamente"}), 201
    except Exception as e:
        logger.exception("Error creando AppUser")
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