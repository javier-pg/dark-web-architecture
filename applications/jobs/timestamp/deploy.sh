#!/bin/bash
source ../../../local.env
sudo docker build -t timestamp:1.0 .
sudo docker tag timestamp:1.0 $PRIVATE_DOCKER_REGISTRY/breacher/timestamp:1.0
sudo docker push $PRIVATE_DOCKER_REGISTRY/breacher/timestamp:1.0
kubectl apply -f deployment.yaml