from utils import *

if __name__ == '__main__':
    prom_address = "http://127.0.0.1:39090"
    prom_client = PromClient(prom_address)

    max_cpu_frequency_query = "node_cpu_frequency_max_hertz"
    min_cpu_frequency_query = "node_cpu_frequency_min_hertz"
    latest_cpu_frequency_query = "node_cpu_scaling_frequency_hertz"

    pod_ips_query = "pod_energy_stat"

    all_node_homogeneous_max_frequencies = get_all_node_homogeneous_frequencies(prom_client, max_cpu_frequency_query)
    print(all_node_homogeneous_max_frequencies)





