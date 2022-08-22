import os

from kubernetes import client, config
from kubernetes.client.rest import ApiException

DOMAIN = "autoscaling.k8s.io"
VPA_NAME = "verticalpodautoscaler"
VPA_PLURAL = "verticalpodautoscalers"
VPA_CHECKPOINT_NAME = "verticalpodautoscalercheckpoint"
VPA_CHECKPOINT_PLURAL = "verticalpodautoscalercheckpoints"


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
    # prom_client = PromCrawler(recommender_config.PROM_URL)

    # Get the VPA CRD
    current_crds = [x['spec']['names']['kind'].lower() for x in v1.list_custom_resource_definition().to_dict()['items']]
    if VPA_NAME not in current_crds:
        print("VerticalPodAutoscaler CRD is not created!")
        exit(-1)

    while True:
        print("Checking the frequency and the target IPS")