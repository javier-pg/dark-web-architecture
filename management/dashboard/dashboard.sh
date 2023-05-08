helm repo add kubernetes-dashboard kubernetes.github.io/dashboard
helm install my-release kubernetes-dashboard/kubernetes-dashboard --set=service.externalPort=8080,resources.limits.cpu=200m,metricsScraper.enabled=true
kubectl proxy
