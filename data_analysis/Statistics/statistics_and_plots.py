
from functools import reduce
import os
from matplotlib import pyplot as plt
import pandas as pd
from typing import Union, Tuple, List, Dict
import csv
import numpy as np

SMALL_SIZE = 14
MEDIUM_SIZE = 16
BIGGER_SIZE = 18

plt.rc('font', size=MEDIUM_SIZE)          # controls default text sizes
plt.rc('axes', titlesize=MEDIUM_SIZE)     # fontsize of the axes title
plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
plt.rc('xtick', labelsize=BIGGER_SIZE)    # fontsize of the tick labels
plt.rc('ytick', labelsize=BIGGER_SIZE)    # fontsize of the tick labels
plt.rc('legend', fontsize=MEDIUM_SIZE)    # legend fontsize
plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

# SYSTEM = 'sockshop'
SYSTEM = 'unicloud'
DATA_FOLDER = os.path.join(f"C:\scul\Thesis\Experiment Results\{SYSTEM}-data")
RESULTS_FOLDER = "statistics.csv"
# RESULTS_FOLDER = f'C:\scul\Thesis\Experiment Results\{SYSTEM}-data'

AD_MODELS = ["birch", "iforest", "knn", "svm", "lstm" ]
RCA_MODELS = ["MicroRCA", "epsilon", "rcd"]

TIME_WINDOWS = ['5', '10', '30','60' ]
AD_METRICS = ['Precision', 'Recall', 'F-Score']
RCA_METRICS = ['level_1', 'level_2', 'level_3']


SOCKSHOP_SERVICES = ['front-end', 'orders', 'carts', 'shipping', 'catalogue', 'payment', 'user']
UNICLOUD_SERVICES = ['geospatialanalysisservice', 'surveyservice', 'transformation-worker', 'transformation-consumer', 'unicloudauth']
SYSTEM_SERVICES = {'sockshop' : SOCKSHOP_SERVICES, 'unicloud' : UNICLOUD_SERVICES}

DESCRIPTIVE_STATISTICS_FOLDER = os.path.join(f"C:\scul\Thesis\Experiment Results\Descriptive statistics")
PLOTS_FOLDER = os.path.join(f"C:\scul\Thesis\Experiment Results")

def print_info(text):
  print(f"\033[94m{text}\033[0m")

# retrieve the all folder names within specified directory
def get_folder_names(directory):
  folder_names = [folder for folder in os.listdir(directory) if os.path.isdir(os.path.join(directory, folder))]
  return folder_names
  
# This only retrieves the gt ranges for Energy Anomalies 
def get_energy_anomaly_gt_ranges(gt_file):
  gt_df = pd.read_csv(gt_file)
  gt_energy_metrics = {}
  gt_energy_metrics["normal_segments"] = {}
  gt_energy_metrics["anomalous_segments"] = {}

  for col in gt_df.columns:
    if not col.endswith("_energy_Anomaly"):
      continue
    gt_energy_metrics["normal_segments"][col] = []
    gt_energy_metrics["anomalous_segments"][col] = []

    normal_start = None
    anomalous_start = None

    for index, value in gt_df[col].items():
      if value == 0:  # value of 0 indicates normal data point
        if normal_start is None:
          normal_start = index
        else:
          continue

        if anomalous_start != None:
          gt_energy_metrics["anomalous_segments"][col].append((anomalous_start, index - 1))
          anomalous_start = None

      if value == 1:  # value of 1 indicates anomalous data point
        if anomalous_start is None:
          anomalous_start = index
        else:
          continue

        if normal_start != None:
          gt_energy_metrics["normal_segments"][col].append((normal_start, index - 1))
          normal_start = None

    if normal_start != None:
      gt_energy_metrics["normal_segments"][col].append((normal_start, len(gt_df[col])))
    elif anomalous_start != None:
      gt_energy_metrics["anomalous_segments"][col].append((anomalous_start, len(gt_df[col])))

  return gt_energy_metrics

def generate_model_stats(results_path, gt_ranges, ad_results):
  # Create new directory if they do not exist
  directory = os.path.dirname(results_path)
  if not os.path.exists(directory):
      os.makedirs(directory)
  print(results_path)

  # Save data to a csv file
  with open(results_path, mode='w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    header = ["service_name", "true_positives", "false_positives", "false_negatives"]
    writer.writerow(header)

    for col in ad_results.columns:
      if not col.endswith("_Anomaly"):
        continue

      true_positives = 0
      false_positives = 0
      false_negatives = 0
      
      col_service = col.split("_")[0]
      gt_col = col_service + "_energy_Anomaly"
      
      
      ad_metric_col = ad_results[col]
      
      for normal_range in gt_ranges["normal_segments"][gt_col]:
        range_start = normal_range[0]
        range_end = normal_range[1] + 1
        ad_range_values = ad_metric_col[range_start:range_end]

        # if one value within the range is marked as an anomaly then we consider it as a false positive
        if not ad_range_values.all() == 0:
          false_positives += 1

      for anomalous_range in gt_ranges["anomalous_segments"][gt_col]:
        range_start = anomalous_range[0]
        range_end = anomalous_range [1] + 1
        ad_range_values = ad_metric_col[range_start:range_end]

        if ad_range_values.any() == 1:
          true_positives += 1
        else:
          false_negatives += 1

      data_row = [col, true_positives, false_positives, false_negatives]
      writer.writerow(data_row)


def calculate_precision(tp, fp):
  if (tp + fp) == 0:
    return 0
  return round(tp / (tp + fp),3)


def calculate_recall(tp, fn):
  if (tp + fn) == 0:
    return 0
  return round(tp / (tp + fn),3)


def calculate_fscore(precision, recall):
  if precision + recall == 0:
    return 0
  fscore = 2 * ((precision * recall) / (precision + recall))

  return round(fscore,3)


def generate_performance_metrics(results_folder):
  # Create new directory if they do not exist
  if not os.path.exists(results_folder):
      os.makedirs(results_folder)

  # Get a list of CSV file paths
  csv_files = [os.path.join(results_folder, file) for file in os.listdir(results_folder) if file.endswith('.csv')]
 
  for file in csv_files:
    if not 'statistics' in file:
      continue
    model = file.split('\\')[-1].split('_')[0] 
    if not model in AD_MODELS:
      continue
    df = pd.read_csv(file)
    for i in range(0,len(df)):
      df.loc[i,'precision'] = calculate_precision(df.loc[i,'true_positives'], df.loc[i,'false_positives'])
      df.loc[i,'recall'] = calculate_recall(df.loc[i,'true_positives'], df.loc[i,'false_negatives'])
      df.loc[i,'f1score'] = calculate_fscore(df.loc[i,'precision'], df.loc[i,'recall'])

    df.to_csv(file, index=False)
    

def get_stats_ad(trial_folder):
  
  for ad_model in AD_MODELS:
      ad_file = os.path.join(trial_folder, f'{ad_model}_results.csv')
      ad_results = pd.read_csv(ad_file)
      gt_ranges = get_energy_anomaly_gt_ranges(os.path.join(trial_folder, 'data_gt.csv'))
      results_file = os.path.join(trial_folder, f'{ad_model}_{RESULTS_FOLDER}')
      generate_model_stats(results_file, gt_ranges, ad_results)
  generate_performance_metrics(trial_folder)
  
    
def get_stats_rca(file, l: int, service) -> Tuple[int, int]:
    true_positives = 0
    false_positives = 0
        # A missing file means that no root-causes were considered #! As this is connected to AD it might not be correct
        # false_positives += NUM_TRIALS - len(os.listdir(model_folder))

    df = pd.read_csv(file)
    if l > df.size:
       true_positives +=1
       return true_positives, false_positives
     
    root_cause_identified = df.loc[l-1, 'Root Cause'].split('_')[0]
    if root_cause_identified == service:
        true_positives += 1
    else:
        false_positives += 1
    return true_positives, false_positives


def get_stats():
  # Anomaly detection
  services = get_folder_names(DATA_FOLDER)
  
  # remove "normal" folder as its not a service
  while 'normal' in services:
    services.remove("normal")

  for service in services:
    service_folder = os.path.join(DATA_FOLDER, service)
    stressors = get_folder_names(service_folder)

    for stressor in stressors:
      stressor_folder = os.path.join(service_folder, stressor)
      users = get_folder_names(stressor_folder)

      for user in users:
        user_folder = os.path.join(stressor_folder, user)
        scenarios = get_folder_names(user_folder)
        
        for scenario in scenarios:          
            scenario_folder = os.path.join(user_folder, scenario)
            time_windows = get_folder_names(scenario_folder)
            
            for time in time_windows:
              time_folder = os.path.join(scenario_folder, time)
              trials = get_folder_names(time_folder)
              
              for trial in trials:
                  trial_folder = os.path.join(time_folder, trial)
                  
                  get_stats_ad(trial_folder)
                  
                  for file in os.listdir(trial_folder):
                    if 'statistics' in file:
                      continue
                    if file.split('_')[0] not in RCA_MODELS:
                      continue
                    # Root Cause Anlysis 
                    rca_metrics = {}
                    k_levels = 3
                    true_positive_identified = False
                    for l in range(1,k_levels + 1):
                        rca_metrics[f"level_{l}"] = {}
                        if true_positive_identified == True:
                          true_positives_rca, false_positives_rca = 1, 0
                        else:
                          true_positives_rca, false_positives_rca = get_stats_rca(os.path.join(trial_folder, file), l, service)
                          true_positive_identified = True if true_positives_rca == 1 else False
                        
                        rca_metrics[f"level_{l}"]["true_positives"] = true_positives_rca
                        rca_metrics[f"level_{l}"]["false_positives"] = false_positives_rca

                        precision_rca = calculate_precision(true_positives_rca, false_positives_rca)
                        rca_metrics[f"level_{l}"]["precision"] = precision_rca

                    rca_metrics[f"average_at_{k_levels}"] = sum(
                        [stats["precision"] for level, stats in rca_metrics.items()]
                    ) / len(rca_metrics)

                    print_info(f"Statistic for Root-Cause Analysis at levels {k_levels}:")
                    print(rca_metrics)
                    result_file = f"{file.split('_')[0]}_statistics.csv"
                    
                    # Convert the structure to a suitable format for DataFrame
                    new_data = {}
                    for key, value in rca_metrics.items():
                        if isinstance(value, dict):
                            value['level'] = key  # Adding a 'level' key to the nested dict
                            new_data[key] = value

                    # Creating DataFrame from the modified structure
                    df = pd.DataFrame(new_data).T.reset_index(drop=True)

                    # Filtering out 'len()' and 'average_at_3' rows
                    df = df[~df['level'].isin(['len()', 'average_at_3'])]

                    df.to_csv(os.path.join(trial_folder, result_file))

def get_overall_AD_and_RCA_data(services, ad_stats, rca_stats):
  
    for service in services:
        service_folder = os.path.join(DATA_FOLDER, service)
        stressors = get_folder_names(service_folder)
        
        for stressor in stressors:
            stressor_folder = os.path.join(service_folder, stressor)
            users = get_folder_names(stressor_folder)
            
            for user in users:
              user_folder = os.path.join(stressor_folder, user)
              scenarios = get_folder_names(user_folder)
            
              for scenario in scenarios:                  
                scenario_folder = os.path.join(user_folder, scenario)
                time_windows = get_folder_names(scenario_folder)
                
                for time in time_windows:
                  
                  if not time in rca_stats:
                    rca_stats[time] = {}
                                        
                  if not time in ad_stats:
                    ad_stats[time] = {}
                    
                  time_folder = os.path.join(scenario_folder, time)
                  trials = get_folder_names(time_folder)

                  for trial in trials:           
                    trial_folder = os.path.join(time_folder, trial)
                    
                    for file in os.listdir(trial_folder):
                      if 'statistics' not in file:
                        continue
                      
                      model_df = pd.read_csv(os.path.join(trial_folder,file))
                      model = file.split('_')[0]
                      
                      # Anomaly detection
                      if model in AD_MODELS:  
                        if not stressor in ad_stats[time]:
                          ad_stats[time][model] = {}
                            
                        precision_series =  model_df['precision'].values
                        recall_series =  model_df['recall'].values
                        f1score_series =  model_df['f1score'].values                    
                            
                        if not "Precision" in ad_stats[time][model] :
                            ad_stats[time][model] ["Precision"] = precision_series
                        else:
                            existing_precision = ad_stats[time][model] ["Precision"]
                            ad_stats[time][model] ["Precision"] = np.concatenate((existing_precision, precision_series), axis = None)
                                                  
                        if not "Recall" in ad_stats[time][model] :                    
                            ad_stats[time][model] ["Recall"] = recall_series
                        else:
                            existing_recall = ad_stats[time][model] ["Recall"]
                            ad_stats[time][model] ["Recall"] = np.concatenate((existing_recall, recall_series), axis = None)
                            
                        if not "F-Score" in ad_stats[time][model] :
                            ad_stats[time][model] ["F-Score"] = f1score_series
                        else:
                            existing_f1score = ad_stats[time][model] ["F-Score"]
                            ad_stats[time][model] ["F-Score"] = np.concatenate((existing_f1score, f1score_series), axis = None)
                      else:                    
                      # Root Cause Analysis                                        
                        if not model in rca_stats[time]:
                            rca_stats[time][model] = {}
                            
                        precision_at_1 = model_df.loc[model_df['level'] == 'level_1', 'precision'].values[0]
                        precision_at_2 = model_df.loc[model_df['level'] == 'level_2', 'precision'].values[0]
                        precision_at_3 = model_df.loc[model_df['level'] == 'level_3', 'precision'].values[0]

                        if not "level_1" in rca_stats[time][model]:
                          rca_stats[time][model]["level_1"] = precision_at_1 
                        else:
                          existing_precision = rca_stats[time][model]["level_1"]
                          rca_stats[time][model]["level_1"] = np.concatenate((existing_precision, precision_at_1), axis = None)                      
                        
                        if not "level_2" in rca_stats[time][model]:
                          rca_stats[time][model]["level_2"] = precision_at_2 
                        else:
                          existing_precision = rca_stats[time][model]["level_2"]
                          rca_stats[time][model]["level_2"] = np.concatenate((existing_precision, precision_at_2), axis = None)
                        if not "level_3" in rca_stats[time][model]:
                          rca_stats[time][model]["level_3"] = precision_at_3 
                        else:
                          existing_precision = rca_stats[time][model]["level_3"]
                          rca_stats[time][model]["level_3"] = np.concatenate((existing_precision, precision_at_3), axis = None)  
    return ad_stats, rca_stats
  
def get_overall_stats_per_time_window():
  ad_stats = {}
  rca_stats = {}
  services = get_folder_names(DATA_FOLDER)
  # remove "normal" folder as its not a service
  while 'normal' in services:
    services.remove("normal")
  ad_stats, rca_stats = get_overall_AD_and_RCA_data(services, ad_stats, rca_stats)
  ad_violin_plots(ad_stats)
  rca_violin_plots(rca_stats)
  ad_CDF_plots(ad_stats)
  rca_CDF_plots(rca_stats)
  
  for time, model_dict in ad_stats.items():
      data_list = []
      for model, values in model_dict.items():
        data_list = export_ad_table(model, values, data_list)
          
      # Create a DataFrame
      df = pd.DataFrame(data_list)

      # Export to CSV
      ad_folder = os.path.join(DESCRIPTIVE_STATISTICS_FOLDER, SYSTEM, 'AD')
      os.makedirs(ad_folder, exist_ok=True)
      file_name = f'{SYSTEM}_OVERALL_{time}.csv'
      path = os.path.join(ad_folder, file_name)
      df.to_csv(path, index=False)         
      
  for time, model_dict in rca_stats.items():
      data_list = []
      for model, values in model_dict.items():
        data_list = export_rca_table(model, values, data_list)
          
      # Create a DataFrame
      df = pd.DataFrame(data_list)

      # Export to CSV
      rca_folder = os.path.join(DESCRIPTIVE_STATISTICS_FOLDER, SYSTEM, 'RCA')
      os.makedirs(rca_folder, exist_ok=True)
      file_name = f'{SYSTEM}_OVERALL_{time}.csv'
      path = os.path.join(rca_folder, file_name)
      df.to_csv(path, index=False)         
       


def export_ad_table(model, values, data_list):
  precision = values["Precision"]
  recall = values["Recall"]
  fscore = values["F-Score"]
                  
  precision = {
      'Algorithm': model,
      'Metric': 'Precision',
      'Min': np.min(precision),
      'Max': np.max(precision),
      'Median': round(np.median(precision), 3),
      'Mean': round(np.mean(precision), 3),
      'SD': round(np.std(precision), 3),
      'CV': round(np.cov(precision, rowvar=False).item(0), 3),
    }

  recall = {
      'Algorithm': model,
      'Metric': 'Recall',
      'Min': np.min(recall),
      'Max': np.max(recall),
      'Median': round(np.median(recall), 3),
      'Mean': round(np.mean(recall), 3),
      'SD': round(np.std(recall), 3),
      'CV': round(np.cov(recall, rowvar=False).item(0), 3),
  }

  fscore = {
      'Algorithm': model,
      'Metric': 'F-Score',
      'Min': np.min(fscore),
      'Max': np.max(fscore),
      'Median': round(np.median(fscore), 3),
      'Mean': round(np.mean(fscore), 3),
      'SD': round(np.std(fscore), 3),
      'CV': round(np.cov(fscore, rowvar=False).item(0), 3),
  }

  data_list.extend([precision, recall, fscore])
  return data_list
    
def export_rca_table(model, values, data_list):
  precision_level_1 = values["level_1"]
  precision_level_2 = values["level_2"]
  precision_level_3 = values["level_3"]
                
  average_precision_level_1 = np.mean(precision_level_1)
  average_precision_level_2 = np.mean(precision_level_2)
  average_precision_level_3 = np.mean(precision_level_3)
  
  mAP = np.mean([average_precision_level_1, average_precision_level_2, average_precision_level_3])
  precision_level_1_stats = {
      'Algorithm': model,
      'Precision Level': 'Precision@1',
      'Min': np.min(precision_level_1),
      'Max': np.max(precision_level_1),
      'Median': round(np.median(precision_level_1), 3),
      'Mean': round(np.mean(precision_level_1), 3),
      'SD': round(np.std(precision_level_1), 3),
      'CV': round(np.cov(precision_level_1, rowvar=False).item(0), 3),
      'MAP': round(mAP, 3)
  }

  precision_level_2_stats = {
      'Algorithm': model,
      'Precision Level': 'Precision@2',
      'Min': np.min(precision_level_2),
      'Max': np.max(precision_level_2),
      'Median': round(np.median(precision_level_2), 3),
      'Mean': round(np.mean(precision_level_2), 3),
      'SD': round(np.std(precision_level_2), 3),
      'CV': round(np.cov(precision_level_2, rowvar=False).item(0), 3),
      'MAP': round(mAP, 3)
  }

  precision_level_3_stats = {
      'Algorithm': model,
      'Precision Level': 'Precision@3',
      'Min': np.min(precision_level_3),
      'Max': np.max(precision_level_3),
      'Median': round(np.median(precision_level_3), 3),
      'Mean': round(np.mean(precision_level_3), 3),
      'SD': round(np.std(precision_level_3), 3),
      'CV': round(np.cov(precision_level_3, rowvar=False).item(0), 3),
      'MAP': round(mAP, 3)
  }

  data_list.extend([precision_level_1_stats, precision_level_2_stats, precision_level_3_stats])

              
  return data_list

def get_AD_and_RCA_data_per_treatment(ad_stats, rca_stats, services):
  for service in services:
      if not service in rca_stats:
        rca_stats[service] = {}
        ad_stats[service] = {}
      service_folder = os.path.join(DATA_FOLDER, service)
      stressors = get_folder_names(service_folder)
      
      for stressor in stressors:
          if not stressor in rca_stats[service]:
            rca_stats[service][stressor] = {}
            ad_stats[service][stressor] = {}
          stressor_folder = os.path.join(service_folder, stressor)
          users = get_folder_names(stressor_folder)
          
          for user in users:
            if not stressor in rca_stats[service][stressor]:
              rca_stats[service][stressor][user] = {}
              ad_stats[service][stressor][user] = {}
            user_folder = os.path.join(stressor_folder, user)
            scenarios = get_folder_names(user_folder)
          
            for scenario in scenarios:
              if not scenario in rca_stats[service][stressor][user]:
                rca_stats[service][stressor][user][scenario] = {}
                ad_stats[service][stressor][user][scenario] = {}
                
              scenario_folder = os.path.join(user_folder, scenario)
              time_windows = get_folder_names(scenario_folder)
              
              for time in time_windows:
                if not time in rca_stats[service][stressor][user][scenario]:
                  rca_stats[service][stressor][user][scenario][time] = {}
                  ad_stats[service][stressor][user][scenario][time] = {}
                  
                time_folder = os.path.join(scenario_folder, time)
                trials = get_folder_names(time_folder)

                for trial in trials:           
                  trial_folder = os.path.join(time_folder, trial)
                  
                  for file in os.listdir(trial_folder):
                    if 'statistics' not in file:
                      continue
                    
                    model_df = pd.read_csv(os.path.join(trial_folder,file))
                    model = file.split('_')[0]
                    
                    # Anomaly detection
                    if model in AD_MODELS:        
                      if not model in ad_stats[service][stressor][user][scenario][time]:
                        ad_stats[service][stressor][user][scenario][time][model] = {}
                          
                      precision_series =  model_df['precision'].values
                      recall_series =  model_df['recall'].values
                      f1score_series =  model_df['f1score'].values                    
                          
                      if not "Precision" in ad_stats[service][stressor][user][scenario][time][model]:
                          ad_stats[service][stressor][user][scenario][time][model]["Precision"] = precision_series
                      else:
                          existing_precision = ad_stats[service][stressor][user][scenario][time][model]["Precision"]
                          ad_stats[service][stressor][user][scenario][time][model]["Precision"] = np.concatenate((existing_precision, precision_series), axis = None)
                                                
                      if not "Recall" in ad_stats[service][stressor][user][scenario][time][model]:                    
                          ad_stats[service][stressor][user][scenario][time][model]["Recall"] = recall_series
                      else:
                          existing_recall = ad_stats[service][stressor][user][scenario][time][model]["Recall"]
                          ad_stats[service][stressor][user][scenario][time][model]["Recall"] = np.concatenate((existing_recall, recall_series), axis = None)
                          
                      if not "F-Score" in ad_stats[service][stressor][user][scenario][time][model]:
                          ad_stats[service][stressor][user][scenario][time][model]["F-Score"] = f1score_series
                      else:
                          existing_f1score = ad_stats[service][stressor][user][scenario][time][model]["F-Score"]
                          ad_stats[service][stressor][user][scenario][time][model]["F-Score"] = np.concatenate((existing_f1score, f1score_series), axis = None)
                    else:                    
                    # Root Cause Analysis                                        
                      if not model in rca_stats[service][stressor][user][scenario][time]:
                          rca_stats[service][stressor][user][scenario][time][model] = {}
                          
                      precision_at_1 = model_df.loc[model_df['level'] == 'level_1', 'precision'].values[0]
                      precision_at_2 = model_df.loc[model_df['level'] == 'level_2', 'precision'].values[0]
                      precision_at_3 = model_df.loc[model_df['level'] == 'level_3', 'precision'].values[0]

                      if not "level_1" in rca_stats[service][stressor][user][scenario][time][model]:
                        rca_stats[service][stressor][user][scenario][time][model]["level_1"] = precision_at_1 
                      else:
                        existing_precision = rca_stats[service][stressor][user][scenario][time][model]["level_1"]
                        rca_stats[service][stressor][user][scenario][time][model]["level_1"] = np.concatenate((existing_precision, precision_at_1), axis = None)                      
                      
                      if not "level_2" in rca_stats[service][stressor][user][scenario][time][model]:
                        rca_stats[service][stressor][user][scenario][time][model]["level_2"] = precision_at_2 
                      else:
                        existing_precision = rca_stats[service][stressor][user][scenario][time][model]["level_2"]
                        rca_stats[service][stressor][user][scenario][time][model]["level_2"] = np.concatenate((existing_precision, precision_at_2), axis = None)
                      if not "level_3" in rca_stats[service][stressor][user][scenario][time][model]:
                        rca_stats[service][stressor][user][scenario][time][model]["level_3"] = precision_at_3 
                      else:
                        existing_precision = rca_stats[service][stressor][user][scenario][time][model]["level_3"]
                        rca_stats[service][stressor][user][scenario][time][model]["level_3"] = np.concatenate((existing_precision, precision_at_3), axis = None)
  return ad_stats, rca_stats

def export_RCA_metric_tables_by_treatment(rca_stats):
  for service, service_dict in rca_stats.items():
    for stress, stress_dict in service_dict.items():
      for user, user_dict in stress_dict.items():
        for scenario, scenario_dict in user_dict.items():
          for time, time_dict in scenario_dict.items():    
            data_list = []

            for model, values in time_dict.items():
              print(f"\n Service {service} Stress {stress} User {user} Scenario {scenario} Time {time} Model {model} \n")
              
              data_list = export_rca_table(model, values, data_list)

            # Create a DataFrame
            df = pd.DataFrame(data_list)

            # Export to CSV
            file_name = f'{service}_{stress}_{user}_{scenario}_{time}.csv'
            rca_folder = os.path.join(DESCRIPTIVE_STATISTICS_FOLDER, SYSTEM, 'RCA')
            os.makedirs(rca_folder, exist_ok=True)
            path = os.path.join(rca_folder, file_name)
            df.to_csv(path, index=False)
   
def export_AD_metric_tables_by_treatment(ad_stats):
  for service, service_dict in ad_stats.items():
    for stress, stress_dict in service_dict.items():
      for user, user_dict in stress_dict.items():
        for scenario, scenario_dict in user_dict.items():
          for time, time_dict in scenario_dict.items():    
            data_list = []

            for model, values in time_dict.items():
              print(f"\n Service {service} Stress {stress} User {user} Scenario {scenario} Time {time} Model {model} \n")
              
              data_list = export_ad_table(model, values, data_list)

            # Create a DataFrame
            df = pd.DataFrame(data_list)

            # Export to CSV
            ad_folder = os.path.join(DESCRIPTIVE_STATISTICS_FOLDER, SYSTEM, 'AD')
            os.makedirs(ad_folder, exist_ok=True)
            file_name = f'{service}_{stress}_{user}_{scenario}_{time}.csv'
            path = os.path.join(ad_folder, file_name)
            df.to_csv(path, index=False)
   
  
def get_stats_per_treatment():
    ad_stats = {}
    rca_stats = {}
    services = get_folder_names(DATA_FOLDER)
    # remove "normal" folder as its not a service
    while 'normal' in services:
      services.remove("normal")

    ad_stats, rca_stats = get_AD_and_RCA_data_per_treatment(ad_stats, rca_stats, services)
    export_RCA_metric_tables_by_treatment(rca_stats)
    export_AD_metric_tables_by_treatment(ad_stats)

def rca_CDF_plots(rca_stats):
  for metric in RCA_METRICS:
  # Create a single JPEG file with five subplots
    fig, axes = plt.subplots(nrows=1, ncols=len(RCA_MODELS), figsize=(20, 6))

    for i, model in enumerate(RCA_MODELS):
        for time in TIME_WINDOWS:
          model_precision_data = rca_stats[f'time_window_{time}'][model][metric]

          count, bins_count = np.histogram(model_precision_data, bins=10)
          pdf = count / sum(count)
          cdf = np.cumsum(pdf)
          
          # Plot with a specific color for each time window
          title_model = model
          if title_model == 'epsilon':
            title_model = 'e-diagnosis'
          axes[i].plot(bins_count[1:], cdf, label=f'Time Window {time}')                
          axes[i].set_title(f"{title_model} Precision@{metric.split('_')[1]}")
          axes[i].set_xlabel(f'Precision Values')
          axes[i].set_ylabel('Cumulative Distribution')
          axes[i].set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
          axes[i].set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])


        
    plt.subplots_adjust(wspace=0.3)  # You can adjust the value as needed
    plt.legend()
    
    directory = os.path.join(PLOTS_FOLDER, 'Plots', SYSTEM)
    os.makedirs(directory, exist_ok=True)

    file_name = os.path.join(directory, f"{SYSTEM}-RCA-Precision@{metric.split('_')[1]}_plots.pdf")
    plt.savefig(file_name)
    
  map_dict = {}
  
  for time, model_dict in rca_stats.items():
    if not time in map_dict:
      map_dict[time] = {}
      
      for model, values in model_dict.items():
        if not model in map_dict[time]:
          map_dict[time][model] = {}
          
        precision_level_1 = values["level_1"]
        precision_level_2 = values["level_2"]
        precision_level_3 = values["level_3"]
                
        average_precision_level_1 = np.mean(precision_level_1)
        average_precision_level_2 = np.mean(precision_level_2)
        average_precision_level_3 = np.mean(precision_level_3)
        
        MAP = np.mean([average_precision_level_1, average_precision_level_2, average_precision_level_3])
        map_dict[time][model]['MAP'] = MAP
  
  file_name = f'RCA-mAP.csv'
  rca_folder = os.path.join(DESCRIPTIVE_STATISTICS_FOLDER, SYSTEM, 'RCA')
  os.makedirs(rca_folder, exist_ok=True)
  path = os.path.join(rca_folder, file_name)
  # Write the dictionary to CSV
  with open(path, 'w', newline='') as csv_file:
    fieldnames = ['Time Window', 'Model', 'mAP']
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    
    # Write header
    writer.writeheader()
    for time_window, models in map_dict.items():
      for model in models:
          writer.writerow({
              'Time Window': time_window,
              'Model': model,
              'mAP': round(models[model]['MAP'], 3)
          })
        
  
  fig, axes = plt.subplots(nrows=1, ncols=len(RCA_MODELS), figsize=(20, 6))
  for i, model in enumerate(RCA_MODELS):
      for time in TIME_WINDOWS:
        model_precision_data = map_dict[f'time_window_{time}'][model]['MAP']

        count, bins_count = np.histogram(model_precision_data, bins=5)
        pdf = count / sum(count)
        cdf = np.cumsum(pdf)
        
        # Plot with a specific color for each time window
        title_model = model
        if title_model == 'epsilon':
          title_model = 'e-diagnosis'
        axes[i].plot(bins_count[1:], cdf, label=f'Time Window {time}')                
        axes[i].set_title(f"{title_model} mAP")
        axes[i].set_xlabel(f'Precision Values')
        axes[i].set_ylabel('Cumulative Distribution')
        axes[i].set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
      
  plt.subplots_adjust(wspace=0.3)  # You can adjust the value as needed
  plt.legend()
    
  directory = os.path.join(PLOTS_FOLDER, 'Plots', SYSTEM)
  os.makedirs(directory, exist_ok=True)

  file_name = os.path.join(directory, f"{SYSTEM}-RCA-MAP_plots.pdf")
  plt.savefig(file_name)
    
def ad_CDF_plots(ad_stats):
  for metric in AD_METRICS:
  # Create a single JPEG file with five subplots
    fig, axes = plt.subplots(nrows=1, ncols=len(AD_MODELS), figsize=(20, 6))

    for i, model in enumerate(AD_MODELS):
        for time in TIME_WINDOWS:          
          model_precision_data = ad_stats[f'time_window_{time}'][model][metric]
          
          count, bins_count = np.histogram(model_precision_data, bins=10)
          pdf = count / sum(count)
          cdf = np.cumsum(pdf)
          
          # Plot with a specific color for each time window
          axes[i].plot(bins_count[1:], cdf, label=f'Time Window {time}')                
          axes[i].set_title(f'{model} {metric}')
          axes[i].set_xlabel(f'{metric} Values')
          axes[i].set_ylabel('Cumulative Distribution')
          axes[i].set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1])
          axes[i].set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1])
        
    plt.subplots_adjust(wspace=0.3)  # You can adjust the value as needed
    plt.legend()
    plt.tight_layout()
    
    directory = os.path.join(PLOTS_FOLDER,'Plots', SYSTEM)
    os.makedirs(directory, exist_ok=True)

    file_name = os.path.join(directory, f'{SYSTEM}-AD-{metric}_plots.pdf')
    plt.savefig(file_name)
    
def ad_violin_plots(ad_stats):
    for metric in AD_METRICS:
        # Create a single JPEG file with five subplots
        fig, axes = plt.subplots(nrows=1, ncols=len(AD_MODELS), figsize=(20, 6))

        for i, model in enumerate(AD_MODELS):
            all_data = []
            labels = []
            for time in ['5', '10', '30', '60']:
                model_precision_data = ad_stats[f'time_window_{time}'][model][metric]
                all_data.append(model_precision_data)
                labels.append(time)

            # Plot violin plot
            axes[i].violinplot(all_data, showmeans=True, showextrema=False, showmedians=False)
            axes[i].set_title(f'{model} {metric}')
            axes[0].set_xlabel('Time windows')
            axes[0].set_ylabel('Precision Distribution')
            axes[i].set_xticks(range(1, len(labels) + 1))
            axes[i].set_xticklabels(labels)


        plt.subplots_adjust(wspace=0.3)  # You can adjust the value as needed
        plt.tight_layout()

        directory = os.path.join(PLOTS_FOLDER, 'Plots', SYSTEM)
        os.makedirs(directory, exist_ok=True)

        file_name = os.path.join(directory, f'{SYSTEM}-AD-{metric}_violin_plots.pdf')
        plt.savefig(file_name)
        plt.close()
def rca_violin_plots(rca_stats):
    for metric in RCA_METRICS:
        # Create a single JPEG file with five subplots
        fig, axes = plt.subplots(nrows=1, ncols=len(RCA_MODELS), figsize=(20, 6))

        for i, model in enumerate(RCA_MODELS):
            all_data = []
            labels = []
            for time in ['5', '10', '30', '60']:
                model_precision_data = rca_stats[f'time_window_{time}'][model][metric]
                all_data.append(model_precision_data)
                labels.append(time)

            # Plot violin plot with specified colors
            axes[i].violinplot(all_data, showmeans=True, showextrema=False, showmedians=False, widths=0.9)
            title_model = model
            if title_model == 'epsilon':
                title_model = 'e-diagnosis'
            axes[i].set_title(f"{title_model} Precision@{metric.split('_')[1]}")
            axes[0].set_xlabel('Time windows')
            axes[0].set_ylabel('Precision Distribution')
            axes[i].set_xticks(range(1, len(labels) + 1))
            axes[i].set_xticklabels(labels)

        plt.subplots_adjust(wspace=0.3)  # You can adjust the value as needed
        plt.tight_layout()

        directory = os.path.join(PLOTS_FOLDER, 'Plots', SYSTEM)
        os.makedirs(directory, exist_ok=True)

        file_name = os.path.join(directory, f"{SYSTEM}-RCA-Precision@{metric.split('_')[1]}_violin_plots.pdf")
        plt.savefig(file_name)

def get_metric_plots(df, metric, service, stress, user, scenario):  

  # Plotting the line chart
  fig, axes = plt.subplots(nrows=1, ncols=len(TIME_WINDOWS), figsize=(20, 6))
  fig.suptitle(f"{metric.capitalize()} Usage for Stress={service} {stress.split('_')[1]}%, User={user}, Scenario={scenario.split('_')[1]}")     

  for i, time in enumerate(TIME_WINDOWS):    
    for svc in SYSTEM_SERVICES[SYSTEM]:
      summed_df = reduce(lambda x, y: x.add(y, fill_value=0), df[f'time_window_{time}'])
      average_df = summed_df / len(df[f'time_window_{time}'])     
      
      average_df["time"] = average_df["time"].astype(float)
      average_df["duration"] = average_df["time"] - average_df["time"].iloc[0]
      
      time_values = average_df['duration']
      metric_values = average_df[f'{svc}_{metric}']
      y_label = 'Resource'
      if metric != 'power':
        if metric == 'cpu':
          metric_values = metric_values / 100
          y_label = f'{metric.capitalize()} Usage %'
        else:
          metric_values = metric_values / 1000000
          y_label = f'{metric.capitalize()} Usage MB'
      else:
        y_label = 'Power (W)'
            
      # Plot with a specific color for each time window
      axes[i].plot(time_values, round(metric_values, 2), label=f'{svc}')  
      axes[i].set_title(f"Time Window {time} sec")     
      axes[i].set_xlabel('Time')
      axes[0].set_ylabel(y_label)
        
  plt.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fancybox=True, shadow=True, ncol=1)
  plt.tight_layout()  
  
  directory = os.path.join(PLOTS_FOLDER, 'Plots', SYSTEM, 'Metrics', metric)
  os.makedirs(directory, exist_ok=True)

  file_name = os.path.join(directory, f"{SYSTEM}-{metric}-{service}_{stress}_{user}_{scenario}_plots.pdf")
  plt.savefig(file_name)
  plt.close()
  
def get_energy_plots(df, metric, service, stress, user, scenario):
  fig = plt.figure(figsize=(10, 6))
  fig.suptitle(f"{metric.capitalize()} Usage for Stress={service} {stress.split('_')[1]}%, User={user}, Scenario={scenario.split('_')[1]}")     
  bin_sizes = {5: 2, 10: 4, 30: 12, 60: 24}  # Customize bin sizes based on your requirements

  for i, time in enumerate(TIME_WINDOWS):    
    summed_df = reduce(lambda x, y: x.add(y, fill_value=0), df[f'time_window_{time}'])
    average_df = summed_df / len(df[f'time_window_{time}'])     
    
    metric_values = average_df[f'{service}_{metric}']
    bin_size = bin_sizes[int(time)]
         
    # Plot with a specific color for each time window
    plt.hist(metric_values, bins=np.arange(min(metric_values), max(metric_values) + bin_size, bin_size), alpha=0.3, label=f'Time Window {time}')
    
        
  plt.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fancybox=True, shadow=True, ncol=1)
  plt.xlabel('Energy Usage Joule')
  plt.tight_layout()  
  
  directory = os.path.join(PLOTS_FOLDER, 'Plots', SYSTEM, 'Metrics', metric)
  os.makedirs(directory, exist_ok=True)

  file_name = os.path.join(directory, f"{SYSTEM}-{metric}-{service}_{stress}_{user}_{scenario}_plots.pdf")
  plt.savefig(file_name)
  plt.close()
  
def get_resource_consumption_plots():
  services = get_folder_names(DATA_FOLDER)  
  while 'normal' in services:
    services.remove("normal")
    
  for service in services:
      service_folder = os.path.join(DATA_FOLDER, service)
      stressors = get_folder_names(service_folder)
      
      for stressor in stressors:
          stressor_folder = os.path.join(service_folder, stressor)
          users = get_folder_names(stressor_folder)
          
          for user in users:
            user_folder = os.path.join(stressor_folder, user)
            scenarios = get_folder_names(user_folder)
          
            for scenario in scenarios:                  
              scenario_folder = os.path.join(user_folder, scenario)
              time_windows = get_folder_names(scenario_folder)
              
              time_window_per_treatment_dfs = {}
              for time in time_windows:
                
                if not time in time_window_per_treatment_dfs:
                  time_window_per_treatment_dfs[time] = {}
                  
                time_folder = os.path.join(scenario_folder, time)
                trials = get_folder_names(time_folder)
                
                dfs_by_trial = []
                for trial in trials:         
                  trial_folder = os.path.join(time_folder, trial)
                  
                  for file in os.listdir(trial_folder):
                    if not 'data.csv' in file:
                      continue
                    
                    df = pd.read_csv(os.path.join(trial_folder,file))
                    dfs_by_trial.append(df)
                    
                time_window_per_treatment_dfs[time] = dfs_by_trial
                
                
              get_metric_plots(time_window_per_treatment_dfs, 'cpu', service, stressor, user, scenario)
              get_metric_plots(time_window_per_treatment_dfs, 'memory', service, stressor, user, scenario)
              get_energy_plots(time_window_per_treatment_dfs, 'energy', service, stressor, user, scenario)
              get_metric_plots(time_window_per_treatment_dfs, 'power', service, stressor, user, scenario)


def get_anomaly_showcase_plots():
  services = get_folder_names(DATA_FOLDER)
    
  for service in services:              
    if service in 'normal':
      continue
                          
    service_folder = os.path.join(DATA_FOLDER, service)
    stressors = get_folder_names(service_folder)

    for stressor in stressors:
        stressor_folder = os.path.join(service_folder, stressor)
        users = get_folder_names(stressor_folder)

        for user in users:
            user_folder = os.path.join(stressor_folder, user)
            scenarios = get_folder_names(user_folder)
            
            for scenario in scenarios:          
                scenario_folder = os.path.join(user_folder, scenario)
                time_windows = get_folder_names(scenario_folder)
                
                for time in time_windows:
                    time_folder = os.path.join(scenario_folder, time)
                    trials = get_folder_names(time_folder)
                    
                    for trial in trials:
                        trial_folder = os.path.join(time_folder, trial)
                                            
                        for file in os.listdir(trial_folder):
                            if file != 'data.csv':
                              continue
                            df = pd.read_csv(os.path.join(trial_folder,file))
                            normal_file = os.path.join(RESULTS_FOLDER, 'normal', user, scenario, time, trial, file)
                            normal_df = pd.read_csv(normal_file)
                            for col in df.columns:
                                metric = 'cpu'
                                if col.endswith(f"{service}_{metric}"):
                                  fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(20, 6))
                                  fig.suptitle(f"{metric.capitalize()} Usage for Stress={service} {stressor.split('_')[1]}%, User={user}, Scenario={scenario.split('_')[1]}")     

                                  for i, svc in enumerate([service, service]):
                                    plot_df = df
                                    if i == 1:
                                      plot_df = normal_df
                                    plot_df["time"] = plot_df["time"].astype(float)
                                    plot_df["duration"] = plot_df["time"] - plot_df["time"].iloc[0]
                                    
                                    time_values = plot_df['duration']
                                    metric_values = plot_df[f'{svc}_{metric}']
                                    y_label = 'Resource'
                                    if metric != 'power':
                                      if metric == 'cpu':
                                        metric_values = metric_values / 100
                                        y_label = f'{metric.capitalize()} Usage %'
                                      else:
                                        metric_values = metric_values / 1000000
                                        y_label = f'{metric.capitalize()} Usage MB'
                                    else:
                                      y_label = 'Power (W)'
                                    
                                    legend_label = f'Anomalous {svc}'
                                    if i == 1:
                                      legend_label = f'Baseline {svc}'
                                    # Plot with a specific color for each time window
                                    axes.plot(time_values, round(metric_values, 2), label=legend_label)  
                                    axes.set_title(f"Anomaly Example")     
                                    axes.set_xlabel('Time')
                                    axes.set_ylabel(y_label)
                                        
                                  plt.legend(loc='upper left', bbox_to_anchor=(1.05, 1), fancybox=True, shadow=True, ncol=1)
                                  plt.tight_layout()  
                                  
                                  directory = os.path.join(PLOTS_FOLDER, 'Plots', SYSTEM, 'Metrics', 'Anomaly Showcase', metric)
                                  os.makedirs(directory, exist_ok=True)

                                  file_name = os.path.join(directory, f"{SYSTEM}-{metric}-{service}_{stressor}_{user}_{scenario}_plots.pdf")
                                  plt.savefig(file_name)
                                  plt.close()
                                      
  
if __name__ == "__main__":
  get_stats()
  get_overall_stats_per_time_window()
  get_stats_per_treatment()
  get_resource_consumption_plots()
  
    