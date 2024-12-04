import cx_Oracle
import logging
import json
import requests
import base64


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
                SELECT 
                    a.id, 
                    a.attraction_name, 
                    SDO_UTIL.TO_GEOJSON(a.shape) AS geojson,
                    i.photoblob  -- Selecting just one image for each attraction
                FROM attractions a
                LEFT JOIN (
                    SELECT 
                        attraction_id, 
                        photoblob
                    FROM images
                    WHERE ROWNUM = 1  -- Get only one image per attraction (first image found)
                ) i ON a.id = i.attraction_id
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

                # Convert the photo BLOB to a base64 encoded string
                photo_blob = attraction[3]  # BLOB data for the photo
                if photo_blob:
                    base64_encoded = base64.b64encode(photo_blob.read()).decode('utf-8')
                else:
                    base64_encoded = "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"  # In case there is no photo available

                # Create the dictionary for the attraction
                attraction_data = {
                    "id": attraction[0],
                    "attraction_name": attraction[1],
                    "geojson": json.loads(geojson_str),  # Parse the GeoJSON string into a dictionary
                    "photo": base64_encoded,  # Base64 encoded photo
                }

                # Scale down the geometry coordinates by 60% (assuming this method exists)
                attraction_data["geojson"] = OracleDatabase.scale_geojson(attraction_data["geojson"])

                # Add the attraction data to the list
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


    
    

   
