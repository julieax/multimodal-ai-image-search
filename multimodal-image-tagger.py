import os
import base64
import requests
import json
import logging
import sqlite3
import exiftool
import shutil
from tqdm import tqdm

# Create a logger
logger = logging.getLogger(__name__)

# Uncomment below line if you want to enable INFO messages
# logging.basicConfig(level=logging.INFO)

# Create a SQLite database connection
conn = sqlite3.connect('image_database.db')
cursor = conn.cursor()

# Create a table if it doesn't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS image_database
                  (filename TEXT, description TEXT, keywords TEXT)''')

# Set the directory path
dataset_name = "SUN-mini"
dir_path = os.path.join(f"/home/{os.getlogin()}/Documents/aiphotofinder/", dataset_name)
logger.info(f"Dataset Path: {dir_path}")

filenames = os.listdir(dir_path)
logger.info(f"{len(filenames)} files found: {filenames}")

# Filter out non-image files
image_filenames = [filename for filename in filenames if filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))]

# Create a progress bar
pbar = tqdm(total=len(image_filenames), desc='Processing images')

for filename in image_filenames:
    logger.info(f"Processing {filename}...")
    
    # Open the image file in binary mode
    with open(os.path.join(dir_path, filename), 'rb') as f:
        # Read the entire file into a bytes object
        image_data = f.read()
        
    # Base64 encode the image data
    encoded_image = base64.b64encode(image_data)

    # Create the JSON payload for the API request to get list of keywords for image
    keywords_payload = {
        "model": "llava:34b",
        "prompt": "Please provide a list of keywords that describes this image. Only return a comma seperated list of keywords and nothing else.",
        "stream": False,
        "images": [encoded_image.decode("utf-8")]
    }

    # Convert the payload to JSON format
    keywords_json_payload = json.dumps(keywords_payload)

    # Send a POST request to the API endpoint
    keywords_response = requests.post('http://localhost:11434/api/generate', data=keywords_json_payload, headers={'Content-Type': 'application/json'})

    if keywords_response.status_code == 200:
        keywords_data = keywords_response.json()
        keywords = keywords_data['response']
        logger.info(keywords) # Print the API response

        # Create the JSON payload for the API request to get short description of image
        description_payload = {
            "model": "llava:34b",
            "prompt": "Please provide a short description of this image. Do not start with this image depicts, this is an image of, etc. and just provide the description. It must be two sentances long.",
            "stream": False,
            "images": [encoded_image.decode("utf-8")]
        }

        # Convert the payload to JSON format
        description_json_payload = json.dumps(description_payload)

        # Send a POST request to the API endpoint
        description_response = requests.post('http://localhost:11434/api/generate', data=description_json_payload, headers={'Content-Type': 'application/json'})

        # Check if the response was successful (200 OK)
        if description_response.status_code == 200:

            description_data = description_response.json()
            description = description_data['response']
            logger.info(description) # Print the API response

            filepath = dir_path+'/'+filename
            # Check if an entry with the same filename already exists in the table
            cursor.execute("SELECT 1 FROM image_database WHERE filename = ?", (filepath,))
            if cursor.fetchone():
                # If an entry exists, update its keywords
                cursor.execute("UPDATE image_database SET description = ?, keywords = ? WHERE filename = ?", (description, keywords, filepath))
            else:
                # If no entry exists, insert a new one
                cursor.execute("INSERT INTO image_database (filename, description, keywords) VALUES (?, ?, ?)", (filepath, description, keywords))
            conn.commit()
            logger.info(f"Saved keywords and description for {filename} to database successfully!")

        else:
            logger.error(f"Error sending description request for {filename}: {description_response.text}")

    try:
        # Save the updated EXIF data back to the image file
        if not os.path.exists(filepath):
            logger.error(f"File {filepath} does not exist")
        else:
            with exiftool.ExifToolHelper() as et:
                try:
                    # Execute the exiftool
                    et.execute(
                        f'-Description={description}',
                        f'-ImageDescription={description}',
                        f'-Keywords={keywords}',
                        filepath  # Pass filepath directly, don't use *[filepath]
                    )
                    logger.info(f"EXIF data for {filename} updated successfully!")
                except Exception as e:
                    logger.error(f"Error updating EXIF data for {filename}: {str(e)}")

                
    except Exception as e:
        logger.error(f"Error updating EXIF data for {filename}: {str(e)}")


    # Update the progress bar
    pbar.update(1)

# Close the SQLite database connection
conn.close()
pbar.close()

# Create a new processed folder name by combining the dataset folder name with '-processed'
processed_folder_name = f"{dataset_name}-processed"

# Create the new processed folder in parent directory if it doesn't exist
parent_dir = os.path.dirname(dir_path)
new_processed_dir = os.path.join(parent_dir, processed_folder_name)
print(new_processed_dir)

if not os.path.exists(new_processed_dir):
    os.makedirs(new_processed_dir)

# Move processed files to the new 'processed' folder
for filename in os.listdir(dir_path):
    if filename.endswith('.jpg'):
        shutil.move(os.path.join(dir_path, filename), os.path.join(new_processed_dir, filename))

# Rename original files back to their .jpg extension
for filename in os.listdir(dir_path):
    if filename.endswith('.jpg_original'):
        new_filename = filename.replace(".jpg_original", ".jpg")
        shutil.move(os.path.join(dir_path, filename), os.path.join(dir_path, new_filename))
