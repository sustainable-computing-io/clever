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
        vpas = crds.list_cluster_custom_object(group=DOMAIN, version="v1", plural=VPA_PLURAL)
        selectedVpas = selects_recommender(vpas, RECOMMENDER_NAME)

        # Update the container default requests for selectedVpas
        # Keep the mapping between nodes and vpas, which manage pods on those nodes.
        node_vpas = {}
        for vpa in selectedVpas:
            vpa_name = vpa["metadata"]["name"]
            vpa_namespace = vpa["metadata"]["namespace"]

            # Get initial container request.
            if vpa_name not in ACTIVE_VPA_DEFAULT_CPU_REQUESTS.keys():
                ACTIVE_VPA_DEFAULT_CPU_REQUESTS[vpa_name], vpa_nodes = get_vpa_detailed_info(corev1, vpa)
            else:
                _, vpa_nodes = get_vpa_detailed_info(corev1, vpa)

            # Select VPAs per node.
            for node in list(set(vpa_nodes.values())):
                if node not in node_vpas.keys():
                    node_vpas[node] = [vpa]
                else:
                    node_vpas[node].append(vpa)

        # Obtain the latest node cpu frequencies
        CUR_NODE_CPU_FREQUENCY = get_all_node_homogeneous_frequencies(prom_client, LATEST_CPU_FREQUENCY_QUERY)

        # Check difference between LATEST_NODE_CPU_FREQUENCY and CUR_NODE_CPU_FREQUENCY
        if CUR_NODE_CPU_FREQUENCY != LATEST_NODE_CPU_FREQUENCY:
            # Select nodes with frequency changes.
            nodes_with_frequency_changes = find_node_with_frequency_changes(CUR_NODE_CPU_FREQUENCY, LATEST_NODE_CPU_FREQUENCY)

            vpas_to_update = {}
            for node in nodes_with_frequency_changes:
                if node not in node_vpas.keys():
                    print("Frequency changes on node {} does not impact any vpa managed pods!")
                    continue

                cur_node_vpas = node_vpas[node]
                for vpa in cur_node_vpas:
                    vpa_name = vpa["metadata"]["name"]
                    vpas_to_update[vpa_name] = vpa

            for vpa in vpas_to_update.values():
                vpa_name = vpa["metadata"]["name"]
                vpa_namespace = vpa["metadata"]["namespace"]

                print("Recommend sizes according to current frequency for vpas on nodes with frequency changes!")

                recommendations = get_recommendation(vpa, corev1, CUR_NODE_CPU_FREQUENCY, MAX_NODE_CPU_FREQUENCY, ACTIVE_VPA_DEFAULT_CPU_REQUESTS[vpa_name])

                if not recommendations:
                    print("No new recommendations obtained, so skip updating the vpa object {}".format(vpa_name))
                    continue

                # Update the recommendations.
                patched_vpa = {"recommendation": {"containerRecommendations": recommendations}}
                body = {"status": patched_vpa}
                vpa_api = client.CustomObjectsApi()

                # Update the VPA object
                # API call doc: https://github.com/kubernetes-client/python/blob/master/kubernetes/docs/CustomObjectsApi.md#patch_namespaced_custom_object
                try:
                    vpa_updated = vpa_api.patch_namespaced_custom_object(group=DOMAIN, version="v1", plural=VPA_PLURAL,
                                                                         namespace=vpa_namespace, name=vpa_name,
                                                                         body=body)
                    print("Successfully patched VPA object with the recommendation: %s" %
                          vpa_updated['status']['recommendation']['containerRecommendations'])
                except ApiException as e:
                    print("Exception when calling CustomObjectsApi->patch_namespaced_custom_object: %s\n" % e)

        time.sleep(SLEEP_WINDOW)

