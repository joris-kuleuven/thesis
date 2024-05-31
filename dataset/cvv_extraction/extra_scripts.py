import json

def fix_vcc_error_commits_2():
    with open('jsons/vcc_error_commits_2.json', 'r') as f:
        data = json.load(f)

    # Prepend URL prefix to each commit hash
    github_commit_urls = ["https://github.com/pimcore/pimcore/commit/" + commit_hash for commit_hash in data]

    # Save the updated data to a new JSON file
    with open('jsons/vcc_error_commits_2.json', 'w') as f:
        json.dump(github_commit_urls, f, indent=4)


def fix_error_commits_all(): #forgot to add /commit in the commit_url attribute of vcc_error_commits_all_v1
    with open('jsons/vcc_error_commits_all_v1.json', 'r') as f:
        data = json.load(f)

    # Modify commit_url in each dictionary
    for item in data:
        commit_url = item["commit_url"]
        url_parts = commit_url.split("/")
        if len(url_parts) >= 5:  # Ensure the URL has enough parts
            # Insert "commit/" after the repository name
            url_parts.insert(5, "commit")
            new_commit_url = "/".join(url_parts)
            item["commit_url"] = new_commit_url


    # Save the updated data to a new JSON file
    with open('jsons/vcc_error_commits_all_v2.json', 'w') as f:
        json.dump(data, f, indent=4)  # Use indent for pretty formatting, optional

#fix_vcc_error_commits_2()
#fix_error_commits_all()
# with open('jsons/vcc_error_commits_all_v2.json', 'r') as f:
#     data = json.load(f)
# print("There are ", len(data), " unused commit")
        
with open('jsons/tabulated_commits_v1.json', 'r') as f:
    data = json.load(f)
print("There are ", len(data), " tabulated commits")