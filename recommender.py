
DEFAULT_NAMESPACE="default"
DELTA = 0.2

# Select the VPAs that choose the current clever recommender
def selects_recommender(vpas, recommender_name):
    selected_vpas = []
    for vpa in vpas["items"]:
        vpa_spec = vpa["spec"]
        if "recommenders" not in vpa_spec.keys():
            continue
        else:
            print("VPA {} has chosen {} recommenders".format(vpa["metadata"]["name"], len(vpa_spec["recommenders"])))
            print(vpa_spec)
            for recommender in vpa_spec["recommenders"]:
                if recommender["name"] == recommender_name:
                    selected_vpas.append(vpa)

    return selected_vpas

# Check if all container CPU requests are the same and get the consistent value.
# If some container requests are larger than others, is_consistent would be False.
def get_consistent_max_val(request_dict):
    max_val = -1
    consistent_cnt = 0
    for pod in request_dict.keys():
        for container in request_dict[pod].keys():
            if request_dict[pod][container] > max_val:
                max_val = request_dict[pod][container]
                consistent_cnt += 1

    is_consistent = True
    if consistent_cnt > 1:
        is_consistent = False

    return is_consistent, max_val


# Only check the default CPU request. If not existed, it will use 1 core by default.
def get_vpa_detailed_info(corev1, vpa):
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
    target_pods = corev1.list_namespaced_pod(namespace=target_namespace, label_selector="app=" + target_ref["name"])

    # Retrieve the target containers
    vpa_pod_nodes = {}
    all_container_cpu_requests = {}
    for pod in target_pods.items:
        all_container_cpu_requests[pod.metadata.name] = {}
        vpa_pod_nodes[pod.metadata.name] = pod.spec.node_name
        for container in pod.spec.containers:
            # print(container.name)
            # obtain the CPU request and convert it to int
            cur_request = str2resource("cpu", container.resources.requests["cpu"])
            all_container_cpu_requests[pod.metadata.name][container.name] = cur_request

    # Get the maximum default request if there are many containers.
    is_consistent, max_cpu_val = get_consistent_max_val(all_container_cpu_requests)
    vpa_container_cpu_request = max_cpu_val

    if not is_consistent:
        print("Warning: the containers managed by {} do not have consistent CPU requests!", vpa["metadata"]["name"])

    return vpa_container_cpu_request, vpa_pod_nodes

# resource2str converts a resource (CPU, Memory) value to a string
def resource2str(resource, value):
    if resource.lower() == "cpu":
        if value < 1:
            return str(int(value * 1000)) + "m"
        else:
            return str(value)
    # Memory is in bytes
    else:
        if value < 1024:
            return str(value) + "B"
        elif value < 1024 * 1024:
            return str(int(value / 1024)) + "k"
        elif value < 1024 * 1024 * 1024:
            return str(int(value / 1024 / 1024)) + "Mi"
        else:
            return str(int(value / 1024 / 1024 / 1024)) + "Gi"

# Convert a resource (CPU, Memory) string to a float value
def str2resource(resource, value):
    if type(value) is str:
        if resource.lower() == "cpu":
            if value[-1] == "m":
                return float(value[:-1]) / 1000
            else:
                return float(value)
        else:
            if value[-1].lower() == "b":
                return float(value[:-1])
            elif value[-1].lower() == "k":
                return float(value[:-1]) * 1024
            elif value[-2:].lower() == "mi":
                return float(value[:-2]) * 1024 * 1024
            elif value[-2:].lower() == "gi":
                return float(value[:-2]) * 1024 * 1024 * 1024
            else:
                return float(value)
    else:
        return value

def bound_var(var, min_value, max_value):
    if var < min_value:
        return min_value
    elif var > max_value:
        return max_value
    else:
        return var

# Find the nodes with frequency changes in the last iteration
def find_node_with_frequency_changes(cur_node_frequencies, prev_node_frequencies):
    node_with_frequency_changes = []
    for node in cur_node_frequencies.keys():
        # TODO: compare frequencies
        if node not in prev_node_frequencies.keys():
            node_with_frequency_changes.append(node)
        else:
            if cur_node_frequencies[node] == prev_node_frequencies[node]:
                continue
            else:
                node_with_frequency_changes.append(node)
    return node_with_frequency_changes

def  get_recommendation(vpa, corev1, node_frequencies, max_node_frequencies, vpa_default_request):
    """
    This function takes a VPA and returns a list of recommendations
    """
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

    # Get the target pods
    target_pods = corev1.list_namespaced_pod(namespace=target_namespace, label_selector="app=" + target_ref["name"])

    # Get the target container traces
    recommendations = []

    # Get uncapped target
    uncapped_targets = {}
    for pod in target_pods.items:
        pod_node = pod.spec.node_name
        node_frequency = node_frequencies[pod_node]
        max_node_frequency = max_node_frequencies[pod_node]
        for container in pod.spec.containers:
            container_name = container.name
            uncapped_target = vpa_default_request * float(max_node_frequency) / float(node_frequency)
            if container_name not in uncapped_targets.keys():
                uncapped_targets[container_name] = uncapped_target
            else:
                uncapped_targets[container_name] = max(uncapped_target, uncapped_targets[container_name])


    for containerPolicy in vpa_spec["resourcePolicy"]["containerPolicies"]:
        controlled_resources = containerPolicy["controlledResources"]
        max_allowed = containerPolicy["maxAllowed"]
        min_allowed = containerPolicy["minAllowed"]

        for resource in controlled_resources:
            if resource != "cpu":
                continue
            else:
                for container_name in uncapped_targets.keys():
                    container_recommendation = {"containerName": container_name, "lowerBound": {}, "target": {},
                                                "uncappedTarget": {}, "upperBound": {}}
                    uncapped_target = uncapped_targets[container_name]
                    lower_bound = uncapped_target * (1 - DELTA)
                    upper_bound = uncapped_target * (1 + DELTA)

                    # If the target is below the lowerbound, set it to the lowerbound
                    min_allowed_value = str2resource(resource, min_allowed[resource])
                    max_allowed_value = str2resource(resource, max_allowed[resource])
                    target = bound_var(uncapped_target, min_allowed_value, max_allowed_value)
                    lower_bound = bound_var(lower_bound, min_allowed_value, max_allowed_value)
                    upper_bound = bound_var(upper_bound, min_allowed_value, max_allowed_value)

                    # Convert CPU/Memory values to millicores/bytes
                    container_recommendation["lowerBound"][resource] = resource2str(resource, lower_bound)
                    container_recommendation["target"][resource] = resource2str(resource, target)
                    container_recommendation["uncappedTarget"][resource] = resource2str(resource, uncapped_target)
                    container_recommendation["upperBound"][resource] = resource2str(resource, upper_bound)

                    recommendations.append(container_recommendation)
    return recommendations
