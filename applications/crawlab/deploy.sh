kubectl apply -f namespace.yaml
kubectl apply -f mongo-statefulset.yaml
kubectl apply -f mongo-service.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f redis-service.yaml
kubectl apply -f crawlab-deployment.yaml
kubectl apply -f crawlab-service.yaml