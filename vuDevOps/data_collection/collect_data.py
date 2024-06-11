from concurrent.futures import ThreadPoolExecutor
import json
import os 
import random
import subprocess
import time
import signal
import pandas as pd
import requests
import datetime


# app_config      = "/home/floroiu/MasterProject/Thesis/vuDevOps/data_collection/sockshop_config.json"
# stressor_config = "/home/floroiu/MasterProject/Thesis/vuDevOps/data_collection/stressor_config.json"
app_config      = "sockshop_config.json"
# app_config      = "unicloud_config.json"
stressor_config = "stressor_config.json"
locust_logs = "./sockshop-locust-data"
# locust_logs = "./unicloud-locust-data"
warmup_time = 3

def generate_experiment(stressor_data, experiment_file):
  print('\033[92m' + f"Generating experiment for: {app_data['application_name']}" + '\033[0m')

  stressed_services = []
  for s in app_data["services"]:
    if s["stress"]:
      stressed_services.append(s["name"])
  
  # Create all possible combinations for each stressors and services 
  combinations = [(service, stressor, usage_scenario, user_load) for service in stressed_services for stressor in stressor_data["stressors"] for usage_scenario in app_data["usage_scenario"] for user_load in app_data["user_load"]]

  # Convert the combinations to a list of dictionaries and multiple by trials
  data = []
  for service, stressor, scenario, users in combinations:
      data.append({"service": service, "stressor": stressor,"scenario": scenario, "users": users, "duration": stressor_data['duration'], "output_folder": "","completed": False})
  
  combinations = [ (scenario, users) for scenario in app_data["usage_scenario"] for users in app_data["user_load"]]

  # Add normal operational runs to data
  for scenario, users in combinations:
    stressor = {"id": "normal","type": "normal",}
    data.append({"service": 'system', "stressor": stressor,"scenario": scenario,"users": users, "duration": stressor_data['duration'], "output_folder": "","completed": False})

  data_list = []
  for _ in range(1, stressor_data['trials'] + 1):
    # Shuffle each list inside the data
    random.shuffle(data)
    data_list.append(data)
  
  # Write the data to experiment file
  with open(experiment_file, 'w') as f: 
    json.dump(data_list, f)

  print('\033[92m' + f"Experiment for {app_data['application_name']} has been generated." + '\033[0m')



def bring_sockshop_up(experiment):  
  p = subprocess.Popen('docker-compose -f ../microservices-demo/deploy/docker-compose/docker-compose.cadvisor.yml up -d', shell=True)
  p.wait()
  p = subprocess.Popen('docker-compose -f ../microservices-demo/deploy/docker-compose/docker-compose.yml up -d', shell=True)
  p.wait()
  p = subprocess.Popen('docker-compose -f ../microservices-demo/deploy/docker-compose/docker-compose.scaphandre.yml up -d', shell=True)
  p.wait()
  
  print('Warm-up time')
  time.sleep(warmup_time * 60)
  install_stressng_inside_services(experiment)
  
def bring_unicloud_up(experiment):  
  p = subprocess.Popen('cd ../microservices-demo/deploy/docker-compose/rabbitmq/ && docker-compose up -d', shell=True)
  p.wait()
  p = subprocess.Popen('docker-compose -f ../microservices-demo/deploy/docker-compose/docker-compose.cadvisor.yml up -d', shell=True)
  p.wait()
  p = subprocess.Popen('docker-compose -f ../microservices-demo/deploy/docker-compose/docker-compose.unicloud.yml up -d', shell=True)
  p.wait()
  p = subprocess.Popen('docker-compose -f ../microservices-demo/deploy/docker-compose/docker-compose.scaphandre.yml up -d', shell=True)
  p.wait()
  
  print('Warm-up time')
  time.sleep(warmup_time * 60)
  install_stressng_inside_services(experiment)
  
def bring_unicloud_down():  
  p = subprocess.Popen('docker-compose -f ../microservices-demo/deploy/docker-compose/rabbitmq/docker-compose.yml down', shell=True)
  p.wait()
  p = subprocess.Popen('docker-compose -f ../microservices-demo/deploy/docker-compose/docker-compose.cadvisor.yml down', shell=True)
  p.wait()
  p = subprocess.Popen('docker-compose -f ../microservices-demo/deploy/docker-compose/docker-compose.unicloud.yml down', shell=True)
  p.wait()
  p = subprocess.Popen('docker-compose -f ../microservices-demo/deploy/docker-compose/docker-compose.scaphandre.yml down', shell=True)
  p.wait()
  
  
def bring_sockshop_down():  
  p = subprocess.Popen('docker-compose -f ../microservices-demo/deploy/docker-compose/docker-compose.cadvisor.yml down', shell=True)
  p.wait()
  p = subprocess.Popen('docker-compose -f ../microservices-demo/deploy/docker-compose/docker-compose.yml down', shell=True)
  p.wait()
  p = subprocess.Popen('docker-compose -f ../microservices-demo/deploy/docker-compose/docker-compose.scaphandre.yml down', shell=True)
  p.wait()

def run_command_command(command):
    start_time = time.time()
    process = subprocess.Popen(command, shell=True)
    process.wait()
    end_time = time.time()
    return start_time, end_time

def run_stress(experiment, trial, treatments):
  stress_commands = []
  stress_timespan_results = []
  
  try:
    for treatment in treatments:      
      service_name = experiment[trial][treatment]['service']
      stress_data = experiment[trial][treatment]['stressor']
      duration = experiment[trial][treatment]['duration']      
      command = f'docker exec {service_name} sh -c "stress-ng --temp-path /tmp/ --timeout {str(duration * 60)}s'
      print(f'Running {service_name}')
      if stress_data['id'] != 'normal':
        cpu_load = stress_data['resource_load']
        resource_load = stress_data['size']
        workers = stress_data['workers']
        command += f' --cpu {workers} --cpu-load {cpu_load}'
        command += f' --vm {workers} --vm-bytes {resource_load}'
        command += f' --hdd {workers} --hdd-bytes {resource_load}"'
      elif stress_data['type'] == "normal":
        print("Running normal operations")
        command = f'sleep {duration * 60}'
        
      #Add the command to the list of commands that should be executed
      stress_commands.append(command)

    # Create a ThreadPoolExecutor with a max_workers value that suits your needs
    max_workers = 1  # You can adjust this based on your system's capabilities
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        stress_timespan_results = list(executor.map(run_command_command, stress_commands))

    return stress_timespan_results

  except Exception as e:
    print(e)
    raise e


def generate_load(app_data, experiment,trial,treatments, log_file):
  # locust is used for SockShop
  if app_data['load_script_type'] == "locust":
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print('\033[92m'+ timestamp + f' Sending traffic to the target system at {app_data["host_url"]}' + '\033[0m')
    
    process = None
    
    for treatment in treatments:
      user_count = experiment[trial][treatment]['users']['count']
      user_spawn_rate = experiment[trial][treatment]['users']['count'] * 0.1
      scenario = experiment[trial][treatment]['scenario']['id']
      process =  subprocess.Popen(f"{app_data['load_script']} -h {app_data['host_url']} -r {int(100)}s -l {log_file} -u {user_count} -s {user_spawn_rate} -n {scenario}", shell=True, preexec_fn=os.setsid)
      # Locust needs a few seconds to deploy all traffic
      time.sleep(10)
    return process

def update_experiment_file(treatments,trial, experiment, output_folders, experiment_file):
  for index, output_folder in zip(treatments, output_folders):
      experiment[trial][index]['completed'] = True
      experiment[trial][index]['output_folder'] = output_folder

  with open(experiment_file, 'w') as f:
      json.dump(experiment, f)


def generate_file_path(app_data, prefix):
  base_directory = f"{app_data['metrics']['output_location']}/{prefix}"
  
  i = 1
  while True:
    unique_name = f'{i}_data.csv'
    file_path = os.path.join(base_directory, unique_name)
    if not os.path.exists(file_path):
        break
    i += 1

  output_folder = f'{base_directory}/{unique_name}'
  os.makedirs(base_directory, exist_ok=True)

  return output_folder

def get_system_metrics(app_data, treatments_results, paths):
  print('\033[92m' + 'Gathering Data...' + '\033[0m')
  
  for (start_time, end_time), file_path in zip(treatments_results, paths):
    command = (
        f"python3 {app_data['metrics']['script']} " 
        f"--ip {app_data['metrics']['prometheus_url']} "
        f"--start {start_time} "
        f"--end {end_time} "
        f"--output {file_path}"
    )
    
    p = subprocess.Popen(command, shell=True)
    p.wait()
    
    print('\033[92m' + f'Data Collected and available at {file_path}' + '\033[0m')

def run_cooldown(app_data, traffic_process):
  timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  print('\033[92m' + "Starting cooldown script" + '\033[0m')
  duration = app_data['cooldown_duration']

  # Terminate locust subprocess
  print('\033[92m' + f"Terminating Load Generation for {traffic_process.pid} at {timestamp}" + '\033[0m')
  if traffic_process != None:
    os.killpg(os.getpgid(traffic_process.pid), signal.SIGKILL) #DEVNULL disregards the output

  locust_process_name = "locust"
  locust_script_process_name = "runLocust.sh"
  
  subprocess.run(["killall", locust_process_name], check=False)
  subprocess.run(["killall", locust_script_process_name], check=False)

  
  # Shhhh the serer is resting
  print('\033[92m' + f'Server resting for {duration} m' + '\033[0m')
  time_seconds = (duration * 60)
  time.sleep(time_seconds)

  print('\033[92m' + 'Hybernation Complete' + '\033[0m')

def run_treatments(treatments,trial, experiment, locust_load_count):
  """
  Parameters:
  treatments (List<int>): Represents the list of treatment index positions for the current repetition
  
  data (List<List<JSONObjec>): Represents the total combinations of treatments
  
  traffic_process (int): Represents the PID for the locust process
  
  locust_load_count (int): Represents the next iteration of the locust process. Used for creating locust logs
  """
  treatment_file_paths = []
  treatment_results = []
  
  for treatment in treatments:
    # Create the new directory for current stressors
    if experiment[trial][treatment]['stressor']['id'] == 'normal':      
      prefix = f"{experiment[trial][treatment]['stressor']['id']}/{experiment[trial][treatment]['users']['name']}/{experiment[trial][treatment]['scenario']['id']}"
      locust_prefix = f"{experiment[trial][treatment]['stressor']['id']}/{experiment[trial][treatment]['users']['name']}/{experiment[trial][treatment]['scenario']['id']}/{locust_load_count}"
    else:
      prefix = f"{experiment[trial][treatment]['service']}/{experiment[trial][treatment]['stressor']['id']}/{experiment[trial][treatment]['users']['name']}/{experiment[trial][treatment]['scenario']['id']}"
      locust_prefix = f"{experiment[trial][treatment]['service']}/{experiment[trial][treatment]['stressor']['id']}/{experiment[trial][treatment]['users']['name']}/{experiment[trial][treatment]['scenario']['id']}/{locust_load_count}"

    treatment_file_paths.append(generate_file_path(app_data, prefix))
    

  create_locust_log(locust_prefix)
  
  time.sleep(2)

  # Gnerate traffic with locust
  traffic_process = generate_load(app_data, experiment,trial,treatments, f'{locust_logs}/{locust_prefix}/Locust_log')
  
  # Run stress and collect metrics 
  treatment_results = run_stress(experiment, trial, treatments)
  
  get_system_metrics(app_data, treatment_results, treatment_file_paths)
      
  # Update experiment file
  update_experiment_file(treatments, trial, experiment, treatment_file_paths, experiment_file)

  # Cooldown Period, allow the system to rest, its going to be a long experiment -_-
  run_cooldown(app_data, traffic_process)
  
def create_locust_log(path):

  folder_path = os.path.join(locust_logs, path)
  print(f'Creating {folder_path}')
  os.makedirs(folder_path, exist_ok=False)

def install_stressng_inside_services(experiment):
  unique_services = set()

  for experiment_treatment in experiment[0]:
      service = experiment_treatment["service"]
      if(service != "system"):
       unique_services.add(service)

  # Convert the set to a list if needed
  unique_services_list = list(unique_services)
  print(unique_services_list)
  
  for service_name in unique_services_list:
    # Install stress-ng within the service container.
      # For SockShop
      stress_ng_command = "apk update && apk add iproute2 && apk add --no-cache stress-ng --repository http://dl-cdn.alpinelinux.org/alpine/edge/community && apk add --no-cache musl>1.1.20 --repository http://dl-cdn.alpinelinux.org/alpine/edge/main"
      # For UNI-Cloud
      # stress_ng_command = "apt-get update &&  apt-get install -y apt-utils && apt-get install -y iproute2 && apt-get install -y stress-ng && apt-get install -y musl>1.1.20"
      install_stress_command = f'docker exec -u root -it {service_name}  sh -c "{stress_ng_command}"'
      print(install_stress_command)
      install_process = subprocess.Popen(install_stress_command, shell=True)
      install_process.wait()
      print('\n')
      
def start_or_continue_experiment(experiment):  
  current_treatment_index = 0
  current_trial_index = 0
  found_incompleted = False
  for repetition in experiment:
    for treatment in repetition:
      if treatment['completed']:
        current_treatment_index += 1
      else:
        found_incompleted = True
        break
    if found_incompleted:
      break
    current_treatment_index = 0
    current_trial_index += 1
    
  return (current_trial_index, current_treatment_index)

def execute_experiment(experiment_file):
  with open(experiment_file, 'r') as f:
    experiment = json.load(f)

  # Continue experiment from last successful run 
  current_treatment_index = 0
  current_trial_index = 0
  trials = len(experiment)
  treatments_in_trial = len(experiment[0])
  
  (current_trial_index, current_treatment_index) = start_or_continue_experiment(experiment)
  
  bring_sockshop_up(experiment)
  # bring_unicloud_up(experiment)
      
  print('\033[92m' + 'Starting experiment...' + '\033[0m')
  treatment_counter = 0
  locust_repetition_counter = 0
  # for i in range(start_from, data_len // 2): For multithreading stress scripts
  for trial_index in range(current_trial_index, trials):
    locust_repetition_counter = trial_index + 1
    for treatment_index in range(current_treatment_index, treatments_in_trial):
      treatment_counter += 1
      total_no_treatments = trials * treatments_in_trial
      print('\033[92m' + f'Current run is {treatment_counter} / {total_no_treatments}' + '\033[0m')
      # For multithreading
      # Create a list of indices that are not marked as completed
      available_treatments = [i for i in range(treatments_in_trial) if i >= current_treatment_index and not experiment[trial_index][i]['completed']]

      treatments = []  # To store indices of selected treatments
      for _ in range(1):
        # Randomly select an index within the range of available data        
        if available_treatments:
            random_index = random.choice(available_treatments)
            treatments.append(random_index)
            available_treatments.remove(random_index)
      for treatment in treatments:
        print(f'Selected treatment {treatment}')
        service_name = experiment[trial_index][treatment]['service']
        treatment_id = experiment[trial_index][treatment]['stressor']['id']
        treatment_scenario = experiment[trial_index][treatment]['scenario']['id']
        treatment_user_load = experiment[trial_index][treatment]['users']['count']
        print(f'Current treatment {service_name} - {treatment_id} - {treatment_scenario} - {treatment_user_load}')
        
        run_treatments(treatments,trial_index, experiment, locust_repetition_counter)
    
    print('Bringing the system down')
    bring_sockshop_down()
    # bring_unicloud_down()
    print('Bringing the system up')
    bring_sockshop_up(experiment)
    # bring_unicloud_up(experiment)
  
  bring_sockshop_down()
  # bring_unicloud_down()
      
  print('\033[92m' + 'Experiment is Complete! WOOHOO! 🚀' + '\033[0m')
  
    
if __name__ == "__main__":
  
  with open(app_config, 'r') as f:
    app_data = json.load(f)

  with open(stressor_config, 'r') as f:
    stressor_data = json.load(f)
  
  app_name = app_data['application_name']
  experiment_file = app_name + '-experiment.json'

  # Check if the experiment config already exists
  confirm = 'n'
  if os.path.exists(experiment_file):
    confirm = input("Experiment file already exists. Do you want continue with the experiment (y/n): ") or 'y'
    
  if confirm.lower() == 'y':
    print('\033[92m' + "Coninuting experiment..." + '\033[0m')
  else:
    generate_experiment(stressor_data, experiment_file)
  
  # Execute experiment 
  execute_experiment(experiment_file)

