source ../local.env
sudo docker build -t oniondownloader:2.0 .
sudo docker tag oniondownloader:2.0 $PRIVATE_DOCKER_REGISTRY/breacher/oniondownloader:2.0
sudo docker push $PRIVATE_DOCKER_REGISTRY/breacher/oniondownloader:2.0
kubectl apply -f namespace.yaml
kubectl delete secret minio-credentials --ignore-not-found -n oniondownloader
kubectl create secret generic minio-credentials --from-literal=MINIO_ONION_ACCESS_KEY=$MINIO_ONION_ACCESS_KEY --from-literal=MINIO_ONION_SECRET_KEY=$MINIO_ONION_SECRET_KEY -n oniondownloader # define in Gitlab ENV
kubectl apply -f deployment.yaml
kubectl apply -f mongo-statefulset.yaml
kubectl apply -f mongo-service.yaml