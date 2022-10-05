docker build -t sparkjob:1.0 .
docker tag sparkjob:1.0 $PRIVATE_DOCKER_REGISTRY/breacher/sparkjob:1.0
docker push $PRIVATE_DOCKER_REGISTRY/breacher/sparkjob:1.0
sed -i 's/PRIVATE_DOCKER_REGISTRY/'"$PRIVATE_DOCKER_REGISTRY"'/' k8s.yml
kubectl apply -f k8s.yml -n spark
sed -i 's/'"$PRIVATE_DOCKER_REGISTRY"'/PRIVATE_DOCKER_REGISTRY/' k8s.yml