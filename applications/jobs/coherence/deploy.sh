#!/bin/bash
source ../../../local.env
sudo docker build -t coherence:1.0 .
sudo docker tag coherence:1.0 $PRIVATE_DOCKER_REGISTRY/breacher/coherence:1.0
sudo docker push $PRIVATE_DOCKER_REGISTRY/breacher/coherence:1.0
kubectl apply -f deployment.yaml