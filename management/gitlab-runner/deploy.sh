source ../local.env
kubectl create namespace gitlab-runner
kubectl create secret generic gitlab-runner-secret --namespace gitlab-runner --from-file=/etc/gitlab/ssl/10.10.10.111.crt
#sudo helm repo add gitlab https://charts.gitlab.io
sudo helm install --namespace gitlab-runner gitlab-runner --set certsSecretName=gitlab-runner-secret --set gitlabUrl=$GITLAB_URL --set runnerRegistrationToken=$GITLAB_RUNNER_TOKEN --set rbac.create="true" --values values.yaml gitlab/gitlab-runner
kubectl create clusterrolebinding gitlab-runner-binding --clusterrole=cluster-admin --serviceaccount=gitlab-runner:default