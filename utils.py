from PromClient import *

def parse_frequency_dict(cpu_frequency_data):
    all_node_frequencies = {}
    for cur_element in cpu_frequency_data:
        node_name = cur_element["metric"]["instance"]
        cpu_idx = cur_element["metric"]["cpu"]
        all_node_frequencies[node_name] = {}
        cur_val = cur_element["value"][1]
        all_node_frequencies[node_name][cpu_idx] = cur_val

    return all_node_frequencies

def get_homogeneous_value(node_frequencies):
    cpu_count = 0
    homogeneous_frequency = -1
    for cpu in node_frequencies.keys():
        if cpu_count == 0:
            homogeneous_frequency = node_frequencies[cpu]
        else:
            if node_frequencies[cpu] != homogeneous_frequency:
                return -1

        cpu_count +=1
    return homogeneous_frequency

def get_all_node_homogeneous_frequencies(prom_cient, prometheus_query):
    frequency_data = prom_cient.get_query(prometheus_query)
    if frequency_data is None:
        return None
    all_node_frequencies = parse_frequency_dict(frequency_data)
    all_node_homogeneous_frequencies = {}
    for node in all_node_frequencies.keys():
        cur_node_homogeneous_frequency = get_homogeneous_value(all_node_frequencies[node])
        if cur_node_homogeneous_frequency == -1:
            return None
        all_node_homogeneous_frequencies[node] = cur_node_homogeneous_frequency
    return all_node_homogeneous_frequencies