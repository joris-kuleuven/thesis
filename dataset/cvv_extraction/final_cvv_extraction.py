from pydriller import Git
from git import Repo
import os
import re
from pydriller import ModificationType
import json
import cvv_tools

with open('jsons/vcc_results_test_4.json', 'r') as f:
    cve_data = json.load(f)
with open('jsons/vcc_error_commits_4.json', 'r') as f:
    error_commits = json.load(f)

def get_vcc(commit_hash, repo):
    # Remove .patch suffix if it exists
    if commit_hash.endswith(".patch"):
        commit_hash = commit_hash[:-6]  # Remove the last 6 characters (.patch)

    commit = repo.get_commit(commit_hash)
    fix_files = cvv_tools.get_fix_files(commit)
    commits_blame_del_lines = cvv_tools.blame_deleted_lines(repo, commit, fix_files)
    commits_blame_context = cvv_tools.blame_context_lines(repo, commit, fix_files)
    
    unique_commits = {}
    
    # Merge commit objects from both dictionaries into a single dictionary
    for file_path, commit_hash in commits_blame_del_lines.items():
        # Check if the commit hash is unique
        if commit_hash not in unique_commits.values():
            # Add the commit to the merged dictionary
            unique_commits[file_path] = list(commit_hash)
    
    for file_path, commit_hash in commits_blame_context.items():
        # Check if the commit hash is unique
        if commit_hash not in unique_commits.values():
            # Add the commit to the merged dictionary
            unique_commits[file_path] = list(commit_hash)
    return unique_commits

base_dir = 'C:\\MT_dataset_repos'
test_apps = []
done_apps = ["Kanboard", "Pimcore", "OwnCloud", "Microweber", "NextCloud"]
for appname, data in cve_data.items():
    if appname not in done_apps:
        repo_dir = os.path.join(base_dir, appname)
        repo = Git(repo_dir)
        # Iterate through data entries
        for entry in data['data']:
            # Check if 'references_transformed' attribute exists
            if 'references_transformed' in entry:
                # Iterate through commit URLs                
                for commit_url in entry['references_transformed']:
                    # Extract hash (last part of the URL)
                    commit_hash = commit_url.split('/')[-1]
                    try:
                        vcc = get_vcc(commit_hash, repo)
                        entry['vcc'] = vcc
                    except Exception as e:
                        print(f"An error occurred while processing commit {commit_hash}: {e}")
                        error_entry = {}
                        error_entry["commit_url"] = entry["gh_link"] + "/commit/" + commit_hash
                        error_entry["original_vuln"] = entry["original_vuln"]
                        error_commits.append(error_entry)


with open('jsons/vcc_results_all_v1.json', 'w') as file:
    json.dump(cve_data, file, indent=4)
with open('jsons/vcc_error_commits_all_v1.json', 'w') as file:
    json.dump(error_commits, file, indent=4)