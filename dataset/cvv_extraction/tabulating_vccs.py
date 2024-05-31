import json

with open('jsons/vcc_results_all_v1.json', 'r') as f:
    full_cve_vcc = json.load(f)

tabulated_commits = []
for appname, data in full_cve_vcc.items():   
    for entry in data['data']:
        # Check if 'references_transformed' attribute exists
        if 'references_transformed' in entry:              
            for commit_url in entry['references_transformed']:
                dict_entry = {}
                dict_entry["sha"] = commit_url.split("/")[-1]
                dict_entry["repo"] = entry["gh_link"]
                dict_entry["is_vulnerable"] = 0
                dict_entry["original_vuln"] = entry["original_vuln"]
                tabulated_commits.append(dict_entry)
        if 'vcc' in entry:
            for file, shas in entry["vcc"].items():
                for sha in shas:
                    dict_entry = {}
                    dict_entry["sha"] = sha
                    dict_entry["repo"] = entry["gh_link"]
                    dict_entry["is_vulnerable"] = 1
                    dict_entry["original_vuln"] = entry["original_vuln"]
                    tabulated_commits.append(dict_entry)
                
with open('jsons/tabulated_commits_v1.json', 'w') as file:
    json.dump(tabulated_commits, file, indent=4)