# for local forwarding
kubectl port-forward -n kubeflow --address 10.10.10.111 svc/minio-service 9001:9000
