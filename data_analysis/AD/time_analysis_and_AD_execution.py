
from datetime import datetime
import os
import shutil
from typing import List, Union
from pycaret.anomaly import *
import numpy as np
import pandas as pd
# import LSTM libraries
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import seaborn as sns
sns.set(color_codes=True)
import matplotlib.pyplot as plt
import tensorflow as tf
from keras.layers import Input, Dropout, Dense, LSTM, TimeDistributed, RepeatVector
from keras.models import Model
from keras import regularizers
#import BIRCH libraries
from sklearn.cluster import Birch
from sklearn import preprocessing
from scipy.spatial import distance

SYSTEM = 'sockshop'
# SYSTEM = 'unicloud'
# Define the main directory
TRAINING_DATA_FOLDER = f'C:\scul\Thesis\Data Analysis\{SYSTEM}-training-data'
DATA_FOLDER = f'C:\scul\Thesis\Data Analysis\{SYSTEM}-data'

RESULTS_FOLDER = f'C:\scul\Thesis\Experiment Results\{SYSTEM}-data'

AD_FOLDER = 'C:\scul\Thesis\Data Analysis\AD'
NORMAL_DATA_PATH = os.path.join(DATA_FOLDER, "normal")
AD_MODELS = ["iforest", "svm", "knn"]

SAVED_AD_MODELS_PATH = os.path.join(AD_FOLDER,"anomaly_detection_models")
LOCAL_AD_MODELS = os.path.join(SAVED_AD_MODELS_PATH,SYSTEM)

TIME_WINDOWS = [10, 30, 60, 5]

# Function to create a new dataframe with averages over specified seconds
def average_over_seconds(df, seconds):
    rows_per_avg = int(seconds / 5)  # Assuming each row is a 5-second interval
    averaged_df = df.groupby(df.index // rows_per_avg).mean()
    return averaged_df

def average_over_seconds_v2(df, seconds):
    rows_per_avg = int(seconds / 5)  # Assuming each row is a 5-second interval
        
    averaged_dfs = []
    for i in range(0, len(df), rows_per_avg):
        group_df = df.iloc[i:i+rows_per_avg, :]
        averaged_df = group_df.mean(axis=0)
        averaged_dfs.append(averaged_df)

    result_df = pd.concat(averaged_dfs, axis=1).transpose()
    return result_df

def transform_folder_structure(path):
    # Move each CSV file into its respective folder
    csv_files = [file for file in os.listdir(path) if file.endswith('_data.csv')]

    for file in csv_files:
        file_number = file.split('_')[0]
        src = os.path.join(path, file)
        
        for time_window in TIME_WINDOWS:            
            dst_folder = os.path.join(path, f'time_window_{time_window}', file_number)
            dst = os.path.join(dst_folder, 'data.csv')
            # Create subfolder for each CSV file and move it
            os.makedirs(dst_folder, exist_ok=True)
            
            if time_window != 5:
                df = pd.read_csv(src)
                df.index = range(1, len(df) + 1)
                df_new = average_over_seconds_v2(df, time_window)
                df_new.to_csv(dst, index=False)
            else:
                shutil.move(src, dst)


def perform_time_analysis():
       # Get the list of targets (subfolders in the main directory)
    targets = [target for target in os.listdir(DATA_FOLDER) if os.path.isdir(os.path.join(DATA_FOLDER, target))]

    for target in targets:
        # Can be front-end, orders and normal
        target_directory = os.path.join(DATA_FOLDER, target)
        stress_factors = [folder for folder in os.listdir(target_directory) if os.path.isdir(os.path.join(target_directory, folder))]

        if 'load_50' not in stress_factors:
            #target is normal
            user_factors = [folder for folder in os.listdir(target_directory) if os.path.isdir(os.path.join(target_directory, folder))]
            for user in user_factors:            
                scenario_factors = [folder for folder in os.listdir(os.path.join(target_directory, user)) if os.path.isdir(os.path.join(target_directory, user, folder))]
                for scenario in scenario_factors:
                    print(f'{DATA_FOLDER}\\{target}\\{user}\\{scenario}')
                    path  = f'{DATA_FOLDER}\\{target}\\{user}\\{scenario}'
                    transform_folder_structure(path)
                    
        else:        
            for stress in stress_factors:            
                user_factors = [folder for folder in os.listdir(os.path.join(target_directory, stress)) if os.path.isdir(os.path.join(target_directory, stress, folder))]
                for user in user_factors:                
                    scenario_factors = [folder for folder in os.listdir(os.path.join(target_directory, stress, user)) if os.path.isdir(os.path.join(target_directory, stress, user, folder))]
                    for scenario in scenario_factors:
                        print(f'{DATA_FOLDER}\\{target}\\{stress}\\{user}\\{scenario}')
                        path  = f'{DATA_FOLDER}\\{target}\\{stress}\\{user}\\{scenario}'
                        transform_folder_structure(path)

                        
def print_info(text: str) -> None:
    print(f"\033[94m{text}\033[0m")


def unix_time_to_datetime(unix_time):
    unix_timestamp = float(unix_time)  # Convert string to float
    return datetime.utcfromtimestamp(unix_timestamp)

def create_dir_if_not_exists(path: str) -> str:
    if not os.path.exists(path):
        os.makedirs(path)

    return path


# Function to calculate energy using the trapezoid method
def calculate_energy_consumption_trapezoid(power_values, interval):
    energy = [0]  # Initialize energy list with 0 for the initial time point
    for i in range(1, len(power_values)):
        # Calculate energy for each interval using trapezoidal rule
        energy_in_interval = 0.5 * (power_values[i - 1] + power_values[i]) * interval
        total_energy = energy[-1] + energy_in_interval
        energy.append(total_energy)
    return energy


def calculate_energy_consumption(
    time_intervals,
    power_watts,
):
    time_intervals_seconds = np.array(time_intervals)
    power_watts = np.array(power_watts)
    
    if time_intervals_seconds[0] == 60:
        print(1)
        
    # Calculate energy consumption for each time interval
    energy_joules = power_watts * time_intervals_seconds

    return energy_joules
   

def convert_to_energy_and_cpu_percentage(
    file_path: str,
    energy_path: str,
    result: str,
    service: str,
    metric: Union[str, None] = None,
) -> None:
    print_info(
        f"Processing file {result} for service {service}{f' and metric {metric}' if metric else ''}..."
    )
    # Read the CSV file and parse the 'time' column while converting Unix timestamps
    result_df = pd.read_csv(file_path, parse_dates=["time"], date_parser=unix_time_to_datetime)

    # Additional processing remains the same
    temp_df = pd.read_csv(file_path)
    temp_df["date_time"] = temp_df["time"].astype(float).apply(unix_time_to_datetime)

    time_intervals = temp_df["date_time"].diff().dt.total_seconds()
    time_intervals.fillna(method="bfill", inplace=True)
    time_interval = time_intervals[0]
    
    for col in result_df.columns:
        if col.endswith("_power"):
            # temp_df.drop(col, axis=1, inplace=True)
            new_col_name = f"{col.split('_')[0]}_energy"
            power = result_df[col]
            energy = calculate_energy_consumption(
                time_intervals,
                power,
            )
            temp_df[new_col_name] = energy
        if col.endswith("_cpu"):
            # temp_df.drop(col, axis=1, inplace=True)
            # new_col_name = f"{col.split('_')[0]}_cpu_percent"
            temp_df[col] = result_df[col] * 100

    temp_df.drop("date_time", axis=1, inplace=True)
    # Remove disk data due to the existing bug in Cadvisor
    columns_to_drop = [col for col in temp_df.columns if '_disk' in col]
    temp_df.drop(columns=columns_to_drop, inplace=True)
    
    temp_df.to_csv(f"{energy_path}/{result.split('.')[0]}.csv", index=False)
    
def power_to_energy_and_cpu_to_percentage() -> None:
    print("Converting power metrics to energy metrics...")

    for service in os.listdir(DATA_FOLDER):
        service_path = os.path.join(DATA_FOLDER, service)
        if not os.path.isdir(service_path):
            continue

        if service == "normal":            
            user_factors = [folder for folder in os.listdir(service_path) if os.path.isdir(os.path.join(service_path, folder))]
            for user in user_factors:            
                scenario_factors = [folder for folder in os.listdir(os.path.join(service_path, user)) if os.path.isdir(os.path.join(service_path, user, folder))]
                for scenario in scenario_factors:
                    scenario_path = os.path.join(service_path, user, scenario)
                    for file in os.listdir(scenario_path):
                        if file.endswith(".csv"):
                            convert_to_energy_and_cpu_percentage(
                                os.path.join(scenario_path, file), scenario_path, file, service
                            )
        else:          
            stress_factors = [folder for folder in os.listdir(service_path) if os.path.isdir(os.path.join(service_path, folder))]
            for stress in stress_factors:            
                user_factors = [folder for folder in os.listdir(os.path.join(service_path, stress)) if os.path.isdir(os.path.join(service_path, stress, folder))]
                for user in user_factors:            
                    scenario_factors = [folder for folder in os.listdir(os.path.join(service_path, stress, user)) if os.path.isdir(os.path.join(service_path, stress, user, folder))]
                    for scenario in scenario_factors:     
                        scenario_path = os.path.join(service_path, stress, user, scenario)
                        for file in os.listdir(scenario_path):
                            if file.endswith(".csv"):
                                convert_to_energy_and_cpu_percentage(
                                    os.path.join(scenario_path, file), scenario_path, file, service
                                )

def create_combined_df(dfs, stress, user, scenario, time_window):
    
    # Concatenate all the DataFrames into a single DataFrame
    normal_df = pd.concat(dfs, ignore_index=True)
    # Drop _disk columns due to existing Cadvisor bug
    columns_to_drop = [col for col in normal_df.columns if '_disk' in col]
    normal_df.drop(columns=columns_to_drop, inplace=True)
    
    time_window_combined_path = os.path.join(TRAINING_DATA_FOLDER, time_window)
    os.makedirs(time_window_combined_path, exist_ok=True)

    
    combined_csv = os.path.join(time_window_combined_path,  f'{stress}_{user}_{scenario}_normal_combined.csv')

    # Store the combined data in a new CSV file
    normal_df.to_csv(combined_csv, index=False)
    
    return normal_df
          
def combine_normal_operations_and_train_AD_models() -> None:
    """
    This function combines all the CSV files in the data/normal folder into a single CSV file.
    The combined file is stored in data/normal/normal_combined.csv.
    The combined file is also stored in the current working directory.

    The function returns nothing.
    """
    user_factors = [folder for folder in os.listdir(NORMAL_DATA_PATH) if os.path.isdir(os.path.join(NORMAL_DATA_PATH, folder))]
    for user in user_factors:        
        scenario_factors = [folder for folder in os.listdir(os.path.join(NORMAL_DATA_PATH, user)) if os.path.isdir(os.path.join(NORMAL_DATA_PATH, user, folder))]
        for scenario in scenario_factors:
            time_windows = [folder for folder in os.listdir(os.path.join(NORMAL_DATA_PATH, user, scenario)) if os.path.isdir(os.path.join(NORMAL_DATA_PATH, user, scenario, folder))]
            for time_window in time_windows:            
                # Initialize an empty list to store DataFrames
                dfs = []            
                trials = [folder for folder in os.listdir(os.path.join(NORMAL_DATA_PATH, user, scenario, time_window)) if os.path.isdir(os.path.join(NORMAL_DATA_PATH, user, scenario, time_window, folder))]
                for trial in trials:            
                    trial_path = os.path.join(NORMAL_DATA_PATH, user, scenario, time_window, trial)
                    # Iterate over all the files in the folder
                    for filename in os.listdir(trial_path):
                        if not filename.endswith(".csv"):
                            continue
                        if "combined" in filename:
                            continue
                        if not "data" in filename:
                            continue

                        # Ensure we only process CSV files, adjust the extension if necessary
                        file_path = os.path.join(trial_path, filename)
                        # Read the file data and append it to the list
                        df = pd.read_csv(file_path)
                        dfs.append(df)

                normal_df = create_combined_df(dfs, 'load_0', user, scenario, time_window)
                train_LSTM_AD_model(normal_df, user, scenario, time_window)
                train_pycaret_AD_models(normal_df, user, scenario, time_window)
            
def train_pycaret_AD_models(train_df, user, scenario, time_window):
    models_dir = create_dir_if_not_exists(
            os.path.join(AD_FOLDER, "anomaly_detection_models")
        )

    train_df.replace(0, np.nan, inplace=True)
    train_df["time"] = pd.to_datetime(train_df["time"], unit="s")
    
    # For each type of AD model to be used, create and train a model instance on the normal data
    for model in AD_MODELS:
        for column in train_df.columns:
            if "time" in column or "_energy" not in column:
                continue 
            print("Training anomaly detection models on normal data...")
            print(f"Training {model} model for {user}-{scenario} factors...")
            
            # Train model on Time & Energy dataframe
            col_data = train_df.loc[:, ["time", column]]
            setup(col_data, session_id = 123)
            
            # Train the model
            trained_model = create_model(model)
            
            resource_dir = create_dir_if_not_exists(
                os.path.join(models_dir, SYSTEM, time_window, f'{user}_{scenario}_{column}')
            )
            # Save the model
            save_model(
                trained_model,
                f"{resource_dir}/{model}_pipeline",
            )
  
# define the autoencoder network model
def autoencoder_model(X):
    inputs = Input(shape=(X.shape[1], X.shape[2]))
    L1 = LSTM(128, activation='relu', return_sequences=True, 
              kernel_regularizer=regularizers.l2(0.00))(inputs)
    L2 = LSTM(64, activation='relu', return_sequences=False)(L1)
    L3 = RepeatVector(X.shape[1])(L2)
    L4 = LSTM(64, activation='relu', return_sequences=True)(L3)
    L5 = LSTM(128, activation='relu', return_sequences=True)(L4)
    output = TimeDistributed(Dense(X.shape[2]))(L5)    
    model = Model(inputs=inputs, outputs=output)
    return model

def train_LSTM_AD_model(df, user, scenario, time_window):
        
    models_dir = create_dir_if_not_exists(
            os.path.join(AD_FOLDER, "anomaly_detection_models")
        )
    df.replace(0, np.nan, inplace=True)
    # df["time"] = pd.to_datetime(df["time"], unit="s")
    # df['time'] = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S.%f')

    # For each type of AD model to be used, create and train a model instance on the normal data
    for column in df.columns:
        if "time" in column or "_energy" not in column:
            continue
        print("Training anomaly detection models on normal data...")
        
        # Train model on Time & Energy dataframe
        train_df = df.loc[:, ["time", column]]
        
        #LSTM STARTS HERE
        # normalize the data
        scaler = StandardScaler()
        X_train = scaler.fit_transform(train_df)
        
        # reshape inputs for LSTM [samples, timesteps, features]
        X_train = X_train.reshape(X_train.shape[0], 1, X_train.shape[1])
        print("Training data shape:", X_train.shape)
        
        # create the autoencoder model
        model = autoencoder_model(X_train)
        model.compile(optimizer='adam', loss='mae')
        model.summary()
        
        # fit the model to the data
        nb_epochs = 100
        batch_size = 10
        model.fit(X_train, X_train, epochs=nb_epochs, batch_size=batch_size,
                            validation_split=0.05)
        

        # plot the loss distribution of the training set
        X_pred = model.predict(X_train)
        X_pred = X_pred.reshape(X_pred.shape[0], X_pred.shape[2])
        X_pred = pd.DataFrame(X_pred, columns=train_df.columns)
        X_pred.index = train_df.index
        
        resource_dir = create_dir_if_not_exists(
            os.path.join(models_dir, SYSTEM, time_window, f'{user}_{scenario}_{column}')
        )
        model.save(f'{resource_dir}/lstm.h5')

def run_BIRCH_AD_with_smoothing(temp_df, df, column):    
    ad_threshold = 0.045  
    smoothing_window = 12
    test_df = df.loc[:, ["time", column]]            

    for svc, energy in test_df.items():
        if svc != 'time':
            energy = energy.rolling(window=smoothing_window, min_periods=1).mean()
            x = np.array(energy)
            x = np.where(np.isnan(x), 0, x)
            normalized_x = preprocessing.normalize([x])

            X = normalized_x.reshape(-1,1)

            birch = Birch(branching_factor=50, n_clusters=None, threshold=ad_threshold, compute_labels=True)
            birch.fit(X)
            birch.predict(X)

            # Calculate distances to cluster centers
            distances = distance.cdist(X, birch.subcluster_centers_)
            min_distances = np.min(distances, axis=1)

            # Set threshold to identify anomalies
            threshold = np.percentile(min_distances, 95)

            # Assign anomaly labels
            test_df['anomaly_label'] = np.where(min_distances > threshold, 1, 0)
            
            temp_df = temp_df.assign(
                **{
                    f"{column}_Anomaly": test_df['anomaly_label'],
                    f"{column}_Anomaly_Score": min_distances,
                }
            )   
    return temp_df

def create_ground_truth() -> None:
    """
    Indicates which of the data in each collected <metrics>.csv file are considered an anomaly
    based on the threshold value.

    The function returns nothing.
    """
    list_of_means = []
    list_of_sds = []
    for time_window in os.listdir(TRAINING_DATA_FOLDER):
        time_window_path = os.path.join(TRAINING_DATA_FOLDER, time_window)
        
        for service_path in os.listdir(time_window_path):
            df_path = os.path.join(time_window_path, service_path)
            if os.path.isdir(df_path):
                continue
            df = pd.read_csv(df_path)  # Reading CSV into a DataFrame
            mean_values = df.mean()  # Calculating means
            std_values = df.std()    # Calculating standard deviations

            list_of_means.append({df_path: mean_values})  # Adding means with a specific name as a dictionary key
            list_of_sds.append({df_path: std_values})     # Adding standard deviations with a specific name as a dictionary key
            
    for service in os.listdir(DATA_FOLDER):
        service_path = os.path.join(DATA_FOLDER, service)
        if not os.path.isdir(service_path):
            continue
        if service == "normal":
            continue
                  
        stress_factors = [folder for folder in os.listdir(service_path) if os.path.isdir(os.path.join(service_path, folder))]
        for stress in stress_factors:            
            user_factors = [folder for folder in os.listdir(os.path.join(service_path, stress)) if os.path.isdir(os.path.join(service_path, stress, folder))]
            for user in user_factors:            
                scenario_factors = [folder for folder in os.listdir(os.path.join(service_path, stress, user)) if os.path.isdir(os.path.join(service_path, stress, user, folder))]
                for scenario in scenario_factors:
                    time_windows = [folder for folder in os.listdir(os.path.join(service_path, stress, user, scenario)) if os.path.isdir(os.path.join(service_path, stress, user, scenario, folder))]
                    for time_window in time_windows:            
                        trials = [folder for folder in os.listdir(os.path.join(service_path, stress, user, scenario, time_window)) if os.path.isdir(os.path.join(service_path, stress, user, scenario, time_window, folder))]
                        for trial in trials:            
                            trial_path = os.path.join(service_path, stress, user, scenario, time_window, trial)
                            for file in os.listdir(trial_path):                         
                                ground_truth_metrics_path = (
                                    f"{trial_path}/data_gt.csv"
                                )
                                if not "data.csv" in file:
                                    continue
                                if os.path.exists(ground_truth_metrics_path):
                                    continue 
                                try:
                                    file_path = os.path.join(trial_path,file)
                                    file_df = pd.read_csv(file_path)
                                    temp_df = pd.read_csv(file_path)
                                except Exception as e:
                                    print(e)
                                    continue

                                try:
                                    # Create a column to store the anomaly indicator
                                    for column in file_df.columns:
                                        if column == "time" or "_energy" not in column:
                                            continue
                                        for index, value in temp_df[column].items():
                                            # print(metrics_means[column], value)
                                            # Retrieval of DataFrames filtered by user and scenario
                                                                                                   
                                            metrics_means = [d[name] for d in list_of_means for name in d if user in name and scenario in name and time_window in name]
                                            metrics_sds = [d[name] for d in list_of_sds for name in d if user in name and scenario in name and time_window in name]
                                            mean_value = metrics_means[0][column]
                                            std_value = metrics_sds[0][column]
                                            if abs(mean_value - value) >= mean_value * std_value:
                                                temp_df.at[index, f"{column}_Anomaly"] = 1
                                            else:
                                                temp_df.at[index, f"{column}_Anomaly"] = 0
                                            temp_df.to_csv(f"{ground_truth_metrics_path}", index=False)
                                            print(f"Ground truth saved at: {ground_truth_metrics_path}")
                                except Exception as e:
                                    print("Error creating ground truth metrics:", e)
                                    continue

def execute_AD_models():
    print("Start executing AD models")
    for service in os.listdir(DATA_FOLDER):
        service_path = os.path.join(DATA_FOLDER, service)
        if not os.path.isdir(service_path):
            continue
        if service == "normal":
            continue
                  
        stress_factors = [folder for folder in os.listdir(service_path) if os.path.isdir(os.path.join(service_path, folder))]
        for stress in stress_factors:            
            user_factors = [folder for folder in os.listdir(os.path.join(service_path, stress)) if os.path.isdir(os.path.join(service_path, stress, folder))]
            for user in user_factors:            
                scenario_factors = [folder for folder in os.listdir(os.path.join(service_path, stress, user)) if os.path.isdir(os.path.join(service_path, stress, user, folder))]
                for scenario in scenario_factors:
                    time_windows = [folder for folder in os.listdir(os.path.join(service_path, stress, user, scenario)) if os.path.isdir(os.path.join(service_path, stress, user, scenario, folder))]
                    for time_window in time_windows:            
                        trials = [folder for folder in os.listdir(os.path.join(service_path, stress, user, scenario, time_window)) if os.path.isdir(os.path.join(service_path, stress, user, scenario, time_window, folder))]
                        for trial in trials:            
                            trial_path = os.path.join(service_path, stress, user, scenario, time_window, trial)
                            for file in os.listdir(trial_path):  
                                if not "data.csv" in file:
                                    continue
                                file_path = os.path.join(trial_path,file)
                                df = pd.read_csv(file_path)
                                temp_df = pd.read_csv(file_path)
                                
                                for column in df.columns:
                                    if "time" in column or "_energy" not in column:
                                        continue
                                    print(f"Executing for {stress}, {user}, {scenario}, DATA_TW = {time_window}, {trial}, {column}")
                                    # Run BIRCH algorithm
                                    birch_results = run_BIRCH_AD_with_smoothing(temp_df, df, column)
                                    model_result_path = os.path.join(trial_path, 'birch_results.csv')
                                    birch_results.to_csv(model_result_path, index=False)
                                    # Run the previously trained algorithms
                                    for model_folder in os.listdir(os.path.join(LOCAL_AD_MODELS, time_window)):
                                        train_model_column = f'{user}_{scenario}_{column}'
                                        if model_folder != train_model_column:
                                            continue
                                        for ad_model in os.listdir(os.path.join(LOCAL_AD_MODELS, time_window, model_folder)):
                                            print(f"Executing for {stress}, {user}, {scenario}, DATA_TW = {time_window}, {trial}, {ad_model}, {column}, Train Model = {model_folder}")

                                            # Run LSTM algorithm
                                            if 'lstm' in ad_model:
                                                model_path = os.path.join(LOCAL_AD_MODELS, time_window, model_folder, ad_model)
                                                model = tf.keras.models.load_model(model_path)
                                                scaler = StandardScaler()
                                                test_df = df.loc[:, ["time", column]]            
                                                X_test = scaler.fit_transform(test_df)
                                                X_test = X_test.reshape(X_test.shape[0], 1, X_test.shape[1])

                                                # calculate the loss on the test set
                                                X_pred = model.predict(X_test)
                                                X_pred = X_pred.reshape(X_pred.shape[0], X_pred.shape[2])
                                                X_pred = pd.DataFrame(X_pred, columns=test_df.columns)
                                                X_pred.index = test_df.index

                                                anomaly_results = pd.DataFrame(index=test_df.index)
                                                Xtest = X_test.reshape(X_test.shape[0], X_test.shape[2])
                                                anomaly_results['Loss_mae'] = np.mean(np.abs(X_pred - Xtest), axis = 1)
                                                THRESHOLD = np.percentile(anomaly_results['Loss_mae'], 95)
                                                anomaly_results['Threshold'] = THRESHOLD
                                                anomaly_results['Anomaly'] = (anomaly_results['Loss_mae'] > anomaly_results['Threshold']).astype(int)
                                                
                                                temp_df = temp_df.assign(
                                                    **{
                                                        f"{column}_Anomaly": anomaly_results["Anomaly"],
                                                        f"{column}_Anomaly_Score": anomaly_results["Loss_mae"],
                                                    }
                                                )   
                                                model_result_path = os.path.join(trial_path, 'lstm_results.csv')                                                    
                                            else:   
                                                # Run SVM, KNN and iForest algorithms
                                                setup(df, session_id = 123, verbose = False)
                                                model_path = os.path.join(LOCAL_AD_MODELS, time_window, model_folder,f"{ad_model.split('_')[0]}_pipeline")
                                                trained_model = load_model(model_path, verbose = False)
                                                df.reset_index(drop=True, inplace=True)
                                                col_df = df.loc[:, ["time", column]]
                                                
                                                col_df.replace(0, np.nan, inplace=True)
                                                col_df["time"] = pd.to_datetime(col_df["time"], unit="s")
                                                anomaly_results = predict_model(trained_model, data = col_df)
                                                
                                                temp_df = temp_df.assign(
                                                    **{
                                                        f"{column}_Anomaly": anomaly_results["Anomaly"],
                                                        f"{column}_Anomaly_Score": anomaly_results["Anomaly_Score"],
                                                    }
                                                )   
                                                model_result_path = os.path.join(trial_path, f"{ad_model.split('_')[0]}_results.csv")
                                            temp_df.to_csv(model_result_path, index=False)
                                        
              
def get_folder_names(directory):
  folder_names = [folder for folder in os.listdir(directory) if os.path.isdir(os.path.join(directory, folder))]
  return folder_names
           
if __name__ == '__main__':    
    power_to_energy_and_cpu_to_percentage()

    perform_time_analysis()                             

    # Create model training dataset from the normal experiment folder
    combine_normal_operations_and_train_AD_models() 

    # Create the Ground Truth
    create_ground_truth()

    # Execute AD algos
    execute_AD_models()