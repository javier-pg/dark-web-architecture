# A Big Data Architecture for Early Identification and Categorization of Dark Web Sites

## Description
A new scalable architecture for the early identification of new Tor sites and the daily analysis of their content. The solution is built using Big Data technologies (Kubernetes, Kafka, Kubeflow, and MinIO), continuously discovering onion services in different sources (threat intelligence, code repositories web-Tor gateways and Tor repositories), deduplicating them using MinHash LSH, and categorizing with the BERTopic topic modeling.

<p align="center">
<kbd>
<img src=imgs/arch.PNG width="500">
</kbd>
</p>

## Organization
The repository is organized as follows:

- `management/`: contains the management services for the architecture
    - `local.env.example`: environment variables for the management services
    - `dashboard/`: kubernetes dashboard service
    - `gitlab-agent/`: gitlab-agent for integration of Kubernetes and GitLab CI/CD
    - `gitlab-runner/`: gitlab-runner for CI/CD pipelines
    - `grafana/`: grafana service for monitoring  
    - `promehteus/`: prometheus service for monitoring
    - `nfs-provisioner/`: NFS provider service for persistent volumes
- `applications`: contains the application-level services for the dark web monitoring
    - `local.env.example`: environment variables for the application-level services
    - `data_sources/`: data sources (threat intelligence, code repositories web-Tor gateways and Tor repositories) configured in Crawlab
    - `crawlab/`: crawlab service for the data ingestion and crawler database
    - `downloaders/`: service for downloading Tor HTML pages and downloader database
    - `torproxy/`: tor proxy for downloading Tor HTML pages
    - `kafka/`: kafka service for streaming
    - `mlops/`: kubeflow service for the daily batch processing
    - `minio/`: minio service for the object data storage
    - `jobs/`: kubernetes jobs for architecture configuration

## Requirements
The project requires the following dependencies:

- `Python 3`
- `Docker 20.10.21`
- `Kubernetes 1.22.12` (_Kubernetes cluster already working_)

## Installation
By executing the CI/CD pipeline (`.gitlab-ci.yml`), the architecture will be deployed automatically on your Kubernetes cluster. Beforehand, the gitlab-agent (`management/gitlab-agent`) and runners (`management/gitlab-runner`) should be configured. Read the official documentation of [GitLab Agent](https://docs.gitlab.com/ee/user/clusters/agent/ci_cd_workflow.html) and [GitLab Runners](https://docs.gitlab.com/runner/install/kubernetes.html).

## Usage

The architecture is used through:
- Crawlab interface for the data ingestion
- Kubernetes client and dashboard for data engineering instructions and monitoring
- Kubeflow interface for configuring the daily batch data processing 


## Images

<p align="center">
<kbd>
<img src=imgs/crawlab.PNG width="500">
</kbd>
</p>

<p align="center">
<kbd>
<img src=imgs/data_sources.png width="500">
</kbd>
</p>

<p align="center">
<kbd>
<img src=imgs/kubernetes_pods_worker01.PNG width="500">
</kbd>
</p>

<p align="center">
<kbd>
<img src=imgs/kubernetes_scaled_pods.PNG width="500">
</kbd>
</p>

<p align="center">
<kbd>
<img src=imgs/mlops.jpg width="500">
</kbd>
</p>



## License
[MIT](https://choosealicense.com/licenses/mit/)
