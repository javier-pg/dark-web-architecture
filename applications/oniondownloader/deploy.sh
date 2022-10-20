source ../local.env
sudo docker build -t oniondownloader:1.0 .
sudo docker tag oniondownloader:1.0 $PRIVATE_DOCKER_REGISTRY/breacher/oniondownloader:1.0
sudo docker push $PRIVATE_DOCKER_REGISTRY/breacher/oniondownloader:1.0
sed -i 's/PRIVATE_DOCKER_REGISTRY/'"$PRIVATE_DOCKER_REGISTRY"'/' oniondownloader.yaml
sed -i 's/MINIO_ACCESS_KEY/'"$MINIO_ACCESS_KEY"'/' oniondownloader.yaml
sed -i 's/MINIO_SECRET_KEY/'"$MINIO_SECRET_KEY"'/' oniondownloader.yaml
sed -i 's/MINIO_API_ENDPOINT/'"$MINIO_API_ENDPOINT"'/' oniondownloader.yaml
kubectl apply -f ns.yaml
kubectl apply -f oniondownloader.yaml
sed -i 's/'"$PRIVATE_DOCKER_REGISTRY"'/PRIVATE_DOCKER_REGISTRY/' oniondownloader.yaml
sed -i 's/'"$MINIO_ACCESS_KEY"'/MINIO_ACCESS_KEY/' oniondownloader.yaml
sed -i 's/'"$MINIO_SECRET_KEY"'/MINIO_SECRET_KEY/' oniondownloader.yaml
sed -i 's/'"$MINIO_API_ENDPOINT"'/MINIO_API_ENDPOINT/' oniondownloader.yaml