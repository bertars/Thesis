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

    app_config_path:            str             = "../vuDevOps/data_collection/sockshop_config.json"
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
        factor2 = FactorModel("anomaly_type", ['resource', 'time'])
        factor3 = FactorModel("service_stressed", ['orders', 'front-end'])
        factor4 = FactorModel("user_load", [100, 1000])
        repetitions = FactorModel("repetition_id", [1])
        # repetitions = FactorModel("repetition_id", list(range(1, 31)))

        services = [
            'front-end', 'edge-router', 'catalogue', 'catalogue-db', 'carts', 'carts-db',
            'orders', 'orders-db', 'shipping', 'queue-master', 'rabbitmq', 'payment',
            'user', 'user-db', 'user-sim'
        ]
        metrics = ['avg_cpu', 'avg_mem', 'avg_mem_rss', 'avg_mem_cache', 'disk', 'power', 'request_duration']
        data_columns = [f"{metric}_{service}" for metric in metrics for service in services]
        
        self.run_table_model = RunTableModel(
        factors=[factor1, factor2, factor3, factor4, repetitions],
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
        stress_ng_command = "apk update && apk add iproute2 && apk add --no-cache stress-ng --repository http://dl-cdn.alpinelinux.org/alpine/edge/community && apk add --no-cache 'musl>1.1.20' --repository http://dl-cdn.alpinelinux.org/alpine/edge/main"
        install_stress_command = f'docker exec -u root -it {service_name} sh -c "{stress_ng_command}"'
        subprocess.run(install_stress_command, shell=True, check=True)

    # def generate_load(self, app_data, experiment,trial,treatments, log_file):
    #     # locust is used for SockShop
    #     if app_data['load_script_type'] == "locust":
    #         timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #         print('\033[92m'+ timestamp + f' Sending traffic to the target system at {app_data["host_url"]}' + '\033[0m')
            
    #         process = None
            
    #         for treatment in treatments:
    #             user_count = experiment[trial][treatment]['users']['count']
    #             user_spawn_rate = experiment[trial][treatment]['users']['count'] * 0.1
    #             scenario = experiment[trial][treatment]['scenario']['id']
    #             process =  subprocess.Popen(f"{app_data['load_script']} -h {app_data['host_url']} -r {int(100)}s -l {log_file} -u {user_count} -s {user_spawn_rate} -n {scenario}", shell=True, preexec_fn=os.setsid)
    #             # Locust needs a few seconds to deploy all traffic
    #             time.sleep(10)
    #         return process
    
    # def run_treatments(treatments,trial, experiment, locust_load_count):
    #     """
    #     Parameters:
    #     treatments (List<int>): Represents the list of treatment index positions for the current repetition
        
    #     data (List<List<JSONObjec>): Represents the total combinations of treatments
        
    #     traffic_process (int): Represents the PID for the locust process
        
    #     locust_load_count (int): Represents the next iteration of the locust process. Used for creating locust logs
    #     """
    #     treatment_file_paths = []
    #     treatment_results = []
        
    #     for treatment in treatments:
    #         # Create the new directory for current stressors
    #         if experiment[trial][treatment]['stressor']['id'] == 'normal':      
    #             prefix = f"{experiment[trial][treatment]['stressor']['id']}/{experiment[trial][treatment]['users']['name']}/{experiment[trial][treatment]['scenario']['id']}"
    #             locust_prefix = f"{experiment[trial][treatment]['stressor']['id']}/{experiment[trial][treatment]['users']['name']}/{experiment[trial][treatment]['scenario']['id']}/{locust_load_count}"
    #         else:
    #             prefix = f"{experiment[trial][treatment]['service']}/{experiment[trial][treatment]['stressor']['id']}/{experiment[trial][treatment]['users']['name']}/{experiment[trial][treatment]['scenario']['id']}"
    #             locust_prefix = f"{experiment[trial][treatment]['service']}/{experiment[trial][treatment]['stressor']['id']}/{experiment[trial][treatment]['users']['name']}/{experiment[trial][treatment]['scenario']['id']}/{locust_load_count}"

    #         treatment_file_paths.append(generate_file_path(app_data, prefix))
            

    #     create_locust_log(locust_prefix)
        
    #     time.sleep(2)

    #     # Generate traffic with locust
    #     traffic_process = generate_load(app_data, experiment,trial,treatments, f'{locust_logs}/{locust_prefix}/Locust_log')
        
        

    def start_run(self, context: RunnerContext) -> None:
        """Perform any activity required for starting the run here.
        For example, starting the target system to measure. 
        Activities after starting the run should also be performed here."""

        output.console_log("Config.start_run() called!")

        output.console_log("Bringing system up...")

        p = subprocess.Popen('sudo docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.cadvisor.yml up -d', shell=True)
        p.wait()
        p = subprocess.Popen('sudo docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.yml up -d', shell=True)
        p.wait()
        p = subprocess.Popen('sudo docker-compose -f ../vuDevOps/microservices-demo/deploy/docker-compose/docker-compose.scaphandre.yml up -d', shell=True)
        p.wait()

        print('Warm-up time')
        time.sleep(WARMUP * 60)
        service_stressed = context.run_variation['service_stressed']
        self.install_stress_ng(service_stressed)
        scenario = context.run_variation['scenario']
        anomaly = context.run_variation['anomaly_type']
        user_load = context.run_variation['user_load']
        print(f'Current treatment {scenario} - {anomaly} - {service_stressed} - {user_load}')



    def start_measurement(self, context: RunnerContext) -> None:
        """Perform any activity required for starting measurements."""
        output.console_log("Config.start_measurement() called!")
        # Run stress and collect metrics 


    def interact(self, context: RunnerContext) -> None:
        """Perform any interaction with the running target system here, or block here until the target finishes."""

        output.console_log("Config.interact() called!")

    def stop_measurement(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping measurements."""

        output.console_log("Config.stop_measurement called!")

    def stop_run(self, context: RunnerContext) -> None:
        """Perform any activity here required for stopping the run.
        Activities after stopping the run should also be performed here."""

        output.console_log("Config.stop_run() called!")
        # Cooldown Period, allow the system to rest, its going to be a long experiment -_-

    def populate_run_data(self, context: RunnerContext) -> Optional[Dict[str, Any]]:
        """Parse and process any measurement data here.
        You can also store the raw measurement data under `context.run_dir`
        Returns a dictionary with keys `self.run_table_model.data_columns` and their values populated"""

        output.console_log("Config.populate_run_data() called!")
        return None

    def after_experiment(self) -> None:
        """Perform any activity required after stopping the experiment here
        Invoked only once during the lifetime of the program."""

        output.console_log("Config.after_experiment() called!")

    # ================================ DO NOT ALTER BELOW THIS LINE ================================
    experiment_path:            Path             = None
