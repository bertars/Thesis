import argparse

import requests
import pandas as pd
import numpy as np


METRIC_STEP = 5  # In seconds
MAX_RESOLUTION = 11_000  # Maximum resolution of Prometheus
DURATION = "1m"

QUERIES = {
    "cpu": f"sum(rate(container_cpu_usage_seconds_total[{DURATION}])) by (container_label_com_docker_compose_service)",
    "memory": f"sum(rate(container_memory_usage_bytes[{DURATION}])) by (container_label_com_docker_compose_service)",
    "memory_rss": f"sum(rate(container_memory_rss[{DURATION}])) by (container_label_com_docker_compose_service)",
    "memory_cache": f"sum(rate(container_memory_cache[{DURATION}])) by (container_label_com_docker_compose_service)",
    "disk": f"sum(rate(container_fs_reads_bytes_total[{DURATION}])) by (container_label_com_docker_compose_service)", # Total bytes read by the container
    "power": f"sum(rate(scaph_process_power_consumption_microwatts[{DURATION}])) by (container_label_com_docker_compose_service) / 1000000",
    
}

CONTAINERS = {
    'rabbitmq', 'redis', 'ts-ui-dashboard', 'ts-auth-service', 'ts-auth-mongo',
    'ts-user-service', 'ts-user-mongo', 'ts-verification-code-service', 'ts-account-mongo',
    'ts-route-service', 'ts-route-mongo', 'ts-contacts-service', 'ts-contacts-mongo',
    'ts-order-service', 'ts-order-mongo', 'ts-order-other-service', 'ts-order-other-mongo',
    'ts-config-service', 'ts-config-mongo', 'ts-station-service', 'ts-station-mongo',
    'ts-train-service', 'ts-train-mongo', 'ts-travel-service', 'ts-travel-mongo',
    'ts-travel2-service', 'ts-travel2-mongo', 'ts-preserve-service', 'ts-preserve-other-service',
    'ts-basic-service', 'ts-ticketinfo-service', 'ts-price-service', 'ts-price-mongo',
    'ts-notification-service', 'ts-security-service', 'ts-security-mongo',
    'ts-inside-payment-service', 'ts-inside-payment-mongo', 'ts-execute-service',
    'ts-payment-service', 'ts-payment-mongo', 'ts-rebook-service', 'ts-rebook-mongo',
    'ts-cancel-service', 'ts-assurance-service', 'ts-assurance-mongo', 'ts-seat-service',
    'ts-travel-plan-service', 'ts-ticket-office-service', 'ts-ticket-office-mongo',
    'ts-news-service', 'ts-news-mongo', 'ts-voucher-mysql', 'ts-voucher-service',
    'ts-food-map-service', 'ts-food-map-mongo', 'ts-route-plan-service', 'ts-food-service',
    'ts-consign-service', 'ts-consign-mongo', 'ts-consign-price-service', 'ts-consign-price-mongo',
    'ts-food-mongo', 'ts-admin-basic-info-service', 'ts-admin-order-service',
    'ts-admin-route-service', 'ts-admin-travel-service', 'ts-admin-user-service', 'ts-avatar-service'
}



# Merge two dictionaries of lists by appending the entries to the list.
# y will be append at the end of x
def _merge(x, y):
    data = x
    for key in y:
        data[key] = x.get(key, []) + y[key]
    return data

#You'll receive data from Prometheus at 5-second intervals,
#and your query will aggregate that data over the last 1 minute
#to provide you with the rate of change in CPU usage by container names.
def _exec_query(query, start_time, end_time, prom_url):
    response = requests.get(
        f"http://{prom_url}/api/v1/query_range",
        params={
            "query": query,
            "start": start_time,
            "end": end_time,
            "step": f"{METRIC_STEP}s",
        },
    )
    data = {}
    results = response.json()["data"]["result"]

    for result in results:
        if all(
            k not in result["metric"].keys() for k in ["container", "name", "target", "container_label_com_docker_compose_service"]
        ):
            continue
        if "container" in result["metric"]:
            service_name = result["metric"]["container"]
        elif "name" in result["metric"]:
            service_name = result["metric"]["name"]
        elif "container_label_com_docker_compose_service" in result["metric"]:
            service_name = result["metric"]["container_label_com_docker_compose_service"]
        else:
            service_name = result["metric"]["target"]
        if service_name not in CONTAINERS:
            continue
        data[service_name] = result["values"]
    return data


# Given a valid query, extracts the relevant data
def exec_query(query, start, end, prom_url):
    # If all the data can be collected in only one request
    if not (end - start) / METRIC_STEP > MAX_RESOLUTION:
        return _exec_query(query, start, end, prom_url)

    data = {}
    start_time = start
    end_time = start
    while end_time < end:
        end_time = min(end_time + MAX_RESOLUTION, end)
        print(f"Querying data from {start_time} to {end_time}")
        d = _exec_query(query, start_time, end_time, prom_url)
        data = _merge(data, d)
        start_time = end_time + 1
    return data


def get_data(queries, start, end, prom_url):
    data = {}
    for name, query in queries.items():
        print(f"Working on query for {name}...")
        data[name] = exec_query(query, start, end, prom_url)

    columns = {}
    for m, containers in data.items():
        for c, info in containers.items():
            i = np.array(info)
            time = i[0:, 0]
            values = i[0:, 1]
            if len(columns) == 0:
                columns["time"] = time
            if len(columns["time"]) < len(time):
                columns["time"] = time
            columns[f"{c}_{m}"] = values
    return columns


def make_dict_list_equal(dict_list):
    l_min = float("inf")
    for key in dict_list:
        l_min = min(l_min, len(dict_list[key]))

    new_dict = {}
    for key, old_list in dict_list.items():
        new_list = old_list
        if len(old_list) > l_min:
            print(
                f"Discarding {len(old_list) - l_min} entries from the end of the column name {key}"
            )
            new_list = old_list[:l_min]
        new_dict[key] = new_list
    return new_dict


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Collect data from Prometheus for trainticket')

    parser.add_argument('--ip', type=str, required=True, help='The ip of vm/container running Prometheus')
    parser.add_argument('--start', type=float, required=True, help='The start time')
    parser.add_argument('--end', type=float, required=True, help='The end time')
    parser.add_argument('--output', type=str, required=True, help='The name/path of the file')

    args = parser.parse_args()
    
    df = pd.DataFrame(
        make_dict_list_equal(get_data(QUERIES, args.start, args.end, args.ip))
    )

    df.to_csv(args.output, index=False)
