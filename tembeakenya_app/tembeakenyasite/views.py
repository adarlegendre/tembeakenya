from django.shortcuts import render
from django.template import loader
from django.shortcuts import render
from django.http import HttpResponse
from .models import OracleDatabase
import logging
import requests
import cx_Oracle


def index(request):
    query = request.GET.get('query', '').strip()
    logging.info(f"User input query: '{query}'")
    
    # Fetch the starting attraction (Nairobi, id=7)
    starting_attraction = OracleDatabase.fetch_tourist_attractions()
    starting_attraction = next((a for a in starting_attraction if a['id'] == 7), None)

    if not starting_attraction:
        logging.error("Starting attraction (Nairobi) not found in database.")
        return render(request, 'tembeakenyasite/index.html', {
            "sitename": "Welcome To Kenya",
            "attractions": [],
            "query": query,
            "distances": [],
        })

    distances = []
    target_attraction = None

    # Fetch the target attraction based on user input
    if query:
        target_attraction = OracleDatabase.fetch_attraction_by_name(query)

    if target_attraction:
        logging.info(f"Target attraction found: {target_attraction}")
        # Calculate the distance between Nairobi and the target attraction
        distances.append({
            'from': starting_attraction['attraction_name'],
            'to': target_attraction['attraction_name'],
            'distance': target_attraction.get('distance', 'Distance not available')
        })
        # Replace the attractions list with only the target attraction
        attractions = [target_attraction]
    else:
        logging.warning(f"No matching attraction found for query: '{query}'")
        attractions = []  # No attractions to display if query doesn't match

    context = {
        "sitename": "Welcome To Kenya",
        "attractions": attractions,
        "query": query,
        "distances": distances,
    }
    return render(request, 'tembeakenyasite/index.html', context)


def attraction_detail(request, attraction_name):
    # Get the tourist attraction by name from the Oracle database
    attraction = OracleDatabase.fetch_attraction_by_name(attraction_name)

    if attraction:
        # If attraction is found, pass it to the template
        context = {
            'attraction': attraction,
        }
        return render(request, 'tembeakenyasite/attraction_detail.html', context)
    else:
        # If no attraction is found, return an error page or a 404
        return render(request, 'tembeakenyasite/attraction_not_found.html')

def attraction_map(request):
    # Get the tourist attractions data from the Oracle database
    attractions = OracleDatabase.fetch_tourist_attractions()

    # Pass the attractions data to the template
    context = {
        'attractions': attractions,
    }

    # Render the HTML page
    return render(request, 'tembeakenyasite/attractions_map.html', context)

def insert_image_view(request):
    """View to insert an image for a specific attraction."""
    if request.method == 'POST':
        # Get form data from the POST request
        attraction_id = request.POST.get('attraction_id')
        image_url = request.POST.get('image_url')
        
        if attraction_id and image_url:
            try:
                # Set up logging
                logging.basicConfig(level=logging.DEBUG)
                
                # Define the DSN (Data Source Name) and credentials for Oracle DB connection
                dsn_tns = cx_Oracle.makedsn("gort.fit.vutbr.cz", 1521, service_name="orclpdb")
                connection = cx_Oracle.connect(user="xotuyag00", password="0syIgeF2", dsn=dsn_tns)

                try:
                    # Fetch the image data from the URL
                    response = requests.get(image_url)
                    response.raise_for_status()  # Raise an error for bad responses
                    image_data = response.content

                    # Prepare a cursor
                    cursor = connection.cursor()

                    # Check if the sequence 'images_seq' exists, and create it if necessary
                    try:
                        cursor.execute("SELECT sequence_name FROM user_sequences WHERE sequence_name = 'IMAGES_SEQ'")
                        seq_exists = cursor.fetchone()

                        if not seq_exists:
                            # If the sequence does not exist, create it
                            cursor.execute("""
                                CREATE SEQUENCE images_seq
                                START WITH 1
                                INCREMENT BY 1
                                NOMAXVALUE
                                NOCYCLE
                                CACHE 20
                            """)
                            logging.info("Sequence 'images_seq' created successfully.")
                    except cx_Oracle.DatabaseError as e:
                        logging.error(f"Error checking/creating sequence: {e}")
                        return HttpResponse("Database error while checking/creating sequence.")

                    # Insert a new row with a placeholder BLOB object
                    query_init = """
                        INSERT INTO images (id, attraction_id, photoblob)
                        VALUES (images_seq.NEXTVAL, :attraction_id, NULL)
                        RETURNING id INTO :image_id
                    """
                    # Create a variable to store the generated ID
                    image_id = cursor.var(int)
                    cursor.execute(query_init, {"attraction_id": attraction_id, "image_id": image_id})

                    # Get the inserted image ID
                    inserted_image_id = image_id.getvalue()[0]

                    # Now we know the ID of the inserted image, we can safely lock the row for update
                    query_select = """
                        SELECT photoblob
                        FROM images
                        WHERE id = :image_id
                        FOR UPDATE
                    """
                    cursor.execute(query_select, {"image_id": inserted_image_id})
                    row = cursor.fetchone()

                    # If row is None, it means the query didn't find the inserted row
                    if row is None:
                        return HttpResponse("Error: Image row not found for update.")

                    # Initialize a BLOB object
                    blob_image = cursor.var(cx_Oracle.BLOB)  # Using BLOB instead of ORDIMAGE

                    # Set image data into BLOB object
                    blob_image.setvalue(0, image_data)

                    # Update the BLOB object in the database
                    cursor.execute("""
                        UPDATE images SET photoblob = :blob_image WHERE id = :image_id
                    """, {
                        "blob_image": blob_image,
                        "image_id": inserted_image_id
                    })

                    # Commit the transaction
                    connection.commit()

                    # Close the cursor and connection
                    cursor.close()
                    connection.close()

                    return HttpResponse("Image inserted successfully!")

                except requests.exceptions.RequestException as req_err:
                    return HttpResponse(f"Request error occurred: {req_err}")
                except cx_Oracle.DatabaseError as db_err:
                    error, = db_err.args
                    return HttpResponse(f"Database error occurred: {error.message}")
                except Exception as e:
                    return HttpResponse(f"Unexpected error while inserting image: {e}")
                
            except Exception as e:
                logging.error(f"Error inserting image: {e}")
                return HttpResponse(f"Error inserting image: {e}")
        else:
            return HttpResponse("Please provide both attraction ID and image URL.")

    return render(request, 'tembeakenyasite/insert_image.html')



