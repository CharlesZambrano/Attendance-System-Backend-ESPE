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