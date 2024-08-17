import logging

from db_connection import get_db_connection

from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

face_bp = Blueprint('face', __name__)

@face_bp.route('/face', methods=['POST'])
def create_face():
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO FACE (TEACHERID, FACEIMAGE, FEATURES, NAME, PATH) 
            VALUES (:teacherid, :faceimage, :features, :name, :path)
            """, 
            {
                'teacherid': data['TEACHERID'],
                'faceimage': data['FACEIMAGE'],
                'features': data['FEATURES'],
                'name': data.get('NAME'),  # Es opcional
                'path': data.get('PATH')  # Es opcional
            }
        )
        conn.commit()
        return jsonify({"message": "Face creado exitosamente"}), 201
    except Exception as e:
        logger.exception("Error creando Face")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@face_bp.route('/face/<int:faceid>', methods=['GET'])
def get_face(faceid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM FACE WHERE FACEID = :faceid", {'faceid': faceid})
        face = cursor.fetchone()
        
        if face is None:
            return jsonify({"error": "Face no encontrado"}), 404
        
        return jsonify(dict(zip([key[0] for key in cursor.description], face))), 200
    except Exception as e:
        logger.exception("Error obteniendo Face")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@face_bp.route('/face/<int:faceid>', methods=['PUT'])
def update_face(faceid):
    try:
        data = request.json
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            UPDATE FACE 
            SET FACEIMAGE = :faceimage, FEATURES = :features, NAME = :name, PATH = :path
            WHERE FACEID = :faceid
            """,
            {
                'faceimage': data['FACEIMAGE'],
                'features': data['FEATURES'],
                'name': data.get('NAME'),
                'path': data.get('PATH'),
                'faceid': faceid
            }
        )
        conn.commit()
        return jsonify({"message": "Face actualizado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error actualizando Face")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@face_bp.route('/face/<int:faceid>', methods=['DELETE'])
def delete_face(faceid):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM FACE WHERE FACEID = :faceid", {'faceid': faceid})
        conn.commit()
        return jsonify({"message": "Face eliminado exitosamente"}), 200
    except Exception as e:
        logger.exception("Error eliminando Face")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()