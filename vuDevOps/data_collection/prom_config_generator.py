import yaml

# List of available scrape intervals
scrape_intervals = ["1s", "5s", "10s", "30s", "1m", "2m", "3m"]
timeout_interval = "10s"
# Ask the user to select a scrape interval
while True:
    print("Select a scrape interval:")
    for i, interval in enumerate(scrape_intervals, 1):
        print(f"{i}. {interval}")

    choice = input("Enter the number corresponding to your choice: ")
    
    try:
        choice = int(choice)
        if 1 <= choice <= len(scrape_intervals):
            scrape_interval = scrape_intervals[choice - 1]
            if(scrape_interval == "1s" | scrape_interval == "5s"):
                timeout_interval = scrape_interval
            break
        else:
            print("Invalid choice. Please select a valid option.")
    except ValueError:
        print("Invalid input. Please enter a number.")


# Define the Prometheus JSON configuration
config = {
    "global": {
        "scrape_interval": scrape_interval,
        "scrape_timeout": timeout_interval,
        "evaluation_interval": "1m"
    },
    "rule_files": ["/etc/prometheus/alert.rules"],
    "alerting": {
        "alertmanagers": [
            {
                "static_configs": [
                    {
                        "targets": ["alertmanager:9093"]
                    }
                ]
            }
        ]
    },
    "scrape_configs": [
        {
            "job_name": "frontend",
            "metrics_path": "metrics",
            "static_configs": [
                {
                    "targets": ["145.108.225.16:9099"]
                }
            ]
        },
        {
            "job_name": "catalogue",
            "static_configs": [
                {
                    "targets": ["145.108.225.16:9091"]
                }
            ]
        },
        {
            "job_name": "payment",
            "static_configs": [
                {
                    "targets": ["145.108.225.16:9097"]
                }
            ]
        },
        {
            "job_name": "user",
            "static_configs": [
                {
                    "targets": ["145.108.225.16:9098"]
                }
            ]
        },
        {
            "job_name": "orders",
            "metrics_path": "metrics",
            "static_configs": [
                {
                    "targets": ["145.108.225.16:9096"]
                }
            ]
        },
        {
            "job_name": "cart",
            "metrics_path": "metrics",
            "static_configs": [
                {
                    "targets": ["145.108.225.16:9092"]
                }
            ]
        },
        {
            "job_name": "shipping",
            "metrics_path": "metrics",
            "static_configs": [
                {
                    "targets": ["145.108.225.16:9094"]
                }
            ]
        },
        {
            "job_name": "queue-master",
            "metrics_path": "prometheus",
            "static_configs": [
                {
                    "targets": ["145.108.225.16:9095"]
                }
            ]
        },
        {
            "job_name": "node-exporter",
            "metrics_path": "metrics",
            "static_configs": [
                {
                    "targets": ["nodeexporter:9100"]
                }
            ]
        },
        {
            "job_name": "scaphandre",
            "metrics_path": "metrics",
            "static_configs": [
                {
                    "targets": ["145.108.225.16:8081"]
                }
            ]
        },
        {
            "job_name": "cadvisor",
            "metrics_path": "metrics",
            "static_configs": [
                {
                    "targets": ["145.108.225.16:8082"]
                }
            ]
        },
    ]
}

# Save the configuration to a YAML file
with open("prometheus.yml", "w") as file:
    yaml.dump(config, file, default_flow_style=False, indent=4)

print(f"Configuration file 'prometheus_config.yml' has been created with scrape_interval set to {scrape_interval}.")
