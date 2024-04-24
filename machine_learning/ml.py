import numpy as np
import pandas as pd
from tqdm import tqdm
import os
import json
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import AdaBoostClassifier
from sklearn.metrics import accuracy_score
from imblearn.under_sampling import RandomUnderSampler
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.model_selection import RepeatedStratifiedKFold
from sklearn.model_selection import RandomizedSearchCV
from sklearn.metrics import roc_curve, auc, roc_auc_score, confusion_matrix, matthews_corrcoef, f1_score, precision_score
from numpy import interp
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
import pickle
from imblearn.over_sampling import SMOTE
from multiprocessing import Pool, cpu_count
from sklearn.model_selection import LeaveOneGroupOut
from worker import worker

ml_vars_dir = "vars"

def bool_cols_to_bin_cols(df):
    bin_cols = ["fix", "is_vulnerable", "neutral", "new_author", "oop_php_files_exist", "authorPresent"]
    # Change binaries to 0 and 1
    for col in bin_cols:
        df[col] = df[col].astype(int)

def apply_smote(X_train, y_train, desired_ratio):
    smote = SMOTE(sampling_strategy=desired_ratio, random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
    return X_train_resampled, y_train_resampled

def calc_vif(X):
    # Calculating VIF
    vif = pd.DataFrame()
    vif["variables"] = X.columns

    with Pool(cpu_count()) as p:
        vif["VIF"] = p.map(worker, [(X, i) for i in range(X.shape[1])])

    return vif

def feature_selection(df_in):
    nr_of_columns_init = df_in.shape[1]
    vif1 = calc_vif(df_in)
    a=vif1.VIF.max()
    while a > 5:
        maximum_a = vif1.loc[vif1['VIF'] == vif1['VIF'].max()]
        vif1 = vif1.loc[vif1['variables'] != maximum_a.iloc[0,0]]
        vif1 = calc_vif(df_in[vif1.variables.tolist()])
        a = vif1.VIF.max()
        print("Dropping feature with VIF of ", maximum_a.iloc[0,1])
        print("Remaining number of features: ", vif1.shape[0])

    X = df_in[vif1.variables.tolist()]
    nr_of_columns_final = X.shape[1]
    print("Selected ", nr_of_columns_final, " out of ", nr_of_columns_init, " features.")
    dropped_list = [col for col in df_in.columns if col not in X.columns]
    with open('dropped_features.txt', 'w') as f:
        for item in dropped_list:
            f.write("%s\n" % item)

    print("Dropped features: ", dropped_list)
    return X

def data_preprocessing(source):
    print("Pre-processing data...")
    
    # Check if the file ends with .csv or .json
    if source.endswith('.csv'):
        # Read CSV file
        tc_df = pd.read_csv(source)
    elif source.endswith('.json'):
        # Read JSON file
        tc_df = pd.read_json(source)
    else:
        # If the file extension is neither .csv nor .json, raise an error
        raise ValueError("Unsupported file format. Please provide a CSV or JSON file.")
    print("Non-numerical processing")

    
    num_rows_with_null = tc_df.isnull().any(axis=1).sum() # Count the number of rows with at least one null value
    num_nulls = tc_df.isnull().sum().sum() # Count the number of null values in the dataframe
    numeric_cols = tc_df.select_dtypes(include=[np.number]).columns
    tc_df[numeric_cols] = tc_df[numeric_cols].fillna(tc_df[numeric_cols].mean())
    print(f"Replaced {num_nulls} null values in ", num_rows_with_null, " rows column average.")

    y = tc_df['is_vulnerable']
    X = tc_df.drop(columns=['is_vulnerable'])

    
    print("Feature selection with VIF...")
    groups = X['appname']
    X = X.drop(columns=['appname'])
    print("Number of LOGO groups: ", len(groups.unique()))
    # colX = [c for c in feature_selection(X.drop(columns=['commit_time']))]
    colX = [c for c in feature_selection(X)]

    # colX = [c for c in feature_selection(X)]

    X = X[colX]
    
    print("Pre-processing done!\n")
    return X, y, groups
    
def save_variables(file_name, variables):
    file_path = os.path.join(ml_vars_dir, file_name)
    with open(file_path, 'wb') as handle:
        pickle.dump(variables, handle, protocol=pickle.HIGHEST_PROTOCOL)

def train_cv_save_results(clf_name, cv, X_final, y_final, LOGO_groups, save_file_name, Xy_are_np=False):
    if not Xy_are_np:    #Check if numpy
        X_final_np = X_final.values
        y_final_np = y_final.values
    else:
        X_final_np = X_final
        y_final_np = y_final
    if clf_name == "AdaBoostClassifier":
        clf = AdaBoostClassifier(n_estimators=1900, learning_rate=0.1, random_state=0)
    else:
        raise Exception("Clf not set for clf name", clf_name)
    
    # splits_indices = cv.split(X_final_np, y_final_np) # Kfold

    splits_indices = cv.split(X_final_np, y_final_np, groups=LOGO_groups)

    mean_fpr = np.linspace(0, 1, 100)
    tprs = []
    aucs = []

    N, P = X_final_np.shape

    # Aggregate the importances over folds here:
    importances_random = np.zeros(P)

    # Loop over crossvalidation folds:
    scores = []  # Collect accuracies here

    TP = []
    FP = []
    TN = []
    FN = []
    tnList = []
    fpList = []
    fnList = []
    tpList = []
    precisionList = []
    f1List = []
    mccList = []

    i = 1
    count = 0
    # for train, test in cv.split(X, y):
    train_splits = []
    test_splits = []
    train_anomaly_percentage = []
    test_anomaly_percentage = []
    train_anomaly_absolute = []
    test_anomaly_absolute = []
    counterfold = 1
    nr_iterations = len(LOGO_groups.unique())
    for train, test in tqdm(splits_indices, desc="Training", unit="fold", total=nr_iterations):
        # print("Iteration ", counterfold, " of ", len(LOGO_groups.unique()))
        counterfold +=1
        train_splits.append(train)
        test_splits.append(test)
        count += 1

        X_train = X_final_np[train]
        y_train = y_final_np[train]
        X_test = X_final_np[test]
        y_test = y_final_np[test]

        X_train, y_train = apply_smote(X_train, y_train, 1)

        a, b = np.unique(y_train, return_counts=True)[1]
        train_anomaly_percentage.append(b / (a + b))
        train_anomaly_absolute.append(b)
        c, d = np.unique(y_test, return_counts=True)[1]
        test_anomaly_percentage.append(d / (c + d))
        test_anomaly_absolute.append(d)

        clf.fit(X_train, y_train)

        probas_ = clf.predict_proba(X_test)
        y_pred = clf.predict(X_test)

        # Compute ROC curve and area under the curve
        
        fpr, tpr, thresholds = roc_curve(y_test, probas_[:, 1], pos_label=1)

        tprs.append(interp(mean_fpr, fpr, tpr))
        tprs[-1][0] = 0.0
        roc_auc = auc(fpr, tpr)
        aucs.append(roc_auc)

        # calculate confusion matrix, precision, f1 and Matthews Correlation Coefficient

        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
        precision = precision_score(y_test, y_pred)
        mcc = matthews_corrcoef(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)

        TN.append(tn)
        TP.append(tp)
        FN.append(fn)
        FP.append(fp)

        tnList.append(tn / (tn + fp))
        tpList.append(tp / (fn + tp))
        fpList.append(fp / (tn + fp))
        fnList.append(fn / (fn + tp))

        precisionList.append(precision)
        f1List.append(f1)
        mccList.append(mcc)

        i += 1
        
    tnList = 100 * np.array(tnList)
    tpList = 100 * np.array(tpList)
    fnList = 100 * np.array(fnList)
    fpList = 100 * np.array(fpList)
    precisionList = 100 * np.array(precisionList)
    f1List = 100 * np.array(f1List)
    mccList = 100 * np.array(mccList)

    mean_tpr = np.mean(tprs, axis=0)
    mean_tpr[-1] = 1.0
    # mean_auc = auc(mean_fpr, mean_tpr)
    mean_auc = np.mean(aucs)
    std_auc = np.std(aucs)
    auc_meanpercent = 100 * mean_auc
    auc_stdpercent = 100 * std_auc

    variables_to_save = {
        'tprs': tprs,
        'aucs': aucs,
        'N': N,
        'P': P,
        'importances_random': importances_random,
        'scores': scores,
        'TP': TP,
        'FP': FP,
        'TN': TN,
        'FN': FN,
        'tnList': tnList,
        'fpList': fpList,
        'fnList': fnList,
        'tpList': tpList,
        'precisionList': precisionList,
        'f1List': f1List,
        'mccList': mccList,
        'train_splits': train_splits,
        'test_splits': test_splits,
        'train_anomaly_percentage': train_anomaly_percentage,
        'test_anomaly_percentage': test_anomaly_percentage,
        'train_anomaly_absolute': train_anomaly_absolute,
        'test_anomaly_absolute': test_anomaly_absolute,
        'auc_meanpercent': auc_meanpercent,
        'auc_stdpercent' : auc_stdpercent
    }
    save_variables(save_file_name, variables_to_save)
   
def load_variables(file_name):
    file_path = os.path.join(ml_vars_dir, file_name)
    with open(file_path, 'rb') as handle:
        loaded_variables = pickle.load(handle)    
    return loaded_variables

def load_show_metrics(file_name):
    print("Showing metrics for file", file_name)
    # Load variables from the file
    loaded_variables = load_variables(file_name)
    # Return each variable separately
    tprs = loaded_variables['tprs']
    aucs = loaded_variables['aucs']
    N = loaded_variables['N']
    P = loaded_variables['P']
    importances_random = loaded_variables['importances_random']
    scores = loaded_variables['scores']
    TP = loaded_variables['TP']
    FP = loaded_variables['FP']
    TN = loaded_variables['TN']
    FN = loaded_variables['FN']
    tnList = loaded_variables['tnList']
    fpList = loaded_variables['fpList']
    fnList = loaded_variables['fnList']
    tpList = loaded_variables['tpList']
    precisionList = loaded_variables['precisionList']
    f1List = loaded_variables['f1List']
    mccList = loaded_variables['mccList']
    train_splits = loaded_variables['train_splits']
    test_splits = loaded_variables['test_splits']
    train_anomaly_percentage = loaded_variables['train_anomaly_percentage']
    test_anomaly_percentage = loaded_variables['test_anomaly_percentage']
    train_anomaly_absolute = loaded_variables['train_anomaly_absolute']
    test_anomaly_absolute = loaded_variables['test_anomaly_absolute']
    
    mean_auc = np.mean(aucs)
    std_auc = np.std(aucs)
    auc_meanpercent = 100 * mean_auc
    auc_stdpercent = 100 * std_auc
    
    """Show metrics"""
    
    # plt.clf()  # Clear the current figure
    
    print("TN: %.02f %% ± %.02f %% - FN: %.02f %% ± %.02f %%" % (np.mean(tnList),
                                                                    np.std(tnList),
                                                                    np.mean(fnList),
                                                                    np.std(fnList)))
    print("FP: %.02f %% ± %.02f %% - TP: %.02f %% ± %.02f %%" % (np.mean(fpList),
                                                                    np.std(fpList),
                                                                    np.mean(tpList),
                                                                    np.std(tpList)))

    print(
        "Precision: %.02f %% ± %.02f %% - F1: %.02f %% ± %.02f %% - MCC: %.02f %% ± %.02f %%" % (np.mean(precisionList),
                                                                                                    np.std(precisionList),
                                                                                                    np.mean(f1List),
                                                                                                    np.std(f1List),
                                                                                                    np.mean(mccList),
                                                                                                    np.std(mccList)))

    print("AUC: %.02f %% ± %.02f %%" % (auc_meanpercent, auc_stdpercent))

def train_ml_from_file(source, clf_name, save_file_name, repeats=1):
    save_file_path = save_file_name + ".pkl"
    X_final, y_final, logo_groups = data_preprocessing(source)
    # cv = RepeatedStratifiedKFold(n_splits=folds, n_repeats=repeats, random_state=1)
    cv = LeaveOneGroupOut()
    train_cv_save_results(clf_name, cv, X_final, y_final, logo_groups, save_file_path)
    load_show_metrics(save_file_path)

data_in_path = "2_subsets_with_nulls.csv"
output_filename = "abc_LOGO_with_nulls_dataset2_v1"
train_ml_from_file(data_in_path, "AdaBoostClassifier", output_filename, repeats=1)