import os
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from utils import *
from recommender import *

# Current Recommender Name
RECOMMENDER_NAME = "clever"
SLEEP_WINDOW = 60

# VPA resources
DOMAIN = "autoscaling.k8s.io"
VPA_NAME = "verticalpodautoscaler"
VPA_PLURAL = "verticalpodautoscalers"
VPA_CHECKPOINT_NAME = "verticalpodautoscalercheckpoint"
VPA_CHECKPOINT_PLURAL = "verticalpodautoscalercheckpoints"

# PROMETHEUS Queries
MAX_CPU_FREQUENCY_QUERY = "node_cpu_frequency_max_hertz"
MIN_CPU_FREQUENCY_QUERY = "node_cpu_frequency_min_hertz"
LATEST_CPU_FREQUENCY_QUERY = "node_cpu_scaling_frequency_hertz"

# Keep the latest node frequencies and the VPA default requests in cache
MAX_NODE_CPU_FREQUENCY = {}
LATEST_NODE_CPU_FREQUENCY = {}
ACTIVE_VPA_DEFAULT_CPU_REQUESTS = {}


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    if 'KUBERNETES_PORT' in os.environ:
        config.load_incluster_config()
    else:
        config.load_kube_config()

    # Get the api instance to interact with the cluster
    api_client = client.api_client.ApiClient()
    v1 = client.ApiextensionsV1Api(api_client)
    corev1 = client.CoreV1Api(api_client)
    crds = client.CustomObjectsApi(api_client)
    resource_version = ''

    # Initialize the prometheus client
    prom_client = PromClient()

    # Initialize the node CPU frequency cache.
    MAX_NODE_CPU_FREQUENCY = get_all_node_homogeneous_frequencies(prom_client, MAX_CPU_FREQUENCY_QUERY)
    if MAX_NODE_CPU_FREQUENCY is None:
        print("Prometheus Query {} at Endpoint {} failed.".format(MAX_CPU_FREQUENCY_QUERY, prom_client.prom_address))
        exit(-1)

    LATEST_NODE_CPU_FREQUENCY = get_all_node_homogeneous_frequencies(prom_client, LATEST_CPU_FREQUENCY_QUERY)
    if LATEST_NODE_CPU_FREQUENCY is None:
        print("Prometheus Query {} at Endpoint {} failed.".format(LATEST_CPU_FREQUENCY_QUERY, prom_client.prom_address))
        exit(-1)

    # Get the VPA CRD
    current_crds = [x['spec']['names']['kind'].lower() for x in v1.list_custom_resource_definition().to_dict()['items']]
    if VPA_NAME not in current_crds:
        print("VerticalPodAutoscaler CRD is not created!")
        exit(-1)

    while True:
        print("Checking the frequency and the target IPS")
        # Updating the default VPA CPU cache.
        # TODO: iterate through all VPAs and get their workload default CPU requests.
        vpas = crds.list_cluster_custom_object(group=DOMAIN, version="v1", plural=VPA_PLURAL)
        selectedVpas = selects_recommender(vpas, RECOMMENDER_NAME)

        # Update the container default requests for selectedVpas
        for vpa in selectedVpas:
            vpa_name = vpa["metadata"]["name"]
            vpa_namespace = vpa["metadata"]["namespace"]

            # Get initial container request.
            if vpa_name not in ACTIVE_VPA_DEFAULT_CPU_REQUESTS.keys():
                ACTIVE_VPA_DEFAULT_CPU_REQUESTS[vpa_name] = get_vpa_default_cpu_request(corev1, vpa)
            else:
                continue

            # Select VPAs per node.
            # TODO: get the mapping between node and vpas for resize later.

        # Obtain the latest node cpu frequencies
        CUR_NODE_CPU_FREQUENCY = get_all_node_homogeneous_frequencies(prom_client, LATEST_CPU_FREQUENCY_QUERY)

        # Check difference between LATEST_NODE_CPU_FREQUENCY and CUR_NODE_CPU_FREQUENCY
        if CUR_NODE_CPU_FREQUENCY == LATEST_CPU_FREQUENCY_QUERY:
            continue
        else:
            # TODO: add logic of resizing the containers
            print("TODO: recommend sizes according to current frequency for vpas on nodes with frequency changes!")

        time.sleep(SLEEP_WINDOW)

