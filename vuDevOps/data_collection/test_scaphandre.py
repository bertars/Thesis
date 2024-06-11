import asyncio
import datetime
import os
import signal
import subprocess
import sys
import threading
import time
import pandas as pd

# Initialize a list to store CPU temperature readings in the global scope
cpu_temperature_readings0 = []
cpu_temperature_readings1 = []
cpu_temperature_readings2 = []



def generate_load():
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #Send traffic against the front-end service (ACTUALLY, send it to edge-router (why?))
    print('\033[92m'+ timestamp + f' Sending traffic to the target system at 145.108.225.16:9099' + '\033[0m')
    
    process =  subprocess.Popen(f"./load-test/runLocust.sh -h 145.108.225.16:9099 -r {int(900)}s", shell=True, preexec_fn=os.setsid)
    # Locust needs a few seconds to deploy all traffic
    time.sleep(10)
    return process

def get_cpu_temperature(thermal_zone_path):
    try:
        with open(thermal_zone_path, 'r') as file:
            temp_str = file.read()
            temperature = int(temp_str) / 1000.0  # Convert from millidegrees to degrees Celsius
            return temperature
    except Exception as e:
        print(f"Error reading CPU temperature: {str(e)}")
        return None

async def run_stress_command(start_time, total_duration, stress_command, interval_between_runs):
    while (time.time() - start_time) < total_duration:
        # Run the stress command
        print('Stressing...')
        process = await asyncio.create_subprocess_shell(stress_command)
        await process.communicate()
        print('Sleeping...')
        await asyncio.sleep(interval_between_runs)

async def poll_cpu_temperature(start_time, total_duration, cpu_check_interval):
    print("Started")
    global cpu_temperature_readings0  # Declare that we are using the global list
    global cpu_temperature_readings1  # Declare that we are using the global list
    global cpu_temperature_readings2  # Declare that we are using the global list
    thermal_zone_path0 = '/sys/class/thermal/thermal_zone0/temp'
    thermal_zone_path1 = '/sys/class/thermal/thermal_zone1/temp'
    thermal_zone_path2 = '/sys/class/thermal/thermal_zone2/temp'
    while (time.time() - start_time) < total_duration:
        cpu_temperature0 = get_cpu_temperature(thermal_zone_path0)
        cpu_temperature1 = get_cpu_temperature(thermal_zone_path1)
        cpu_temperature2 = get_cpu_temperature(thermal_zone_path2)
        if cpu_temperature0 is not None:
            print(f"CPU Temperature: {cpu_temperature0}°C")
            sys.stdout.flush()  # Flush the output to ensure immediate printing
            cpu_temperature_readings0.append(cpu_temperature0)
        if cpu_temperature1 is not None:
            print(f"CPU Temperature: {cpu_temperature0}°C")
            sys.stdout.flush()  # Flush the output to ensure immediate printing
            cpu_temperature_readings1.append(cpu_temperature1)
        if cpu_temperature2 is not None:
            print(f"CPU Temperature: {cpu_temperature2}°C")
            sys.stdout.flush()  # Flush the output to ensure immediate printing
            cpu_temperature_readings2.append(cpu_temperature2)
        await asyncio.sleep(cpu_check_interval)

if __name__ == "__main__":
    print('Starting experiment')
    stress_duration  = 60
    os.makedirs('./scaph-data', exist_ok=True)
    result_csv_path = './scaph-data/scaph.csv'
    memory = "921M"
    stress_command =f'docker exec orders sh -c "stress-ng --temp-path /tmp/ --timeout {str(stress_duration)}s --vm {1} --vm-bytes {memory}"'

    #Install Stress NG
    install_stress_command = f'docker exec -u root -it shipping sh -c "apk update && apk add iproute2 && apk add --no-cache stress-ng --repository http://dl-cdn.alpinelinux.org/alpine/edge/community && apk add --no-cache musl>1.1.20 --repository http://dl-cdn.alpinelinux.org/alpine/edge/main"'
    print(install_stress_command)
    install_process = subprocess.Popen(install_stress_command, shell=True)
    install_process.wait()
    print('\n')
    
    #Generate load with locust
    locust_process = generate_load()
            
    total_duration = 900

    # Set the interval between runs (15 seconds)
    interval_between_runs = 30
    cpu_check_interval = 5
    start_time = time.time()
    
    loop = asyncio.get_event_loop()

    loop.run_until_complete(asyncio.gather(run_stress_command(start_time, total_duration, stress_command, interval_between_runs), poll_cpu_temperature(start_time, total_duration, cpu_check_interval)))

    end_time = time.time()
    
    print('\033[92m' + 'Gathering Data...' + '\033[0m')
  
    command = (
        f"python3 ./metrics/get_metrics.py " 
        f"--ip 145.108.225.16:30000 "
        f"--start {start_time} "
        f"--end {end_time} "
        f"--output {result_csv_path}"
    )
    
    p = subprocess.Popen(command, shell=True)
    p.wait()
    
    print('\033[92m' + f'Data Collected and available at {result_csv_path}' + '\033[0m')
    
    if locust_process != None:
        os.killpg(os.getpgid(locust_process.pid), signal.SIGKILL)
        
    df = pd.read_csv(result_csv_path)

    # If the length of CPU temperature readings does not match the number of rows in the DataFrame
    if len(cpu_temperature_readings0) != len(df):
        # Fill the DataFrame with a placeholder value (e.g., NaN)
        placeholder = cpu_temperature_readings0[1]  # You can use other values like 'NaN' if needed

        # Determine how many rows need to be added or removed
        num_rows_to_add = len(df) - len(cpu_temperature_readings0)

        if num_rows_to_add > 0:
            # Append the placeholder value to the DataFrame for the missing rows
            for _ in range(num_rows_to_add):
                cpu_temperature_readings0.append(placeholder)
        elif num_rows_to_add < 0:
            # Remove extra rows from the DataFrame
            df = df.iloc[:len(cpu_temperature_readings0)]
            
    if len(cpu_temperature_readings1) != len(df):
        # Fill the DataFrame with a placeholder value (e.g., NaN)
        placeholder = cpu_temperature_readings1[1]  # You can use other values like 'NaN' if needed

        # Determine how many rows need to be added or removed
        num_rows_to_add = len(df) - len(cpu_temperature_readings1)

        if num_rows_to_add > 0:
            # Append the placeholder value to the DataFrame for the missing rows
            for _ in range(num_rows_to_add):
                cpu_temperature_readings1.append(placeholder)
        elif num_rows_to_add < 0:
            # Remove extra rows from the DataFrame
            df = df.iloc[:len(cpu_temperature_readings1)]
            
    if len(cpu_temperature_readings2) != len(df):
        # Fill the DataFrame with a placeholder value (e.g., NaN)
        placeholder = cpu_temperature_readings2[1]  # You can use other values like 'NaN' if needed

        # Determine how many rows need to be added or removed
        num_rows_to_add = len(df) - len(cpu_temperature_readings2)

        if num_rows_to_add > 0:
            # Append the placeholder value to the DataFrame for the missing rows
            for _ in range(num_rows_to_add):
                cpu_temperature_readings2.append(placeholder)
        elif num_rows_to_add < 0:
            # Remove extra rows from the DataFrame
            df = df.iloc[:len(cpu_temperature_readings2)]

    # Add the 'CPU_Temperature' column to the DataFrame
    df['CPU_Temperature_0'] = cpu_temperature_readings0
    df['CPU_Temperature_1'] = cpu_temperature_readings1
    df['CPU_Temperature_2'] = cpu_temperature_readings2
    
    # Write the updated DataFrame to a new CSV file
    df.to_csv(result_csv_path, index=False)

    