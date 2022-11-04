# for local forwarding
kubectl port-forward -n minio --address 10.10.10.111 pod/minio 9011:9010
