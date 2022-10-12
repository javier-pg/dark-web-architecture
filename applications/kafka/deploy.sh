source ../local.env
sudo helm repo add bitnami https://charts.bitnami.com/bitnami
kubectl create namespace kafka
sudo docker build -t kafka:1.0 .
sudo docker tag kafka:1.0 $PRIVATE_DOCKER_REGISTRY/breacher/kafka:1.0
sudo docker push $PRIVATE_DOCKER_REGISTRY/breacher/kafka:1.0
sed -i 's/PRIVATE_DOCKER_REGISTRY/'"$PRIVATE_DOCKER_REGISTRY"'/' values.yaml
sed -i 's/KAFKA_PASSWORD/'"$KAFKA_PASSWORD"'/' values.yaml
sudo helm install kafka bitnami/kafka -f values.yaml --version 14.9.3 -n kafka
sed -i 's/'"$PRIVATE_DOCKER_REGISTRY"'/PRIVATE_DOCKER_REGISTRY/' values.yaml
sed -i 's/'"$KAFKA_PASSWORD"'/KAFKA_PASSWORD/' values.yaml
# kubectl run kafka-client --restart='Never' --image docker.io/bitnami/kafka:2.8.1-debian-10-r99 --namespace kafka --command sleep infinity
# kubectl exec --stdin --tty -n kafka kafka-client -- /bin/bash
# $ kafka-console-consumer.sh --bootstrap-server kafka.kafka.svc.cluster.local:9092 --topic crawlab_test.results_onions_farmer
