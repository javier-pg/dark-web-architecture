source ../local.env
sudo helm repo add bitnami https://charts.bitnami.com/bitnami
kubectl create namespace kafka
sudo docker build -t kafka:1.0 .
sudo docker tag kafka:1.0 $PRIVATE_DOCKER_REGISTRY/breacher/kafka:1.0
sudo docker push $PRIVATE_DOCKER_REGISTRY/breacher/kafka:1.0
sudo helm install kafka bitnami/kafka -f values.yaml --version 14.9.3 -n kafka
kubectl exec -n kafka kafka-0 -- kafka-topics.sh --alter --bootstrap-server localhost:9092 --topic crawlab_test.results_onions_farmer --partitions 10
# kafka-topics.sh --bootstrap-server localhost:9092 --topic crawlab_test.results_gateways --create --partitions 10
# kafka-topics.sh --topic crawlab_test.results_onions_farmer  --bootstrap-server localhost:9092 --delete
