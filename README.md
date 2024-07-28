# Multimodal AI Image Search using AMD Radeon GPU
This is part of a LLaVA Multimodal Image Search Project I put together for AMD and Hackerster.io's Pervasive AI Developer Contest. A more detailed write of this project can be found here: https://www.hackster.io/juliea/llava-multimodel-image-search-dfaee3 

![Multimodal Image Search Diagram](multimodal-image-search-diagram.png)


## Dataset Used
The dataset used for this project is a small subset (200 images) of the Princeton Vision & Robotics SUN (***S**cene **UN**derstanding) dataset which can be found [here](https://vision.princeton.edu/projects/2010/SUN/). Since the original dataset is very large and comprised of 130,519 images this much small mini dataset of images was created and can be found on HuggingFace: https://huggingface.co/datasets/julieax/SUN-mini

## Requirements
You will need the following installed and setup before you can run this project:
- AMD Radeon GPU
- AMD ROCm (preferrably 6.1.x+)
- PyTorch+ROCm
- Ollama
- Photoprism (or any other photo organization/sharing app)

## Running the Multimodal Image Processing script
1. Install the required python pip pacakges:
```
pip install -r requirements.txt
```
2. Update the dataset name and directory path in the `multimodal-image-tagger.py` file to point to the image folder you would like to process.

3. Run the python image processing script and watch it process your image files. Be sure to change the `--image_folder_name` and `--image_folder_path` to reflect the images you want to process.
```
python3 multimodal-image-tagger.py --image_folder_name="SUN-mini" --image_folder_path="/home/$USER/Documents/multimodal-ai-image-search/SUN-mini"
```

## Using Processed Images with Photoprism via Docker
Once the images have been processed via the `multimodal-image-tagger.py` script you can upload the processed images to a photo organization app such as [Photoprism](https://docs.photoprism.app/). This is an example of how to run Photoprism locally via Docker:
```bash
docker run -d \
  --name photoprism \
  --security-opt seccomp=unconfined \
  --security-opt apparmor=unconfined \
  -p 2342:2342 \
  -e PHOTOPRISM_UPLOAD_NSFW="true" \
  -e PHOTOPRISM_ADMIN_PASSWORD="insecure" \
  -v /photoprism/storage \
  -v ~/Pictures/photoprism:/photoprism/originals \
  photoprism/photoprism
  ```

  The description and keyword EXIF data created by the image tagger script can now be used to easily search through your images to make it easier to organize and find the photos you are looking for.