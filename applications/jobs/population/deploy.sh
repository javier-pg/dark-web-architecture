#!/bin/bash
source ../../../local.env
sudo docker build -t auxdownloader:1.0 .
sudo docker tag auxdownloader:1.0 $PRIVATE_DOCKER_REGISTRY/breacher/auxdownloader:1.0
sudo docker push $PRIVATE_DOCKER_REGISTRY/breacher/auxdownloader:1.0
kubectl apply -f deployment.yaml