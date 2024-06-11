# 1. Introduction
The following repo contains the necessary files to reproduce the data gathering phase our experiment. The systems used for our experimentation are [SockShop](https://github.com/microservices-demo/microservices-demo) and [UNI-Cloud](https://marxact.com/nl/uni-cloud/). To ensure that the project results are reproducible, new repos for the code of these systems were created to accommodate any changes we have introduced to help with the execution of the experiment.

The following data collection scripts and evaluation tools were designed to be able to execute on any microservice with minimum setup. However, this repo's sole purpose is to help with the reproducibility of our results for the uDevOps project. 

# 2. Data Gathering
This section describes how to gather performance and energy data from SockShop or UNI-Cloud using Prometheus. 
## 2.1 Requirements:
### 2.1.1 Requirement 1:
Before running the data collection process it is important to have SockShop or UNI-Cloud up and running, along with all monitoring services. For more information, please look at the documentation under the [vuDevOps/microservices-demo](https://github.com/MaxiStefan/Thesis/blob/main/vuDevOps/microservices-demo/README.md) folder.
### 2.1.2 Requirement 2:
Create and activate a Python virtual environment, and install the required modules using the following commands:
```zsh
cd $HOME/vuDevOps/data_collection
python3 -m venv .venv

source .venv/bin/activate

pip3 install -r requirements.txt
```


## 2.2 Editing Configs (Optional)
There are two types of configs for data collection: the application config and the stressor config. We have two application configs, one for each target system, Sock Shop and UNI-Cloud. The config files contain information such as, name, services to be tested, and file pathing. Additionally, further experiment configurations such as user loads and usage scenarios can be configured via these config files. The names of the files are as follows:
```zsh
sockshop_config.json
unicloud_config.json
```
The stressor config file contains information about anomalies that are injected in target application services in the form of hardware resource stressing. In particular, stressor config is comprised of details about the type of stressors to deploy using stress-ng, the number of trials per stressor, and the duration of each trial run. 
```zsh
stressor_config.json
```

## 2.3 Running
To initiate the data collection process for the target applications use the command below. It is advised to use Tmux (terminal multiplexer) or something similar to detach from the terminal in which the process is running as the process can take a few days to complete.
```zsh
python3 collect_data.py
```

Once the script is ran you might be promted to continue or generate a new experiment. In the case the experiment fails for whatever reason (e.g. bad data, power outage) you can resume the experiment from the last succesfully run trial. 

# 3. Running AD and RCD
Instructions for running Anomaly Detection and Root Cause Analysis tools are available within the [Data Analysis](https://github.com/MaxiStefan/Thesis/blob/main/Data%20Analysis/README.md) folder.
