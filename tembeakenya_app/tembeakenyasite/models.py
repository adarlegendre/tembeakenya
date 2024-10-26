import cx_Oracle

class OracleDatabase:
    @staticmethod
    def check_connection():
        try:
            lib_dir = r"C:\\oracle\\instantclient_23_5"
            try:
                cx_Oracle.init_oracle_client(lib_dir=lib_dir)
            except Exception as err:
                return "oracle init failed"
            # Define the DSN and credentials for the Oracle database
            dsn_tns = cx_Oracle.makedsn("gort.fit.vutbr.cz", 1521, service_name="orclpdb")
            connection = cx_Oracle.connect(user="xotiena00", password="LUAstazi", dsn=dsn_tns)
            
            # Test the connection by querying the database
            cursor = connection.cursor()
            cursor.execute("SELECT 1 FROM dual")  # A simple query to check connectivity
            cursor.fetchone()
            
            # Close the connection
            cursor.close()
            connection.close()
            
            return "Connection successful"
        except cx_Oracle.DatabaseError as e:
            return f"Connection failed: {e}"