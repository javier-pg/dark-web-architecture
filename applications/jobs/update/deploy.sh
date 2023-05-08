#!/bin/bash
source ../../../local.env
sudo docker build -t update:1.0 .
sudo docker tag update:1.0 $PRIVATE_DOCKER_REGISTRY/breacher/update:1.0
sudo docker push $PRIVATE_DOCKER_REGISTRY/breacher/update:1.0
kubectl apply -f deployment.yaml