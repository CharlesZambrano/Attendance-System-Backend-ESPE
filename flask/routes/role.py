import logging
from datetime import datetime

from db_connection import get_db_connection

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

role_bp = Blueprint('role', __name__)

@role_bp.route('/role', methods=['POST'])
def create_role():
    cursor = None
    conn = None
    try:
        # Verificar que el contenido JSON esté presente
        if not request.is_json:
            return jsonify({"error": "El cuerpo de la solicitud debe estar en formato JSON."}), 400

        data = request.get_json()

        if not data or 'ROLENAME' not in data or 'CREATIONDATE' not in data:
            return jsonify({"error": "Faltan datos requeridos: ROLENAME y CREATIONDATE."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Validación del formato de la fecha
        try:
            creationdate = datetime.strptime(data['CREATIONDATE'], '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Se espera 'YYYY-MM-DD'."}), 400

        cursor.execute(
            """
            INSERT INTO ROLE (ROLENAME, CREATIONDATE) 
            VALUES (:rolename, TO_DATE(:creationdate, 'YYYY-MM-DD'))
            """, 
            {
                'rolename': data['ROLENAME'],
                'creationdate': creationdate
            }
        )
        conn.commit()
        return jsonify({"message": "Role creado exitosamente"}), 201
    except Exception as e:
        logger.exception("Error creando Role")
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@role_bp.route('/role/<int:roleid>', methods=['GET'])
def get_role(roleid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM ROLE WHERE ROLEID = :roleid", {'roleid': roleid})
        role = cursor.fetchone()
        
        if role is None:
            return jsonify({"error": "Role no encontrado"}), 404
        
        return jsonify(dict(zip([key[0] for key in cursor.description], role))), 200
    except Exception as e:
        logger.exception("Error obteniendo Role")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@role_bp.route('/role/<int:roleid>', methods=['PUT'])
def update_role(roleid):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            UPDATE ROLE 
            SET ROLENAME = :rolename
            WHERE ROLEID = :roleid
            """,
            {
                'rolename': data['ROLENAME'],
                'roleid': roleid
            }
        )
        conn.commit()
        return jsonify({"message": "Role actualizado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error actualizando Role")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@role_bp.route('/role/<int:roleid>', methods=['DELETE'])
def delete_role(roleid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM ROLE WHERE ROLEID = :roleid", {'roleid': roleid})
        conn.commit()
        return jsonify({"message": "Role eliminado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error eliminando Role")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
