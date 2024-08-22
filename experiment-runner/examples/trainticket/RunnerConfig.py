from EventManager.Models.RunnerEvents import RunnerEvents
from EventManager.EventSubscriptionController import EventSubscriptionController
from ConfigValidator.Config.Models.RunTableModel import RunTableModel
from ConfigValidator.Config.Models.FactorModel import FactorModel
from ConfigValidator.Config.Models.RunnerContext import RunnerContext
from ConfigValidator.Config.Models.OperationType import OperationType
from ProgressManager.Output.OutputProcedure import OutputProcedure as output

from typing import Dict, List, Any, Optional
from pathlib import Path
from os.path import dirname, realpath

from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import time
import subprocess
import shlex
import random
import datetime
import json
import os 
import signal

WARMUP = 3

class RunnerConfig:
    ROOT_DIR = Path(dirname(realpath(__file__)))

    # ================================ USER SPECIFIC CONFIG ================================
    """The name of the experiment."""
    name:                       str             = "new_runner_experiment"

    """The path in which Experiment Runner will create a folder with the name `self.name`, in order to store the
    results from this experiment. (Path does not need to exist - it will be created if necessary.)
    Output path defaults to the config file's path, inside the folder 'experiments'"""
    results_output_path:        Path             = ROOT_DIR / 'experiments'

    """Experiment operation type. Unless you manually want to initiate each run, use `OperationType.AUTO`."""
    operation_type:             OperationType   = OperationType.AUTO

    """The time Experiment Runner will wait after a run completes.
    This can be essential to accommodate for cooldown periods on some systems."""
    time_between_runs_in_ms:    int             = 1000

    app_config_path:            str             = "../vuDevOps/data_collection/trainticket_config.json"
    stressor_config_path:       str             = "../vuDevOps/data_collection/stressor_config.json"

    # Dynamic configurations can be one-time satisfied here before the program takes the config as-is
    # e.g. Setting some variable based on some criteria
    def __init__(self):
        """Executes immediately after program start, on config load"""

        EventSubscriptionController.subscribe_to_multiple_events([
            (RunnerEvents.BEFORE_EXPERIMENT, self.before_experiment),
            (RunnerEvents.BEFORE_RUN       , self.before_run       ),
            (RunnerEvents.START_RUN        , self.start_run        ),
            (RunnerEvents.START_MEASUREMENT, self.start_measurement),
            (RunnerEvents.INTERACT         , self.interact         ),
            (RunnerEvents.STOP_MEASUREMENT , self.stop_measurement ),
            (RunnerEvents.STOP_RUN         , self.stop_run         ),
            (RunnerEvents.POPULATE_RUN_DATA, self.populate_run_data),
            (RunnerEvents.AFTER_EXPERIMENT , self.after_experiment )
        ])
        self.run_table_model = None  # Initialized later
        self.load_configs()
        self.traffic_process = None

        output.console_log("Custom config loaded")

    def load_configs(self):
        with open(self.app_config_path, 'r') as f:
            self.app_data = json.load(f)
        with open(self.stressor_config_path, 'r') as f:
            self.stressor_data = json.load(f)

    def create_run_table_model(self) -> RunTableModel:
        """Create and return the run_table model here. A run_table is a List (rows) of tuples (columns),
        representing each run performed"""
        factor1 = FactorModel("scenario", ['scenario_A', 'scenario_B'])
        # factor2 = FactorModel("anomaly_type", ['resource', 'time'])
        factor2 = FactorModel("service_stressed", ['ts-travel-service', 'ts-order-service'])
        factor3 = FactorModel("user_load", [100, 1000])
        # repetitions = FactorModel("repetition_id", [1])
        repetitions = FactorModel("repetition_id", list(range(1, 31)))

        services = [
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
        ]
        metrics = ['avg_cpu', 'avg_mem', 'avg_mem_rss', 'avg_mem_cache', 'avg_disk', 'avg_power']
        data_columns = [f"{service}_{metric}" for metric in metrics for service in services]
        
        self.run_table_model = RunTableModel(
        factors=[factor1, factor2, factor3, repetitions],
        exclude_variations=[
            # {factor1: ['example_treatment1']},                   # all runs having treatment "example_treatment1" will be excluded
            # {factor1: ['example_treatment2'], factor2: [True]},  # all runs having the combination ("example_treatment2", True) will be excluded
        ],
        data_columns=data_columns,
        shuffle=True
        )
        return self.run_table_model


    def before_experiment(self) -> None:
        """Perform any activity required before starting the experiment here
        Invoked only once during the lifetime of the program."""

        output.console_log("Config.before_experiment() called!")

    def before_run(self) -> None:
        """Perform any activity required before starting a run.
        No context is available here as the run is not yet active (BEFORE RUN)"""

        output.console_log("Config.before_run() called!")

    def install_stress_ng(self, service_name):
        output.console_log(f"Installing stress-ng in {service_name}...")
        update_commands = "echo 'deb http://archive.debian.org/debian/ jessie main' > /etc/apt/sources.list && echo 'deb http://archive.debian.org/debian-security/ jessie/updates main' >> /etc/apt/sources.list && echo 'Acquire::Check-Valid-Until \"false\";' > /etc/apt/apt.conf.d/99no-check-valid-until && apt-get update" 
        apt_get_update_command = f'docker exec -u root -it docker-compose-{service_name}-1 /bin/sh -c "{update_commands}"'
        subprocess.run(apt_get_update_command, shell=True, check=False)
        stress_ng_command = "apt-get install -y apt-utils iproute2 stress-ng musl --force-yes"
        install_stress_command = f'docker exec -u root -it docker-compose-{service_name}-1 /bin/sh -c "{stress_ng_command}"'
        subprocess.run(install_stress_command, shell=True, check=True)

    def generate_load(self, app_data,scenario,user_count, log_file):
        if app_data['load_script_type'] == "locust":
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print('\033[92m'+ timestamp + f' Sending traffic to the target system at {app_data["host_url"]}' + '\033[0m')
            
            process = None
                
            user_spawn_rate = 5
            script_path = f"../vuDevOps/data_collection{app_data['load_script']}"
            subprocess.run(["chmod", "+x", script_path], check=True)
            process =  subprocess.Popen(f"{script_path} -h {app_data['host_url']} -r {int(100)}s -l {log_file} -u {user_count} -s {user_spawn_rate} -n {scenario}", shell=True, preexec_fn=os.setsid)
            # Locust needs a few seconds to deploy all traffic
            time.sleep(10)
            return process    


    def start_run(self, context: RunnerContext) -> None:
        """Perform any activity required for starting the run here.
        For example, starting the target system to measure. 
        Activities after starting the run should also be performed here."""

        output.console_log("Config.start_run() called!")

        output.console_log("Bringing system up...")

        p = subprocess.Popen('docker compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.cadvisor.yml up -d', shell=True)
        p.wait()
        p = subprocess.Popen('docker compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.trainticket.yml --env-file ../vuDevOps/microservices-demo/.env up -d', shell=True)
        p.wait()
        p = subprocess.Popen('docker compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.scaphandre.yml up -d', shell=True)
        p.wait()

        print('Warm-up time')
        time.sleep(WARMUP * 60)
        service_stressed = context.run_variation['service_stressed']
        self.install_stress_ng(service_stressed)

        scenario = context.run_variation['scenario']
        user_load = context.run_variation['user_load']
        repetition = context.run_variation['repetition_id']

        print(f'Current treatment {scenario} - anomalous - {service_stressed} - {user_load} - {repetition}')

        base_dir = Path('../vuDevOps/data_collection/trainticket-data')

        # Ensure the base directory exists
        os.makedirs(base_dir, exist_ok=True)

        # Create the directory path
        dir_path = base_dir / scenario / 'anomalous' / service_stressed / str(user_load) / f'repetition_{repetition}'
    
        # Create the directories
        os.makedirs(dir_path, exist_ok=True)

        time.sleep(2)
        
        print(f'Created directory: {dir_path}')

        traffic_process = self.generate_load(self.app_data, scenario, user_load, f'{dir_path}/Locust_log')
        self.traffic_process = traffic_process


    def run_command_command(self, command):
        start_time = time.time()
        process = subprocess.Popen(command, shell=True)
        process.wait()
        end_time = time.time()
        return start_time, end_time 

    def run_stress(self, service_name):        
        try:
            duration = self.stressor_data['duration']      
            # duration = 1
            command = f'docker exec docker-compose-{service_name}-1 sh -c "stress-ng --timeout {str(duration * 60)}s'
            print(f'Running {service_name}')
            
            cpu_load = self.stressor_data['resource_load']
            resource_load = self.stressor_data['size']
            workers = self.stressor_data['workers']
            command += f' --cpu {workers} --cpu-load {cpu_load}'
            command += f' --vm {workers} --vm-bytes {resource_load}'
            command += f' --hdd {workers} --hdd-bytes {resource_load}"'
                
            stress_timespan_results = self.run_command_command(command)

            print(f"Timespan results {stress_timespan_results}")
            return stress_timespan_results

        except Exception as e:
            print(e)
            raise e
        
    def get_system_metrics(self, app_data, treatment_results, path):
        print('\033[92m' + 'Gathering Data...' + '\033[0m')

        start_time, end_time = treatment_results
        print(f"Start time: {start_time} End time: {end_time}")

        output_file = os.path.join(path, 'metrics.csv')

        script_path = f"../vuDevOps/data_collection{app_data['metrics']['script']}"
        command = (
            f"python3 {script_path} " 
            f"--ip {app_data['metrics']['prometheus_url']} "
            f"--start {start_time} "
            f"--end {end_time} "
            f"--output {output_file}"
        )
        
        p = subprocess.Popen(command, shell=True)
        p.wait()
        
        print('\033[92m' + f'Data Collected and available at {path}' + '\033[0m')
        
        
    def start_measurement(self, context: RunnerContext) -> None:
        """Perform any activity required for starting measurements."""
        output.console_log("Config.start_measurement() called!")
        # Run stress and collect metrics 
        service_stressed = context.run_variation['service_stressed']
        scenario = context.run_variation['scenario']
        user_load = context.run_variation['user_load']
        repetition = context.run_variation['repetition_id']

        base_dir = Path('../vuDevOps/data_collection/trainticket-data')

        dir_path = base_dir / scenario / 'anomalous' / service_stressed / str(user_load) / f'repetition_{repetition}'

        treatment_results = self.run_stress(service_stressed)   

        self.get_system_metrics(self.app_data, treatment_results, dir_path)     


    def interact(self, context: RunnerContext) -> None:
        """Perform any interaction with the running target system here, or block here until the target finishes."""

        output.console_log("Config.interact() called!")

    def run_cooldown(self, app_data, traffic_process):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print('\033[92m' + "Starting cooldown script" + '\033[0m')
        duration = app_data['cooldown_duration']
        # duration = 1

        # Terminate locust subprocess
        print('\033[92m' + f"Terminating Load Generation for {traffic_process.pid} at {timestamp}" + '\033[0m')
        if traffic_process != None:
            os.killpg(os.getpgid(traffic_process.pid), signal.SIGKILL) #DEVNULL disregards the output

        locust_process_name = "locust"
        locust_script_process_name = "runLocust.sh"
        
        subprocess.run(["sudo", "killall", locust_process_name], check=False)
        subprocess.run(["sudo", "killall", locust_script_process_name], check=False)

        
        # Shhhh the serer is resting
        print('\033[92m' + f'Server resting for {duration} m' + '\033[0m')
        time_seconds = (duration * 60)
        time.sleep(time_seconds)

        print('\033[92m' + 'Hybernation Complete' + '\033[0m')

    def stop_measurement(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping measurements."""

        output.console_log("Config.stop_measurement called!")
        self.run_cooldown(self.app_data, self.traffic_process)


    def stop_run(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping the run.
        Activities after stopping the run should also be performed here."""

        output.console_log("Config.stop_run() called!")

        output.console_log("Stopping system...")

        p = subprocess.Popen('docker compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.cadvisor.yml down', shell=True)
        p.wait()
        p = subprocess.Popen('docker compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.trainticket.yml --env-file ../vuDevOps/microservices-demo/.env down', shell=True)
        p.wait()
        p = subprocess.Popen('docker compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.scaphandre.yml down', shell=True)
        p.wait()

    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, Any]]:
        """Parse and process any measurement data here.
        You can also store the raw measurement data under `context.run_dir`
        Returns a dictionary with keys `self.run_table_model.data_columns` and their values populated"""

        output.console_log("Config.populate_run_data() called!")

        service_stressed = context.run_variation['service_stressed']
        scenario = context.run_variation['scenario']
        user_load = context.run_variation['user_load']
        repetition = context.run_variation['repetition_id']

        base_dir = Path('../vuDevOps/data_collection/trainticket-data')

        metrics_path = base_dir / scenario / 'anomalous' / service_stressed / str(user_load) / f'repetition_{repetition}' / 'metrics.csv'

        metrics_df = pd.read_csv(metrics_path)

        services = [
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
        ]

        run_data = {}
        for service in services:
            cpu_col = f'{service}_cpu'
            mem_col = f'{service}_memory'
            mem_rss_col = f'{service}_memory_rss'
            mem_cache_col = f'{service}_memory_cache'
            disk_col = f'{service}_disk'
            power_col = f'{service}_power'
            
            if cpu_col in metrics_df.columns:
                run_data[f'{service}_avg_cpu'] = round(metrics_df[cpu_col].mean(), 3)
            if mem_col in metrics_df.columns:
                run_data[f'{service}_avg_mem'] = round(metrics_df[mem_col].mean(), 3)
            if mem_rss_col in metrics_df.columns:
                run_data[f'{service}_avg_mem_rss'] = round(metrics_df[mem_rss_col].mean(), 3)
            if mem_cache_col in metrics_df.columns:
                run_data[f'{service}_avg_mem_cache'] = round(metrics_df[mem_cache_col].mean(), 3)
            if disk_col in metrics_df.columns:
                run_data[f'{service}_avg_disk'] = round(metrics_df[disk_col].mean(), 3)
            if power_col in metrics_df.columns:
                run_data[f'{service}_avg_power'] = round(metrics_df[power_col].mean(), 9)

        return run_data

    def after_experiment(self) -> None:
        """Perform any activity required after stopping the experiment here
        Invoked only once during the lifetime of the program."""

        output.console_log("Config.after_experiment() called!")
        output.console_log("Bringing system down...")

        p = subprocess.Popen('docker compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.cadvisor.yml down', shell=True)
        p.wait()
        p = subprocess.Popen('docker compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.trainticket.yml --env-file ../vuDevOps/microservices-demo/.env down', shell=True)
        p.wait()
        p = subprocess.Popen('docker compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.scaphandre.yml down', shell=True)
        p.wait()

        print('\033[92m' + 'Experiment is Complete! WOOHOO! 🚀' + '\033[0m')

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path:            Path             = None
