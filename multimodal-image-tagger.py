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
#logging.basicConfig(level=logging.INFO)

# Alternatively to enable debugging you can run the script with 
# python -m logging.basicConfig(level=logging.DEBUG) photofinder-process-images.py

# Create a SQLite database connection
conn = sqlite3.connect('image_keywords.db')
cursor = conn.cursor()

# Create a table if it doesn't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS image_keywords
                  (filename TEXT, keywords TEXT)''')

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
    # Check if the file is an image (e.g., .jpg,2012,, in PNG)
    logger.info(f"Processing {filename}...")
    
    # Open the image file in binary mode
    with open(os.path.join(dir_path, filename), 'rb') as f:
        # Read the entire file into a bytes object
        image_data = f.read()
        
    # Base64 encode the image data
    encoded_image = base64.b64encode(image_data)

    # Create the JSON payload for the API request
    payload = {
        "model": "llava:34b",
        "prompt": "Please provide a list of keywords that describes this image. Only return a comma seperated list of keywords and nothing else.",
        "stream": False,
        "images": [encoded_image.decode("utf-8")]
    }

    # Convert the payload to JSON format
    json_payload = json.dumps(payload)

    # Send a POST request to the API endpoint
    response = requests.post('http://localhost:11434/api/generate', data=json_payload, headers={'Content-Type': 'application/json'})

    # Check if the response was successful (200 OK)
    if response.status_code == 200:
        data = response.json()
        keywords = data['response']
        logger.info(keywords) # Print the API response

        filepath = dir_path+filename
        # Check if an entry with the same filename already exists in the table
        cursor.execute("SELECT 1 FROM image_keywords WHERE filename = ?", (filepath,))
        if cursor.fetchone():
            # If an entry exists, update its keywords
            cursor.execute("UPDATE image_keywords SET keywords = ? WHERE filename = ?", (data['response'], filepath))
        else:
            # If no entry exists, insert a new one
            cursor.execute("INSERT INTO image_keywords (filename, keywords) VALUES (?, ?)", (filepath, data['response']))
        conn.commit()
        logger.info(f"Saved keywords for {filename} to database successfully!")

    else:
        logger.error(f"Error sending request for {filename}: {response.text}")

    try:
        # Save the updated EXIF data back to the image file
        with exiftool.ExifToolHelper() as et:
            # Execute the exiftool
            et.execute(
                    f'-Description={keywords}',
                    f'-ImageDescription={keywords}',
                    f'-Keywords={keywords}',
                    *[filepath]
                )
            # Check the metadata if log level set to INFO
            if logger.getEffectiveLevel() <= logging.INFO:
                metadata = et.get_metadata(filepath)
                for file, data in zip(filepath, metadata):
                    logger.info(f"{file}:{data}")
                logger.info(f"EXIF data for {filename} updated successfully!")
                
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
