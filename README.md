# CLEVER
Container Level Energy-efficient VPA Recommender for Kubernetes

## Pre-requisites
- Baremetal Node OS - RedHat 8
- Kubernetes 1.22+
- Kepler v0.2
- Prometheus release-0.11
- Kubernetes Vertical Pod Autoscaler (VPA) 0.11

## Installation
### Install Kepler
- Follow the instructions in the [Kepler](https://github.com/sustainable-computing-io/kepler) to install Kepler as DaemonSets on nodes of the Kubernetes Cluster.

### Install Prometheus & Grafana Dashboard
- Follow the instructions in the [kube-prometheus](https://github.com/prometheus-operator/kube-prometheus) to install both Prometheus and Grafana on the Kubernetes Cluster.
- Import the [Grafana Dashboard](https://grafana.com/docs/grafana/v9.0/dashboards/export-import/). The dashboard is available in the `dashboards/clever-dashboard.json` folder.
- Access Prometheus UI and Grafana Dashboard via `kubectl port-forward` command following the [Access UIs tutorial](https://github.com/prometheus-operator/kube-prometheus/blob/main/docs/access-ui.md).

### Install VPA
- Follow the instructions [here](https://github.com/kubernetes/autoscaler/blob/master/vertical-pod-autoscaler/README.md) to install the VPA on the Kubernetes Cluster.

### Install CLEVER
- Clone the CLEVER repository
```bash
git clone https://github.com/sustainable-computing-io/clever.git
```

- Deploy CLEVER Recommender to run as an alternative recommender for VPA.
```bash
kubectl apply -f manifests/clever.yaml
```

## Tutorial
- Deploy the example application that selects the CLEVER recommender for VPA.
```bash
kubectl apply -f manifests/random.yaml
```

- The example application defines a VPA Custom Resource with the following configuration:
```yaml
apiVersion: "autoscaling.k8s.io/v1"
kind: VerticalPodAutoscaler
metadata:
  name: random-vpa
spec:
  recommenders:
    - name: clever
  targetRef:
    apiVersion: "apps/v1"
    kind: Deployment
    name: random
  resourcePolicy:
    containerPolicies:
      - containerName: '*'
        minAllowed:
          cpu: 100m
        maxAllowed:
          cpu: 16
        controlledResources: ["cpu"]
```

- Monitor the recommended CPU requests for the example application by watching the VPA object.
```bash
watch -n 0.1 ./scripts/vpa.sh random-vpa
```

- Change the node CPU frequencies to observe the effect on the recommended CPU requests.
```bash
./scripts/set_cpu_freq.sh 1GHz
```
