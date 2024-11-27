# Study Design
If you want to replicate the study, follow the following steps:
## Phase 1: Controlled Experiment and Dataset Construction
### Systems Deployment
You can find the documentation on how to deploy the Systems Under Test (SUT) and monitoring tools with Docker in [`vuDevOps/microservices-demo/README.md`](https://github.com/bertars/Thesis/blob/main/vuDevOps/microservices-demo/README.md)

### Experiment Setup and Execution
In this study, [Experiment Runner](https://github.com/S2-group/experiment-runner/) was used to automatically execute the experiment.

You can find the documentation to run the experiment for:

- Baseline: [`experiment-runner/examples/baseline`](https://github.com/bertars/Thesis/tree/main/experiment-runner/examples/baseline)

- Sockshop: [`experiment-runner/examples/sockshop`](https://github.com/bertars/Thesis/tree/main/experiment-runner/examples/sockshop)

- TrainTicket: [`experiment-runner/examples/trainticket`](https://github.com/bertars/Thesis/tree/main/experiment-runner/examples/trainticket)

### Data Collection
All the documentation, programs, and files used for the data collection during the experiment execution can be found in the [`vuDevOps/data_collection`](https://github.com/bertars/Thesis/tree/main/vuDevOps/data_collection) folder.

Moreover, you can find the raw data collected during the experiment in the following folders:

- Sockshop data: [`vuDevOps/data_collection/sockshop-data`](https://github.com/bertars/Thesis/tree/main/vuDevOps/data_collection/sockshop-data)

- TrainTicket data: [`vuDevOps/data_collection/trainticket-data`](https://github.com/bertars/Thesis/tree/main/vuDevOps/data_collection/trainticket-data)

### Code Used for Full Experiment

```zsh
# After deploying the systems and monitoring tools:
tmux

sudo docker login

getent group docker

sudo usermod -aG docker berta

newgrp docker

id -nG

cd vuDevOps/data_collection

python3 -m venv .venv

source .venv/bin/activate

pip3 install -r requirements.txt

cd ../../experiment-runner

python3 experiment-runner/ examples/baseline/RunnerConfig.py
# OR
python3 experiment-runner/ examples/sockshop/RunnerConfig.py
# OR
python3 experiment-runner/ examples/trainticket/RunnerConfig.py

```

## Phase 2: Execution and Analysis of Anomaly Detection (AD) and Root Cause Analysis (RCA) algorithms

All the necessary files to reproduce the data processing, training, and execution of the AD and RCA algorithms can be found in the [`data_analysis`](https://github.com/bertars/Thesis/tree/main/data_analysis) folder.

### Anomaly Detection 

In the [`data_analysis/AD`](https://github.com/bertars/Thesis/tree/main/data_analysis/AD) folder you will find:

- [`anomaly_detection_models`](https://github.com/bertars/Thesis/tree/main/data_analysis/AD/anomaly_detection_models) folder, where the trained AD models are stored
- [`results`](https://github.com/bertars/Thesis/tree/main/data_analysis/AD/results) folder, where the results for the AD algorithms are stored
- `AD_execution.ipynb`: Jupyter notebook where all the data preprocessing and visualization, as well as the training and execution of the AD algorithms, is done.
- `anomalous_data.csv`: Sockshop dataset where all the anomalous data collected (stressing specific services) has been combined
- `ts-anomalous_data.csv`: TrainTicket dataset where all the anomalous data collected (stressing specific services) has been combined
- `normal_data.csv`: Sockshop dataset where all the normal data collected (without any stress) has been combined
- `ts-normal_data.csv`: TrainTicket dataset where all the normal data collected (without any stress) has been combined
- `ground_truth.csv`: The ground truth for the Sockshop dataset to compare the AD algorithms against
- `ts-ground_truth.csv`: The ground truth for the TrainTicket dataset to compare the AD algorithms against
- `anomalous_detection_execution_metrics.csv`: Average CPU and memory usage during the execution of the AD algorithms for the Sockshop dataset
- `ts-anomalous_detection_execution_metrics.csv`: Average CPU and memory usage during the execution of the AD algorithms for the TrainTicket dataset

### Root Cause Analysis
In the [`data_analysis/RCA`](https://github.com/bertars/Thesis/tree/main/data_analysis/RCA) folder you will find different folders for the RCA algorithms, including:

- [`CausalRCA`](https://github.com/bertars/Thesis/tree/main/data_analysis/RCA/CausalRCA)
- [`MicroRCA`](https://github.com/bertars/Thesis/tree/main/data_analysis/RCA/MicroRCA)
- [`PyRCA`](https://github.com/bertars/Thesis/tree/main/data_analysis/RCA/PyRCA)
- [`results`](https://github.com/bertars/Thesis/tree/main/data_analysis/RCA/results), where the results for the RCA algorithms are stored

### Statistics
In the [`data_analysis/Statistics`](https://github.com/bertars/Thesis/tree/main/data_analysis/Statistics) folder, you will find the following:

- [`Descriptive statistics`](https://github.com/bertars/Thesis/tree/main/data_analysis/Statistics/Descriptive%20statistics) folder, where the final statistics for the AD and RCA algorithms after analyzing the Sockshop and TrainTicket datasets are stored.
- `statistics.ipynb`: Jupyter notebook to compute the overall and detailed results for the AD and RCA algorithms, as well as to generate descriptive plots
