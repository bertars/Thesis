
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

# 3 Running the data analysis

## 3.1 Anomaly Detection 
The Jupyter notebook `AD_execution.ipynb` will convert power metrics into energy consumption, train the AD models, create the Ground Truth, and lastly, run the previously trained AD models on the anomalous dataset. This script has to be executed for each system in order to generate the results. For this phase, the notebook has a parameter at the top of the file %SYSTEM%, that can be used to distinguish the system the code is supposed to be executed for.


## 3.2 Root cause analysis 
### 3.2.1 MicroRCA
The Jupyter notebook `microRCA.ipynb` will run the [MicroRCA](https://github.com/elastisys/MicroRCA) algorithm on the anomalous dataset. For this phase, the notebook has a parameter at the top of the file %SYSTEM%, that can be used to distinguish the system the code is supposed to be executed for.
```zsh
cd $HOME/data_analysis/RCA/MicroRCA
python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt
```

### 3.2.2 RCD and CIRCA
The Jupyter notebook `pyRCA.ipynb` will train and run RCA models RCD and CIRCA. For this phase, the notebook has a parameter at the top of the file %SYSTEM%, that can be used to distinguish the system the code is supposed to be executed for. 

The RCD and CIRCA algorithms have been taken from the [PyRCA](https://github.com/zhouruixingzhu/PyRCA) library, so you first would need to go to its repository and download the `pyrca` folder. Then you can do the following:
```zsh
cd $HOME/data_analysis/RCA/PyRCA
python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt
pip install .
```

### 3.2.3 CausalRCA
The Jupyter notebook `causalRCA.ipynb` will run the RCA model [CausalRCA](https://github.com/AXinx/CausalRCA_code). For this phase, the notebook has a parameter at the top of the file %SYSTEM%, that can be used to distinguish the system the code is supposed to be executed for. 

```zsh
cd $HOME/data_analysis/RCA/CausalRCA
python3 -m venv .venv

source .venv/bin/activate

pip install -r requirements.txt
```

# 4 Descriptive Statistics and Plots
The Jupyter notebook `statistics.ipynb` will compute per treatment and overall results for the performance metrics Precision, Recall and F-Score for AD algorithms, and PR@1,2,3 as well as MAP for RCA algorithms. Using these results, we export .csv files that reflect the results for the aforementioned scenarios in a table-like format, available in the [`data_analysis/Statistics/Descriptive statistics`](https://github.com/bertars/Thesis/tree/main/data_analysis/Statistics/Descriptive%20statistics) folder. For this phase, the notebook has a parameter at the top of the file %SYSTEM%, that can be used to distinguish the system the code is supposed to be executed for.

Additionally, we also export a visual representation of the same metrics using heatmaps. These plots are available in the Descriptive statistics folder, separated by each system and algorithm type. 



