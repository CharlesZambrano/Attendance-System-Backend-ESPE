import cx_Oracle


def get_db_connection():
    """
    Establece y devuelve una conexión a la base de datos Oracle.
    """
    try:
        # Configuración de la conexión a la base de datos Oracle
        dsn = cx_Oracle.makedsn("oracle-db", 1521, service_name="ORCLPDB1")
        connection = cx_Oracle.connect(user="espe_system", password="admin", dsn=dsn)
        return connection
    except cx_Oracle.DatabaseError as e:
        print(f"Error al conectarse a la base de datos: {e}")
        raise

def insert_face_data(maestro_id, image_blob, embedding_str):
    """
    Inserta datos faciales en la tabla Rostros.
    """
    connection = None
    cursor = None
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
        print("Datos insertados correctamente.")
    except cx_Oracle.DatabaseError as e:
        print(f"Error al insertar datos en la base de datos: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()