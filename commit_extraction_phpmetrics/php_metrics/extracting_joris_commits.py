import os
import json
from extra_scripts import search_appname

with open("jsons/phpAppsWithGithubLinks.json", 'r') as file:
    appname_ghlink_data = json.load(file)
# Function to process a single JSON file
def process_json_file(file_path, for_git_metrics=False):
    with open(file_path, 'r') as f:
        commits = []
        if not for_git_metrics:
            data = json.load(f)
            repo_url = data.get("singleUrl", "")
            commits = data.get("commits", [])
            appname = search_appname(repo_url, appname_ghlink_data)
            
            # Append URL to each commit
            for commit in commits:
                commit["repo"] = repo_url
                if appname:
                    commit["appname"] = appname
                else:
                    raise Exception("ERROR: Appname not found")
        else:
            commits = []
            for line in f:
                entry = json.loads(line)
                commits.append(entry)
        if commits:
            return commits
        else:
            raise Exception("EMPTY COMMITS")
        

# Function to process all JSON files in a directory
def process_json_files(directory, for_git_metrics=False):
    all_commits = []
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            commits = process_json_file(file_path, for_git_metrics=for_git_metrics)
            all_commits.extend(commits)
    return all_commits

def json_file_processing_wrapper_random_commits():
    print("Processing json files...")
    json_directory = '/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/joris_jsons/random-commits_150324update'
    all_commits = process_json_files(json_directory)
    print("Processing is done, now saving...")

    output_file = '/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/jsons/joris_commits.json'
    with open(output_file, 'w') as f:
        json.dump(all_commits, f, indent=4)
    print("Done")

def removing_overlaps():
    with open('/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/jsons/joris_commits.json', 'r') as file:
        joris_commits = json.load(file)

    with open('/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/jsons/tabulated_commits_v8_nov.json', 'r') as file:
        tabulated_commits_v8 = json.load(file)

    # Remove duplicates from joris_commits
    unique_entries_joris = []
    for entry_joris in joris_commits:
        if entry_joris['sha'] not in [entry_v8['sha'] for entry_v8 in tabulated_commits_v8 if entry_v8['appname'] == entry_joris['appname']]:
            unique_entries_joris.append(entry_joris)

    # Remove duplicates from tabulated_commits_v8
    unique_entries_v8 = []
    for entry_v8 in tabulated_commits_v8:
        if entry_v8['sha'] not in [entry_joris['sha'] for entry_joris in joris_commits if entry_joris['appname'] == entry_v8['appname']]:
            unique_entries_v8.append(entry_v8)
    print("filtered v8", len(unique_entries_v8)) #this should print filtered v8 0

    # Save filtered commits to new JSON files
    with open('/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/jsons/joris_commits_filtered.json', 'w') as file:
        json.dump(unique_entries_joris, file, indent=4)

def removing_overlaps_v2():
    with open('/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/jsons/joris_commits.json', 'r') as file:
        joris_commits = json.load(file)

    with open('/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/jsons/tabulated_commits_v8_nov.json', 'r') as file:
        tabulated_commits_v8 = json.load(file)
    # Remove duplicates from joris_commits
    unique_entries_joris = []
    for entry_joris in joris_commits:
        exist = False
        for entry_v8 in tabulated_commits_v8:
            if entry_joris["sha"] == entry_v8["sha"] and entry_joris["appname"] == entry_v8["appname"]:
                exist = True
                break
        if not exist:
            unique_entries_joris.append(entry_joris)

    # Save filtered commits to new JSON files
    with open('/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/jsons/joris_commits_filtered_v2.json', 'w') as file:
        json.dump(unique_entries_joris, file, indent=4)

def removing_overlaps_check(): #
    with open('/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/jsons/joris_commits_filtered_v2.json', 'r') as file:
        joris_commits = json.load(file)

    with open('/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/jsons/tabulated_commits_v8_nov.json', 'r') as file:
        tabulated_commits_v8 = json.load(file)
    # Remove duplicates from joris_commits
    unique_entries_joris = []
    for entry_joris in joris_commits:
        exist = False
        for entry_v8 in tabulated_commits_v8:
            if entry_joris["sha"] == entry_v8["sha"] and entry_joris["appname"] == entry_v8["appname"]:
                exist = True
                break
        if not exist:
            unique_entries_joris.append(entry_joris)

    # Save filtered commits to new JSON files
    with open('/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/jsons/joris_commits_filtered_check.json', 'w') as file:
        json.dump(unique_entries_joris, file, indent=4)

# removing_overlaps_check()
def adding_php_metr_extracted():
    with open('/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/jsons/joris_commits_filtered_v2.json', 'r') as file:
        joris_commits_filtered = json.load(file)
    for com in joris_commits_filtered:
        com["php_metrics_extracted"] = 0
    with open('/home/deck/Documents/masterGT/mt_git/thesis/dataset/php_metrics/jsons/joris_commits_filtered_v3.json', 'w') as file:
        json.dump(joris_commits_filtered, file, indent=4)

def json_file_processing_wrapper_git_metr_commits():
    print("Processing json files...")
    json_directory = 'joris_jsons/ProccessFeatures_allCommits'
    all_commits = process_json_files(json_directory, for_git_metrics=True)
    print("Processing is done, now saving...")

    output_file = 'jsons/git_metrics_commits.json'
    with open(output_file, 'w') as f:
        json.dump(all_commits, f, indent=4)
    print("Done")

json_file_processing_wrapper_git_metr_commits()

