# for local testing
source ../local.env
kubectl apply -f namespace.yaml
kubectl delete secret minio-credentials --ignore-not-found -n minio
kubectl create secret generic minio-credentials --from-literal=MINIO_ROOT_USER=$MINIO_ROOT_USER --from-literal=MINIO_ROOT_PASSWORD=$MINIO_ROOT_PASSWORD -n minio # define in Gitlab ENV
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml