#!/bin/bash
source ../../local.env
sudo docker build -t downloaded:1.0 .
sudo docker tag downloaded:1.0 $PRIVATE_DOCKER_REGISTRY/breacher/downloaded:1.0
sudo docker push $PRIVATE_DOCKER_REGISTRY/breacher/downloaded:1.0
kubectl apply -f deployment.yaml