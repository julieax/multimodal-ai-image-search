import os
import base64
import requests
import json
import sqlite3

# Create a SQLite database connection
conn = sqlite3.connect('image_keywords.db')
cursor = conn.cursor()

# Create a table if it doesn't exist
cursor.execute('''CREATE TABLE IF NOT EXISTS image_keywords
                  (filename TEXT, keywords TEXT)''')

# Set the directory path
dir_path = f"/home/{os.getlogin()}/Pictures/"
filenames = os.listdir(dir_path)
print(f"{len(filenames)} files found: {filenames}")

# Iterate through all files in the directory
for filename in os.listdir(dir_path):
    # Check if the file is an image (e.g., .jpg,2012,, in PNG)
    if filename.endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
        print(f"Processing {filename}...")
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
            print(data['response']) # Print the API response

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
            print(f"Saved keywords for {filename} to database successfully!")

        else:
            print(f"Error sending request for {filename}: {response.text}")

    else:
        print(f'Skipping unsupported image format: {filename}')

# Close the SQLite database connection
conn.close()