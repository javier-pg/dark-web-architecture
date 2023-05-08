#!/bin/bash
source ../../local.env
sudo docker build -t first_identification:2.0 .
sudo docker tag first_identification:2.0 $PRIVATE_DOCKER_REGISTRY/breacher/first_identification:2.0
sudo docker push $PRIVATE_DOCKER_REGISTRY/breacher/first_identification:2.0
kubectl apply -f deployment.yaml