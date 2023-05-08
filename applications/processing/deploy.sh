#!/bin/bash
source ../local.env
sudo docker build -t processing:1.0 .
sudo docker tag processing:1.0 $PRIVATE_DOCKER_REGISTRY/breacher/processing:1.0
sudo docker push $PRIVATE_DOCKER_REGISTRY/breacher/processing:1.0
kubectl apply -f deployment.yaml