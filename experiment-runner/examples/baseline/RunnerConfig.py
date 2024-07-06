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
# import requests
import datetime
import json
import os 
import signal

WARMUP = 0
DURATION = 1

class RunnerConfig:
    ROOT_DIR = Path(dirname(realpath(__file__)))

    # ================================ USER SPECIFIC CONFIG ================================
    """The name of the experiment."""
    name:                       str             = "baseline"

    """The path in which Experiment Runner will create a folder with the name `self.name`, in order to store the
    results from this experiment. (Path does not need to exist - it will be created if necessary.)
    Output path defaults to the config file's path, inside the folder 'experiments'"""
    results_output_path:        Path             = ROOT_DIR / 'experiments'

    """Experiment operation type. Unless you manually want to initiate each run, use `OperationType.AUTO`."""
    operation_type:             OperationType   = OperationType.AUTO

    """The time Experiment Runner will wait after a run completes.
    This can be essential to accommodate for cooldown periods on some systems."""
    time_between_runs_in_ms:    int             = 1000

    sock_app_config_path:       str             = "../vuDevOps/data_collection/sockshop_config.json"
    ts_app_config_path:         str             = "../vuDevOps/data_collection/trainticket_config.json"
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
        self.sock_app_data = None
        self.ts_app_data = None
        self.stressor_data = None
        self.system = None
        self.traffic_process = None

        output.console_log("Custom config loaded")

    def load_configs(self):
        with open(self.sock_app_config_path, 'r') as f:
            self.sock_app_data = json.load(f)
        with open(self.ts_app_config_path, 'r') as f:
            self.ts_app_data = json.load(f)
        with open(self.stressor_config_path, 'r') as f:
            self.stressor_data = json.load(f)

    def create_run_table_model(self) -> RunTableModel:
        """Create and return the run_table model here. A run_table is a List (rows) of tuples (columns),
        representing each run performed"""
        factor1 = FactorModel("system", ['trainticket'])
        # factor1 = FactorModel("system", ['sockshop', 'trainticket'])
        factor2 = FactorModel("scenario", ['scenario_A', 'scenario_B'])
        factor3 = FactorModel("user_load", [100, 1000])
        repetitions = FactorModel("repetition_id", [1])
        # repetitions = FactorModel("repetition_id", list(range(1, 31)))

        services = [
            'front-end', 'catalogue', 'catalogue-db', 'carts', 'carts-db',
            'orders', 'orders-db', 'shipping', 'queue-master', 'rabbitmq', 'payment',
            'user', 'user-db',
            'redis', 'ts-ui-dashboard', 'ts-auth-service', 'ts-auth-mongo',
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

        print(f"Generated data columns (total {len(data_columns)}): {len(set(data_columns))}")
        
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
        self.load_configs()

    def before_run(self) -> None:
        """Perform any activity required before starting a run.
        No context is available here as the run is not yet active (BEFORE RUN)"""

        output.console_log("Config.before_run() called!")

    def generate_load(self, app_data, scenario, user_count, log_file):
        # locust is used for SockShop
        if app_data['load_script_type'] == "locust":
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print('\033[92m'+ timestamp + f' Sending traffic to the target system at {app_data["host_url"]}' + '\033[0m')
            
            process = None
                
            user_spawn_rate = 1
            script_path = f"../vuDevOps/data_collection{app_data['load_script']}"
            subprocess.run(["chmod", "+x", script_path], check=True)
            process =  subprocess.Popen(f"{script_path} -h {app_data['host_url']} -r {int(100)}s -l {log_file} -u {user_count} -s {user_spawn_rate} -n {scenario}", shell=True, preexec_fn=os.setsid)
            # Locust needs a few seconds to deploy all traffic
            time.sleep(2)
            return process    


    def start_run(self, context: RunnerContext) -> None:
        """Perform any activity required for starting the run here.
        For example, starting the target system to measure. 
        Activities after starting the run should also be performed here."""

        output.console_log("Config.start_run() called!")

        system = context.run_variation['system']
        self.system = system

        if system == 'sockshop':
            output.console_log("Bringing sockshop up...")
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.cadvisor.yml up -d', shell=True)
            p.wait()
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.yml up -d', shell=True)
            p.wait()
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.scaphandre.yml up -d', shell=True)
            p.wait()

            app_data = self.sock_app_data
        if system == 'trainticket':
            output.console_log("Bringing trainticket up...")
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.cadvisor.yml up -d', shell=True)
            p.wait()
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.trainticket.yml --env-file ../vuDevOps/microservices-demo/.env up -d', shell=True)
            p.wait()
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.scaphandre.yml up -d', shell=True)
            p.wait()

            app_data = self.ts_app_data

        print('Warm-up time')
        time.sleep(WARMUP * 60)        

        scenario = context.run_variation['scenario']
        user_load = context.run_variation['user_load']
        repetition = context.run_variation['repetition_id']

        print(f'Current treatment {system} - {scenario} - {user_load} - {repetition}')

        base_dir = Path(f"../vuDevOps/data_collection{app_data['metrics']['output_location']}")

        # Ensure the base directory exists
        os.makedirs(base_dir, exist_ok=True)

        # Create the directory path
        dir_path = base_dir / scenario / 'baseline' / str(user_load) / f'repetition_{repetition}'
    
        # Create the directories
        os.makedirs(dir_path, exist_ok=True)

        time.sleep(2)
        
        print(f'Created directory: {dir_path}')

        traffic_process = self.generate_load(app_data, scenario, user_load, f'{dir_path}/Locust_log')
        self.traffic_process = traffic_process


    def run_duration(self, duration):
        start_time = time.time()
        time.sleep(duration * 60)
        end_time = time.time()
        return start_time, end_time 
        
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
        # Collect metrics 

        if self.system == 'sockshop':
            app_data = self.sock_app_data
        if self.system == 'trainticket':
            app_data = self.ts_app_data        

        scenario = context.run_variation['scenario']
        user_load = context.run_variation['user_load']
        repetition = context.run_variation['repetition_id']

        base_dir = Path(f"../vuDevOps/data_collection{app_data['metrics']['output_location']}")

        dir_path = base_dir / scenario / 'baseline' / str(user_load) / f'repetition_{repetition}'

        treatment_results = self.run_duration(DURATION)   

        self.get_system_metrics(app_data, treatment_results, dir_path)     


    def interact(self, context: RunnerContext) -> None:
        """Perform any interaction with the running target system here, or block here until the target finishes."""

        output.console_log("Config.interact() called!")

    def run_cooldown(self, app_data, traffic_process):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print('\033[92m' + "Starting cooldown script" + '\033[0m')
        # duration = app_data['cooldown_duration']
        duration = 1

        # Terminate locust subprocess
        print('\033[92m' + f"Terminating Load Generation for {traffic_process.pid} at {timestamp}" + '\033[0m')
        if traffic_process != None:
            os.killpg(os.getpgid(traffic_process.pid), signal.SIGKILL) #DEVNULL disregards the output

        locust_process_name = "locust"
        locust_script_process_name = "runLocust.sh"
        ts_locust_script_process_name = "runTrainTicketLocust.sh"
        
        subprocess.run(["sudo", "killall", locust_process_name], check=False)
        subprocess.run(["sudo", "killall", locust_script_process_name], check=False)
        subprocess.run(["sudo", "killall", ts_locust_script_process_name], check=False)

        
        # Shhhh the serer is resting
        print('\033[92m' + f'Server resting for {duration} m' + '\033[0m')
        time_seconds = (duration * 60)
        time.sleep(time_seconds)

        print('\033[92m' + 'Hybernation Complete' + '\033[0m')

    def stop_measurement(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping measurements."""

        output.console_log("Config.stop_measurement called!")

        if self.system == 'sockshop':
            app_data = self.sock_app_data
        if self.system == 'trainticket':
            app_data = self.ts_app_data  

        self.run_cooldown(app_data, self.traffic_process)


    def stop_run(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping the run.
        Activities after stopping the run should also be performed here."""

        output.console_log("Config.stop_run() called!")

        if self.system == 'sockshop':
            output.console_log("Stopping sockshop...")
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.cadvisor.yml stop', shell=True)
            p.wait()
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.yml stop', shell=True)
            p.wait()
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.scaphandre.yml stop', shell=True)
            p.wait()

        if self.system == 'trainticket':
            output.console_log("Stopping trainticket...")
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.cadvisor.yml stop', shell=True)
            p.wait()
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.trainticket.yml --env-file ../vuDevOps/microservices-demo/.env stop', shell=True)
            p.wait()
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.scaphandre.yml stop', shell=True)
            p.wait()

    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, Any]]:
        """Parse and process any measurement data here.
        You can also store the raw measurement data under `context.run_dir`
        Returns a dictionary with keys `self.run_table_model.data_columns` and their values populated"""

        output.console_log("Config.populate_run_data() called!")

        if self.system == 'sockshop':
            app_data = self.sock_app_data
            services = [
                'front-end', 'catalogue', 'catalogue-db', 'carts', 'carts-db',
                'orders', 'orders-db', 'shipping', 'queue-master', 'rabbitmq', 'payment',
                'user', 'user-db'
            ]
        if self.system == 'trainticket':
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
            app_data = self.ts_app_data        

        scenario = context.run_variation['scenario']
        user_load = context.run_variation['user_load']
        repetition = context.run_variation['repetition_id']

        base_dir = Path(f"../vuDevOps/data_collection{app_data['metrics']['output_location']}")

        metrics_path = base_dir / scenario / 'baseline' / str(user_load) / f'repetition_{repetition}' / 'metrics.csv'

        metrics_df = pd.read_csv(metrics_path)

        

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

        if self.system == 'sockshop':
            output.console_log("Stopping sockshop...")
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.cadvisor.yml down', shell=True)
            p.wait()
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.yml down', shell=True)
            p.wait()
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.scaphandre.yml down', shell=True)
            p.wait()

        if self.system == 'trainticket':
            output.console_log("Stopping trainticket...")
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.cadvisor.yml down', shell=True)
            p.wait()
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.trainticket.yml --env-file ../vuDevOps/microservices-demo/.env down', shell=True)
            p.wait()
            p = subprocess.Popen('docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.scaphandre.yml down', shell=True)
            p.wait()

        print('\033[92m' + 'Experiment is Complete! WOOHOO! 🚀' + '\033[0m')

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path:            Path             = None
