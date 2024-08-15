import cx_Oracle


def get_db_connection():
    # Configuración de la conexión a la base de datos Oracle
    dsn = cx_Oracle.makedsn("localhost", 1521, service_name="ORCLPDB1")
    connection = cx_Oracle.connect(user="espe_system", password="admin", dsn=dsn)
    return connection

def insert_face_data(maestro_id, image_blob, embedding_str):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Preparar la consulta de inserción
        sql = """
        INSERT INTO Rostros (MaestroID, ImagenRostro, Caracteristicas)
        VALUES (:maestro_id, :image_blob, :embedding_str)
        """
        cursor.execute(sql, [maestro_id, image_blob, embedding_str])

        # Confirmar la transacción
        connection.commit()

    except cx_Oracle.DatabaseError as e:
        print(f"Error al insertar datos en la base de datos: {e}")
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()