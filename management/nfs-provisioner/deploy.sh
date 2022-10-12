# important for nodes to have nfs-common installed (apt-get install -y nfs-common)
sudo helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/
sudo helm install nfs-subdir-external-provisioner nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
    --set nfs.server=10.10.10.106 \
    --set nfs.path=/ \
    --set storageClass.defaultClass=true \
    --set storageClass.reclaimPolicy=Retain