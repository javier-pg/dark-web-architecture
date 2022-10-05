source ../local.env
sed -i 's/MINIO_PASSWORD/'"$MINIO_PASSWORD"'/' minio-dev.yaml
sed -i 's/MINIO_USER/'"$MINIO_USER"'/' minio-dev.yaml
kubectl apply -f minio-dev.yaml
sed -i 's/'"$MINIO_PASSWORD"'/MINIO_PASSWORD/' minio-dev.yaml
sed -i 's/'"$MINIO_USER"'/MINIO_USER/' minio-dev.yaml
