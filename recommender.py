
DEFAULT_NAMESPACE="default"

def selects_recommender(vpas, recommender_name):
    selected_vpas = []
    for vpa in vpas["items"]:
        vpa_spec = vpa["spec"]
        if "recommenders" not in vpa_spec.keys():
            continue
        else:
            print(vpa_spec)
            for recommender in vpa_spec["recommenders"]:
                if recommender["name"] == recommender_name:
                    selected_vpas.append(vpa)

    return selected_vpas

def get_target_container_default_cpu_request(corev1_client, target_namespace, target_ref):
    default_request = 1

    target_pods = corev1_client.list_namespaced_pod(namespace=target_namespace, label_selector="app=" + target_ref["name"])

    # Retrieve the target containers
    for pod in target_pods.items:
        for container in pod.spec.containers:
            print(container.name)
            # TODO: obtain the CPU request and convert it to int
            # Get the maximum default request if there are many containers.

    return default_request

# Only check the default CPU request. If not existed, it will use 1 core by default.
def get_vpa_default_cpu_request(corev1, vpa):
    # Get the VPA spec
    vpa_spec = vpa["spec"]

    # example target_ref {'apiVersion': 'apps/v1', 'kind': 'Deployment', 'name': 'hamster'}
    target_ref = vpa_spec["targetRef"]
    print(target_ref)

    # Retrieve the target pods
    if "namespace" in target_ref.keys():
        target_namespace = target_ref["namespace"]
    else:
        target_namespace = DEFAULT_NAMESPACE

    # Get the target containers
    target_container_cpu_request = get_target_container_default_cpu_request(corev1, target_namespace, target_ref)
    return target_container_cpu_request
