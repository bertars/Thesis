
# 1. Introduction
The following repo contains the necessary files to reproduce the data processing, training and execution of Anomaly Detection and Root Cause Analysis algorithms.

# 2. Install necessary plugins
Create and activate a Python virtual environment, and install the required modules using the following commands:
```zsh
cd $HOME/Data Analysis/AD
python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt
pip install pycaret --use-pep517
```

# 3 Running the data processing script

## 3.1 Time-sensitivity Analysis, Energy Usage, and Anomaly Detection 
This script will convert power metrics into energy consumption, perform the time-sensitivity analysis for 5, 10, 30 and 60 time-window configurations, train the AD models, create the Ground Truth, and lastly, run the previously trained AD models on the anomalous dataset. This script has to be executed for each system in order to generate the results. For this phase, the script has a parameter at the top of the file %SYSTEM%, that can be used to distinguish the system the script is supposed to be executed for.
```zsh
python3 time_analysis_and_AD_execution.py
```

## 3.2 Root cause analysis 
### 3.2.1 RCD and e-diagnosis
This script will train and run RCA models RCD and e-diagnosis. For this phase, the script has a parameter at the top of the file %SYSTEM%, that can be used to distinguish the system the script is supposed to be executed for.
```zsh
cd $HOME/Data Analysis/RCA/e-Diagnosis \& RCD-PyRCA
python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt
pip install .
```
Running the script
```zsh
python3 pyRCA.py
```


### 3.2.1 MicroRCA
This script will run the MicroRCA algorithm on the anomalous dataset. For this phase, the script has a parameter at the top of the file %SYSTEM%, that can be used to distinguish the system the script is supposed to be executed for.
```zsh
cd $HOME/Data Analysis/RCA/MicroRCA
python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt
```

```zsh
python3 microRCA.py
```

# 4 Descriptive Statistics and Plots
This script will compute per treatment, per time-window, and overall results for the performance metrics Precision, Recall and F-Score for AD algorithms, and PR@1,2,3 as well as MAP for RCA algorithms. Using these results, we export .csv files that reflect the results for the aforementioned scenarios in a table-like format, available in the Experiment Results/Descriptive statistics folder. Additionally, we also export a visual representation of the same metrics using CDF plots, as well as Resource Usage line charts for CPU and Memory, and Histograms for Energy with representative bins for the various time windows available. These plots are available in Experiment Results/Plots section, separated by each system. For this phase, the script has a parameter at the top of the file %SYSTEM%, that can be used to distinguish the system the script is supposed to be executed for.
```zsh
cd $HOME/Data Analysis/Statistics and Plots
python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt
```

```zsh
python3 statistics_and_plots.py
```


