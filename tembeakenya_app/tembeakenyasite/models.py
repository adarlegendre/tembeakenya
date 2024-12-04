import cx_Oracle
import logging
import json
import requests

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
    def insert_image_for_attraction(attraction_id, image_url):
        """Inserts a new image for a given attraction."""
        try:
            # Step 1: Define the DSN (Data Source Name) and credentials for Oracle DB connection
            dsn_tns = cx_Oracle.makedsn("gort.fit.vutbr.cz", 1521, service_name="orclpdb")
            
            # Step 2: Connect to the Oracle Database
            with cx_Oracle.connect(user="xotiena00", password="LUAstazi", dsn=dsn_tns) as connection:
                
                # Step 3: Fetch the image data from the URL
                response = requests.get(image_url)
                response.raise_for_status()  # Raise an error for bad responses
                image_data = response.content

                # Step 4: Prepare a cursor for inserting into the images table
                with connection.cursor() as cursor:
                    # Step 5: Prepare the SQL query to insert a new image
                    query = """
                        INSERT INTO images (attraction_id, photo)
                        VALUES (:attraction_id, :photo)
                    """

                    # Step 6: Execute the insert query with the parameters
                    cursor.execute(query, {
                        "attraction_id": attraction_id,
                        "photo": image_data
                    })

                # Step 7: Commit the transaction
                connection.commit()

            logging.info("Image inserted successfully for attraction_id: %s", attraction_id)

        except requests.exceptions.RequestException as req_err:
            logging.error(f"Failed to fetch image from URL: {image_url}. Error: {req_err}")
        except cx_Oracle.DatabaseError as db_err:
            error, = db_err.args
            logging.error(f"Database error occurred: {error.message}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")


    @staticmethod
    def update_image_for_attraction(attraction_id, new_image_url):
        """Updates an image related to a specific attraction."""
        try:
            # Define the DSN (Data Source Name) and credentials for Oracle DB connection
            dsn_tns = cx_Oracle.makedsn("gort.fit.vutbr.cz", 1521, service_name="orclpdb")
            connection = cx_Oracle.connect(user="xotiena00", password="LUAstazi", dsn=dsn_tns)

            # Fetch the new image data from the URL
            response = requests.get(new_image_url)
            response.raise_for_status()  # Raise an error for bad responses
            new_image_data = response.content

            # Prepare a cursor for updating the image in the images table
            cursor = connection.cursor()

            # Prepare the SQL query to update the image for the specific attraction
            query = """
                UPDATE images
                SET photo = :photo, photo_si = :photo_si, photo_ac = :photo_ac,
                    photo_ch = :photo_ch, photo_pc = :photo_pc, photo_tx = :photo_tx
                WHERE attraction_id = :attraction_id
            """

            # Convert image data to Oracle types (ORDImage, SI_StillImage, etc.)
            ord_image = cx_Oracle.Binary(new_image_data)  # This will be the BLOB that stores the image
            # As before, you would ideally convert the BLOB data into Oracle types for the other fields
            photo_si = ord_image  # Here for simplicity, we're using the same for all
            photo_ac = ord_image
            photo_ch = ord_image
            photo_pc = ord_image
            photo_tx = ord_image

            # Execute the update query with the parameters
            cursor.execute(query, {
                "photo": ord_image,
                "photo_si": photo_si,
                "photo_ac": photo_ac,
                "photo_ch": photo_ch,
                "photo_pc": photo_pc,
                "photo_tx": photo_tx,
                "attraction_id": attraction_id
            })

            # Commit the transaction
            connection.commit()

            # Close the cursor and connection
            cursor.close()
            connection.close()

            print("Image updated successfully!")

        except Exception as e:
            logging.error(f"Unexpected error while updating image: {e}")
            return None

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


    
    

   
