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
            registrationdate = datetime.strptime(data['REGISTRATIONDATE'], '%Y-%m-%d').strftime('%Y-%m-%d')
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido. Se espera 'YYYY-MM-DD'."}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO PROFESSOR (USERID, PROFESSORCODE, FIRSTNAME, LASTNAME, EMAIL, REGISTRATIONDATE, PHOTO, UNIVERSITYID, IDCARD) 
            VALUES (:userid, :professorcode, :firstname, :lastname, :email, TO_DATE(:registrationdate, 'YYYY-MM-DD'), :photo, :universityid, :idcard)
            """,
            {
                'userid': data['USERID'],
                'professorcode': data['PROFESSORCODE'],
                'firstname': data['FIRSTNAME'],
                'lastname': data['LASTNAME'],
                'email': data['EMAIL'],
                'registrationdate': registrationdate,
                'photo': data.get('PHOTO'),  # Es opcional
                'universityid': data['UNIVERSITYID'],
                'idcard': data['IDCARD']
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

@professor_bp.route('/professor/<int:professorid>', methods=['GET'])
def get_professor(professorid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM PROFESSOR WHERE PROFESSORID = :professorid", {'professorid': professorid})
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

@professor_bp.route('/professor/<int:professorid>', methods=['PUT'])
def update_professor(professorid):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE PROFESSOR 
            SET USERID = :userid, PROFESSORCODE = :professorcode, FIRSTNAME = :firstname, LASTNAME = :lastname, 
                EMAIL = :email, REGISTRATIONDATE = TO_DATE(:registrationdate, 'YYYY-MM-DD'), 
                PHOTO = :photo, UNIVERSITYID = :universityid, IDCARD = :idcard
            WHERE PROFESSORID = :professorid
            """,
            {
                'userid': data['USERID'],
                'professorcode': data['PROFESSORCODE'],
                'firstname': data['FIRSTNAME'],
                'lastname': data['LASTNAME'],
                'email': data['EMAIL'],
                'registrationdate': datetime.strptime(data['REGISTRATIONDATE'], '%Y-%m-%d').strftime('%Y-%m-%d'),
                'photo': data.get('PHOTO'),
                'universityid': data['UNIVERSITYID'],
                'idcard': data['IDCARD'],
                'professorid': professorid
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

@professor_bp.route('/professor/<int:professorid>', methods=['PATCH'])
def patch_professor(professorid):
    try:
        data = request.json

        if not data:
            return jsonify({"error": "No se proporcionaron datos para actualizar"}), 400

        # Preparar la sentencia SQL dinámica para actualizar solo los campos proporcionados
        fields = []
        values = {}

        # Validación y asignación de campos
        if 'USERID' in data:
            fields.append("USERID = :userid")
            values['userid'] = data['USERID']
        
        if 'PROFESSORCODE' in data:
            fields.append("PROFESSORCODE = :professorcode")
            values['professorcode'] = data['PROFESSORCODE']
        
        if 'FIRSTNAME' in data:
            fields.append("FIRSTNAME = :firstname")
            values['firstname'] = data['FIRSTNAME']
        
        if 'LASTNAME' in data:
            fields.append("LASTNAME = :lastname")
            values['lastname'] = data['LASTNAME']
        
        if 'EMAIL' in data:
            fields.append("EMAIL = :email")
            values['email'] = data['EMAIL']
        
        if 'REGISTRATIONDATE' in data:
            try:
                registrationdate = datetime.strptime(data['REGISTRATIONDATE'], '%Y-%m-%d').strftime('%Y-%m-%d')
                fields.append("REGISTRATIONDATE = TO_DATE(:registrationdate, 'YYYY-MM-DD')")
                values['registrationdate'] = registrationdate
            except ValueError:
                return jsonify({"error": "Formato de fecha inválido. Se espera 'YYYY-MM-DD'."}), 400
        
        if 'PHOTO' in data:
            fields.append("PHOTO = :photo")
            values['photo'] = data.get('PHOTO')
        
        if 'UNIVERSITYID' in data:
            fields.append("UNIVERSITYID = :universityid")
            values['universityid'] = data['UNIVERSITYID']
        
        if 'IDCARD' in data:
            fields.append("IDCARD = :idcard")
            values['idcard'] = data['IDCARD']
        
        if not fields:
            return jsonify({"error": "No se proporcionaron campos válidos para actualizar"}), 400

        # Unir los campos para formar la sentencia SQL
        sql = f"UPDATE PROFESSOR SET {', '.join(fields)} WHERE PROFESSORID = :professorid"
        values['professorid'] = professorid

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

@professor_bp.route('/professor/<int:professorid>', methods=['DELETE'])
def delete_professor(professorid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM PROFESSOR WHERE PROFESSORID = :professorid", {'professorid': professorid})
        conn.commit()
        return jsonify({"message": "Professor eliminado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error eliminando Professor")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
