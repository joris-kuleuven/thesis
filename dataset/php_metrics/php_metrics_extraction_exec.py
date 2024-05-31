import php_metrics_extraction_tools as my_tools
import os
import time
import json

def get_commit_metrics(appname, commit_sha, on_deck=False):
    print("Getting metrics for commit: ", commit_sha, " from app ", appname)
    start_time = time.time()  # Record the start time
    if on_deck:
        base_path = '/home/deck/Documents/masterGT/MT_dataset_repos'
    else:
        base_path = 'C:\\MT_dataset_repos'

    repo_path = os.path.join(base_path, appname)
    temp_dir = os.path.join(repo_path, "temp")
    xml_path = os.path.join(base_path, "sum.xml")   
    php_file_counter = 0
    print("PREPARING FILES...")

    try:        
        php_file_counter = my_tools.prepare_files(appname, commit_sha, on_deck)
    except Exception as e:
        print("Error in preparing files: ", str(e))
        print("CLEANING UP...")
        try:
            my_tools.clear_temp_files(appname, on_deck)
        except Exception as e:
            print("Error cleaning up ", str(e))
            raise e
        raise e

    print("RUNNING PDEPEND...")
    try:
        if php_file_counter > 0:
            my_tools.run_pdepend(temp_dir, on_deck)
        else:
            print("There's no php files in commit ", commit_sha)
    except Exception as e:
        print("Error in running pdepend: ", str(e))
        print("CLEANING UP...")
        try:
            my_tools.clear_temp_files(appname, on_deck)
        except Exception as e:
            print("Error cleaning up ", str(e))
            raise e
        raise e

    print("PARSING RESULT XML...")
    try:
        if php_file_counter > 0:
            result = my_tools.parse_xml(xml_path)
        else:
            result = {
                'average_loc': -1,
                'average_ncloc': -1,
                'average_dit': -1,
                'average_nocc': -1,
                'average_cbo': -1,
                'average_wmc': -1,
                'average_ccn': -1,
                'average_hv': -1,
            }
    except Exception as e:
        print("Error parsing sum.xml: ", str(e))
        print("CLEANING UP...")
        try:
            my_tools.clear_temp_files(appname, on_deck)
        except Exception as e:
            print("Error cleaning up ", str(e))
            raise e
        raise e

    print("CLEANING UP...")
    try:
        my_tools.clear_temp_files(appname, on_deck)
    except Exception as e:
        print("Error cleaning up ", str(e))
        raise e
    
    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time  # Calculate elapsed time
    print("Elapsed time is ", elapsed_time)
    if result:
        return result
    else:
        raise Exception("Result not found")

def test_get_commit_metrics(on_deck=False):
    if on_deck:
        base_path = '/home/deck/Documents/masterGT/MT_dataset_repos'
    else:
        base_path = 'C:\\MT_dataset_repos'
    
    appname = "OwnCloud"
    sha_test = "5da6475927a0cf359d8befd7e23e64b470fd9ad5" #Microweber, basically 0 php
    sha_test_2 = "c93eca49c32428ece03dd67042772d5fa62c8d6e" #OwnCloud, not part of the branch
    sha_test_3 = "ca036e9f86bb5cdb3dac0930ec131e5f35e26c5f" #Pimcore, lotsa of files (50)

    repo_path = os.path.join(base_path, appname)
    temp_dir = os.path.join(repo_path, "temp")
    xml_path = os.path.join(base_path, "sum.xml")
    # my_tools.prepare_files(appname, sha_test, on_deck=on_deck)
    # my_tools.run_pdepend(temp_dir, on_deck=on_deck)
    # print(my_tools.parse_xml(xml_path))
    # my_tools.clear_temp_files(appname, on_deck=on_deck)
    
    print(get_commit_metrics(appname, sha_test_2, on_deck))
    

def main_run():
    my_tools.clear_all_temp_files()
    start_time = time.time()  # Record the start time
    with open("/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/jsons/joris_commits_filtered_v3.json", 'r') as file:
        tabulated_commits = json.load(file)
    # test_apps = ["NextCloud", "Tuleap", "Piwigo", "Shopware"]
    count = 0
    for commit in tabulated_commits:
        php_metrics_extracted = commit["php_metrics_extracted"]
        
        if php_metrics_extracted == 0:
        #if commit["appname"] in test_apps:    
            try:
                result = get_commit_metrics(commit["appname"], commit["sha"], on_deck=True)
                commit["average_loc"] = result["average_loc"]
                commit["average_ncloc"] = result["average_ncloc"]
                commit["average_dit"] = result["average_dit"]
                commit["average_nocc"] = result["average_nocc"]
                commit["average_cbo"] = result["average_cbo"]
                commit["average_wmc"] = result["average_wmc"]
                commit["average_ccn"] = result["average_ccn"]
                commit["average_hv"] = result["average_hv"]
                commit["php_metrics_extracted"] = 1
            except Exception as e:
                print("ERROR getting commit metrics: ", str(e))
                commit["php_metrics_extracted"] = -1
            count += 1
        if count%200 == 0: #This is to save as we go along so we dont lose progress, it saves every 200 commit metric extraction
            with open('/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/jsons/joris_commits_filtered_v4.json', 'w') as file:
                json.dump(tabulated_commits, file, indent=4)

    with open('/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/jsons/joris_commits_filtered_v4.json', 'w') as file:
            json.dump(tabulated_commits, file, indent=4)
    end_time = time.time()  # Record the end time
    elapsed_time = end_time - start_time  # Calculate elapsed time
    print("In total, the whole extraction takes ", elapsed_time," seconds")
    print("The whole process processed", count, "commits")

main_run()