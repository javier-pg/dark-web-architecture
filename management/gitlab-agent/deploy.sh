source ../local.env
sudo helm upgrade --install kubernetes gitlab/gitlab-agent \
    --namespace gitlab-agent \
    --set image.tag=v15.2.0 \
    --set config.token=$GITLAB_AGENT_TOKEN \
    --set config.kasAddress=wss://$GITLAB_KAS_IPADDRESS/-/kubernetes-agent/ \
    --set config.caCert="$(sudo cat $GITLAB_CACERT_PATH)"
