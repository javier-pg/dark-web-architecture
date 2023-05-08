#!/bin/bash
source ../../local.env
sudo docker build -t update:2.0 .
sudo docker tag update:2.0 $PRIVATE_DOCKER_REGISTRY/breacher/update:2.0
sudo docker push $PRIVATE_DOCKER_REGISTRY/breacher/update:2.0
kubectl apply -f deployment.yaml