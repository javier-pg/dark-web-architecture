#!/bin/bash
source ../../local.env
sudo docker build -t auxdownloader:2.0 .
sudo docker tag auxdownloader:2.0 $PRIVATE_DOCKER_REGISTRY/breacher/auxdownloader:2.0
sudo docker push $PRIVATE_DOCKER_REGISTRY/breacher/auxdownloader:2.0
kubectl apply -f deployment.yaml