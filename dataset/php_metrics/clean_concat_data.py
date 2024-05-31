import json


"""
This file is responsible for cleaning the dataset, mostly ensuring that every commit entry has the same features
Additionally, I will concatenate (and combine) different commit sets here.
"""

def clean_data(input_path_file, output_path_file, vuln_to_bool=True):
    with open(input_path_file, 'r') as file:
        tabulated_commits = json.load(file)

    for com in tabulated_commits:        

        #change the vulnerability label to boolean, only for tab commits v8 and below
        if vuln_to_bool:
            com["neutral"] = False
            if com["is_vulnerable"] == 1:
                com["is_vulnerable"] = True
            else:
                com["is_vulnerable"] = False

        #add the oop_php_files_exist attr
        if "average_loc" in com and com["average_loc"] == -1 and com["php_metrics_extracted"] != -1:
            com["oop_php_files_exist"] = False
        elif com["php_metrics_extracted"] != -1:
            com["oop_php_files_exist"] = True
        else:
            com["oop_php_files_exist"] = None

        #if it's error, add php metrics attribute and set to None
        if com["php_metrics_extracted"] == -1:
            com["average_loc"] = None
            com["average_ncloc"] = None
            com["average_dit"] = None
            com["average_nocc"] = None
            com["average_cbo"] = None
            com["average_wmc"] = None
            com["average_ccn"] = None
            com["average_hv"] = None

    with open(output_path_file, 'w') as file:
        json.dump(tabulated_commits, file, indent=4)

def concat(input_file_1, input_file_2, output_path):
    with open(input_file_1, 'r') as file:
        tabulated_commits_1 = json.load(file)
    with open(input_file_2, 'r') as file:
        tabulated_commits_2 = json.load(file)
    
    with open(output_path, 'w') as file:
        json.dump(tabulated_commits_1 + tabulated_commits_2, file, indent=4)

def get_commit(tabulated_commits, sha):
    for com in tabulated_commits:
        if "sha" in com and com["sha"] == sha:
            return com
        elif "commit_sha" in com and com["commit_sha"] == sha:
            return com
    return None
        

def merge_git_php_commits(git_metrics_file_path, php_metrics_file_path, output_file_path):
    with open(git_metrics_file_path, 'r') as f:
        git_metrics_commits = json.load(f)
    with open(php_metrics_file_path, 'r') as f:
        php_metrics_commits = json.load(f)
    
    for com in git_metrics_commits:
        sha = com["commit_sha"]
        other_com = get_commit(php_metrics_commits, sha)
        if other_com:
            com.update({
                "repo": other_com.get("repo"),
                "appname": other_com.get("appname"),
                "php_metrics_extracted": other_com.get("php_metrics_extracted"),
                "average_loc": other_com.get("average_loc"),
                "average_ncloc": other_com.get("average_ncloc"),
                "average_dit": other_com.get("average_dit"),
                "average_nocc": other_com.get("average_nocc"),
                "average_cbo": other_com.get("average_cbo"),
                "average_wmc": other_com.get("average_wmc"),
                "average_ccn": other_com.get("average_ccn"),
                "average_hv": other_com.get("average_hv"),
                "oop_php_files_exist": other_com.get("oop_php_files_exist")
            })
        else:
            print("Other com from php_metrics for some reason dont exist for", sha)
    
    with open(output_file_path, 'w') as file:
        json.dump(git_metrics_commits, file, indent=4)


# clean_data("jsons/joris_commits_filtered_v4.json", "jsons/joris_commits_filtered_v5.json", vuln_to_bool=False)
# concat("jsons/joris_commits_filtered_v5.json", "jsons/tabulated_commits_v9_nov.json", "jsons/tabulated_commits_v10_nov.json")
# merge_git_php_commits("jsons/git_metrics_commits.json", "jsons/tabulated_commits_v10_nov.json", "jsons/tabulated_commits_v11_nov.json")
