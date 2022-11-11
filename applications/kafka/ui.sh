sudo helm repo add kafka-ui https://provectus.github.io/kafka-ui
sudo helm install kafka-ui kafka-ui/kafka-ui --set envs.config.KAFKA_CLUSTERS_O_NAME=local --set envs.config.KAFKA_CLUSTERS_O_NAME_BOOTSTRAPSERVER=kafka:9092 --namespace kafka
kubectl port-forward svc/kafka-ui 8090:80