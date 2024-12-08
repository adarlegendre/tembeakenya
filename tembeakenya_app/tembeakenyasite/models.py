import cx_Oracle
import logging
import json
import requests
import base64



# Initialize Oracle Client only once
lib_dir = r"..\\oracle\\instantclient_23_5"
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
            connection = cx_Oracle.connect(user="xotuyag00", password="0syIgeF2", dsn=dsn_tns)

            # Query to fetch attractions and SDO_GEOMETRY (converted to GeoJSON)
            query = """
                SELECT 
                    a.id, 
                    a.attraction_name, 
                    SDO_UTIL.TO_GEOJSON(a.shape) AS geojson,
                    i.photoblob
                FROM attractions a
                LEFT JOIN (
                    SELECT 
                        attraction_id, 
                        photoblob,
                        ROW_NUMBER() OVER (PARTITION BY attraction_id ORDER BY id) AS rn
                    FROM images
                ) i ON a.id = i.attraction_id AND i.rn = 1
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
            dsn_tns = cx_Oracle.makedsn("gort.fit.vutbr.cz", 1521, service_name="orclpdb")
            
            # Connect to the database
            with cx_Oracle.connect(user="xotuyag00", password="0syIgeF2", dsn=dsn_tns) as connection:
                
                # Prepare cursor to insert into images table
                with connection.cursor() as cursor:
                    query = """
                        INSERT INTO images (attraction_id, photo_url)
                        VALUES (:attraction_id, :photo_url)
                    """
                    cursor.execute(query, {
                        "attraction_id": attraction_id,
                        "photo_url": image_url
                    })
                    
                # Commit changes
                connection.commit()
                logging.info("Image inserted successfully for attraction_id: %s", attraction_id)
            
            return True  # Return True on success

        except Exception as e:
            logging.error(f"Error inserting image for attraction {attraction_id}: {e}")
            return False



    @staticmethod
    def update_image_for_attraction(attraction_id, new_image_url):
        """Updates an image related to a specific attraction."""
        try:
            # Define the DSN (Data Source Name) and credentials for Oracle DB connection
            dsn_tns = cx_Oracle.makedsn("gort.fit.vutbr.cz", 1521, service_name="orclpdb")
            connection = cx_Oracle.connect(user="xotuyag00", password="0syIgeF2", dsn=dsn_tns)

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
        """
        Fetches a tourist attraction by its name and calculates distance from Nairobi.
        """
        try:
            
            dsn_tns = cx_Oracle.makedsn("gort.fit.vutbr.cz", 1521, service_name="orclpdb")
            connection = cx_Oracle.connect(user="xotuyag00", password="0syIgeF2", dsn=dsn_tns)

            # Query to get the attraction details (including geojson)
            query = """
                SELECT id, attraction_name, category_id, 
                    SDO_UTIL.TO_GEOJSON(shape) AS geojson
                FROM attractions
                WHERE LOWER(attraction_name) = :attraction_name
            """
            cursor = connection.cursor()
            cursor.execute(query, {"attraction_name": attraction_name.lower()})
            result = cursor.fetchone()

            if result:
                logging.info(f"Attraction found: {result}")
                # Handle LOB for geojson
                geojson_lob = result[3]  # This is the LOB object
                if isinstance(geojson_lob, cx_Oracle.LOB):
                    geojson_str = geojson_lob.read()  # Read the LOB into a string
                else:
                    geojson_str = geojson_lob  # If it's already a string

                attraction_data = {
                    "id": result[0],
                    "attraction_name": result[1],
                    "category_id": result[2],
                    "geojson": json.loads(geojson_str) if geojson_str else None
                }

                # Query to calculate the distance from Nairobi (id = 7)
                distance_query = """
                    SELECT SDO_GEOM.SDO_DISTANCE(a1.shape, a2.shape, 0.005) AS distance
                    FROM attractions a1, attractions a2
                    WHERE a1.id = 7 AND a2.id = :target_id
                """
                cursor.execute(distance_query, {"target_id": attraction_data["id"]})
                distance_result = cursor.fetchone()

                if distance_result:
                    attraction_data["distance"] = distance_result[0]
                else:
                    attraction_data["distance"] = None

                    # Query to fetch all images associated with the attraction
                images_query = """
                    SELECT photoblob FROM images
                    WHERE attraction_id = :attraction_id
                """
                cursor.execute(images_query, {"attraction_id": attraction_data["id"]})
                images = []
                for row in cursor:
                    photo_blob = row[0]  # Assuming the image is stored as a BLOB
                    if photo_blob:
                        # Convert the BLOB to a Base64-encoded string
                        images.append(base64.b64encode(photo_blob.read()).decode('utf-8'))

                # Add images to the attraction data
                attraction_data["images"] = images
    

                cursor.close()
                connection.close()

                return attraction_data
            else:
                logging.warning(f"No attraction found with name: {attraction_name}")
                cursor.close()
                connection.close()
                return None
        except cx_Oracle.DatabaseError as e:
            logging.error(f"Database error while fetching attraction by name: {e}")
            return None
    @staticmethod
    def fetch_attraction_by_id(attraction_id):
        """
        Fetches an attraction by its ID along with associated images.
        """
        try:
            dsn_tns = cx_Oracle.makedsn("gort.fit.vutbr.cz", 1521, service_name="orclpdb")
            connection = cx_Oracle.connect(user="xotuyag00", password="0syIgeF2", dsn=dsn_tns)
            cursor = connection.cursor()

            # Query to fetch attraction details
            attraction_query = """
                SELECT id, attraction_name, category_id, SDO_UTIL.TO_GEOJSON(shape) AS geojson
                FROM attractions
                WHERE id = :attraction_id
            """
            cursor.execute(attraction_query, {"attraction_id": attraction_id})
            result = cursor.fetchone()

            if not result:
                logging.warning(f"No attraction found with ID {attraction_id}.")
                return None

            attraction_data = {
                "id": result[0],
                "attraction_name": result[1],
                "category_id": result[2],
                "geojson": result[3],  # If geojson is needed
            }

            # Query to fetch images for this attraction
            images_query = """
                SELECT id, photoblob FROM images
                WHERE attraction_id = :attraction_id
            """
            cursor.execute(images_query, {"attraction_id": attraction_id})
            images = []
            for row in cursor:
                image_id = row[0]
                photo_blob = row[1]
                if photo_blob:
                    base64_encoded = base64.b64encode(photo_blob.read()).decode('utf-8')
                    images.append({"id": image_id, "photo": base64_encoded})
            attraction_data["images"] = images

            cursor.close()
            connection.close()

            return attraction_data
        except Exception as e:
            logging.error(f"Error fetching attraction by ID {attraction_id}: {e}")
            return None
    @staticmethod
    def delete_image_by_id(image_id):
        """Deletes an image from the database by its image_id."""
        try:
            dsn_tns = cx_Oracle.makedsn("gort.fit.vutbr.cz", 1521, service_name="orclpdb")
            connection = cx_Oracle.connect(user="xotuyag00", password="0syIgeF2", dsn=dsn_tns)
            cursor = connection.cursor()

            # Delete the image from the images table using the image_id
            delete_query = """
                DELETE FROM images
                WHERE id = :image_id
            """
            cursor.execute(delete_query, {"image_id": image_id})

            # Commit the transaction
            connection.commit()

            # Close the cursor and connection
            cursor.close()
            connection.close()

            return True  # Return True if the image was successfully deleted
        except Exception as e:
            logging.error(f"Error deleting image with ID {image_id}: {e}")
            return False  # Return False if there was an error
    
    
    @staticmethod
    def update_image_by_id(image_id, new_image_url):
        """Updates an image's URL in the database by its image_id."""
        try:
            dsn_tns = cx_Oracle.makedsn("gort.fit.vutbr.cz", 1521, service_name="orclpdb")
            connection = cx_Oracle.connect(user="xotuyag00", password="0syIgeF2", dsn=dsn_tns)
            cursor = connection.cursor()

            # Update the image URL using the image_id
            update_query = """
                UPDATE images
                SET photo_url = :new_image_url
                WHERE id = :image_id
            """
            cursor.execute(update_query, {"new_image_url": new_image_url, "image_id": image_id})

            # Commit the transaction
            connection.commit()

            # Close the cursor and connection
            cursor.close()
            connection.close()

            return True  # Return True if the image was successfully updated
        except Exception as e:
            logging.error(f"Error updating image with ID {image_id}: {e}")
            return False  # Return False if there was an error    
   
