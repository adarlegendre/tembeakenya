import cx_Oracle
import logging
import json

# Initialize Oracle Client only once
lib_dir = r"C:\\oracle\\instantclient_23_5"
try:
    cx_Oracle.init_oracle_client(lib_dir=lib_dir)
except Exception as err:
    logging.error(f"Oracle client initialization failed: {err}")
    raise  # If initialization fails, raise an error to stop the program

class OracleDatabase:
    @staticmethod
    def fetch_tourist_attractions():
        """Fetches tourist attraction data from the database including SDO_GEOMETRY and scales the coordinates."""
        try:
            # Define the DSN (Data Source Name) and credentials for Oracle DB connection
            dsn_tns = cx_Oracle.makedsn("gort.fit.vutbr.cz", 1521, service_name="orclpdb")
            connection = cx_Oracle.connect(user="xotiena00", password="LUAstazi", dsn=dsn_tns)

            # Query to fetch attractions and SDO_GEOMETRY (converted to GeoJSON)
            query = """
                SELECT id, attraction_name, 
                       SDO_UTIL.TO_GEOJSON(shape) as geojson
                FROM attractions 
            """
            cursor = connection.cursor()
            cursor.execute(query)
            
            # Fetch all results
            attractions = cursor.fetchall()

            # Convert query results into a list of dictionaries
            attractions_data = []
            for attraction in attractions:
                geojson_lob = attraction[2]  # LOB object for geojson

                # Read LOB to get the string value (if the column is of type LOB)
                if isinstance(geojson_lob, cx_Oracle.LOB):
                    geojson_str = geojson_lob.read()  # Read the LOB
                    # If the result is bytes, decode to string
                    if isinstance(geojson_str, bytes):
                        geojson_str = geojson_str.decode('utf-8')  # Decode bytes to string
                else:
                    geojson_str = geojson_lob  # In case it's already a string

                # Convert the GeoJSON string to a dictionary
                attraction_data = {
                    "id": attraction[0],
                    "attraction_name": attraction[1],
                    "geojson": json.loads(geojson_str)  # Now you can safely parse the JSON
                }

                # Scale down the geometry coordinates by 60%
                attraction_data["geojson"] = OracleDatabase.scale_geojson(attraction_data["geojson"])

                attractions_data.append(attraction_data)
            
            # Close the cursor and connection
            cursor.close()
            connection.close()

            logging.info(f"Fetched and scaled tourist attractions data: {attractions_data}")
            return attractions_data
        
        except Exception as e:
            logging.error(f"Unexpected error while fetching tourist attractions: {e}")
            return []

    @staticmethod
    def scale_geojson(geojson_data):
        """Scales down the geometry coordinates by 60%."""
        def scale_coordinates(coords, scale_factor=0.01):
            """Scales the coordinates of the geometry."""
            if isinstance(coords[0], list):  # This handles multipoint, polygon, etc.
                return [scale_coordinates(c, scale_factor) for c in coords]
            else:  # This handles point type (x, y)
                return [coord * scale_factor for coord in coords]

        # Check if the GeoJSON is a valid geometry with coordinates
        if 'type' in geojson_data and 'coordinates' in geojson_data:
            geojson_data['coordinates'] = scale_coordinates(geojson_data['coordinates'])
        
        return geojson_data

    @staticmethod
    def fetch_attraction_by_name(attraction_name):
        """Fetches a tourist attraction by its name."""
        try:
            # Define the DSN (Data Source Name) and credentials for Oracle DB connection
            dsn_tns = cx_Oracle.makedsn("gort.fit.vutbr.cz", 1521, service_name="orclpdb")
            connection = cx_Oracle.connect(user="xotiena00", password="LUAstazi", dsn=dsn_tns)

            # Query to fetch a single attraction by its name
            query = """
                SELECT id, attraction_name, category_id, city, 
                       SDO_UTIL.TO_GEOJSON(shape) as geojson
                FROM attractions
                WHERE attraction_name = :attraction_name
            """
            cursor = connection.cursor()
            cursor.execute(query, {"attraction_name": attraction_name})
            
            # Fetch the result
            attraction = cursor.fetchone()
            
            if attraction:
                # Read LOB to get the string value (if the column is of type LOB)
                geojson_lob = attraction[4]  # LOB object for geojson

                if isinstance(geojson_lob, cx_Oracle.LOB):
                    geojson_str = geojson_lob.read()  # Read the LOB
                    # If the result is bytes, decode to string
                    if isinstance(geojson_str, bytes):
                        geojson_str = geojson_str.decode('utf-8')  # Decode bytes to string
                else:
                    geojson_str = geojson_lob  # In case it's already a string

                # Convert the result into a dictionary
                attraction_data = {
                    "id": attraction[0],
                    "attraction_name": attraction[1],
                    "category_id": attraction[2],
                    "city": attraction[3],
                    "geojson": json.loads(geojson_str)  # Now you can safely parse the JSON
                }

                # Close the cursor and connection
                cursor.close()
                connection.close()

                return attraction_data
            else:
                # No attraction found
                cursor.close()
                connection.close()
                return None
        
        except Exception as e:
            logging.error(f"Unexpected error while fetching attraction by name: {e}")
            return None

   
