# aiphotofinder
Photo organisation app using multi-modal LLaVa model 

# Dataset
https://huggingface.co/datasets/julieax/SUN-mini

# Using AI Photofinder with Photo Prism Docker container
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