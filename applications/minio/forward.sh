# for local forwarding
source ../local.env
kubectl port-forward -n minio --address $MINIO_IPADDRESS pod/minio 9011:9010
