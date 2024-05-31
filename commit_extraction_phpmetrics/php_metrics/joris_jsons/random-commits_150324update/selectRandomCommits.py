from pydriller import Repository
import random
import logging
import json
inputFile = "/home/joris/thesis/repo_shas.json"

logging.basicConfig(filename='selectRandomCommits.log',
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    level=logging.WARNING,
                    datefmt='%Y-%m-%d %H:%M:%S')

def generate_filename_from_url(url):
    url_without_protocol = url.replace("https://", "")
    filename = url_without_protocol.replace("/", "_")
    filename += ".json"
    return filename

with open(inputFile, 'r') as file:
    vulData = json.load(file)
    
def gather_commits(repo_url):
    original_commit_shas = vulData.get(repo_url, [])
    logging.warning("number of commits in project: " + str(len(original_commit_shas)))
    other_commit_shas = []
    try:
        for commit in Repository(repo_url).traverse_commits():
            if len(commit.parents) == 1:
                commit_sha = commit.hash
                if commit_sha not in original_commit_shas:
                    other_commit_shas.append(commit_sha)
    except Exception as e:
        logging.error(f"Error: {e}")
    vulnerable_count = sum(1 for sha in original_commit_shas if sha[1] == 1)
    print("Number of vulnerable commits:", vulnerable_count)

    # Add random sample of non-vulnerable commits
    non_vuln_commit_shas = random.sample(other_commit_shas, 3 * vulnerable_count)
    logging.warning("number of vulnerable commits: " + str(vulnerable_count))

    # Create list of objects with features: sha, is_vulnerable, neutral
    commits_data = []
    for sha in original_commit_shas:
        is_vulnerable = True if sha[1] == 1 else False
        commits_data.append({"sha": sha[0], "is_vulnerable": is_vulnerable, "neutral": False})
    for sha in non_vuln_commit_shas:
        commits_data.append({"sha": sha, "is_vulnerable": False, "neutral": True})
    
    # Output data containing singleUrl and commits
    outputData = {"singleUrl": repo_url, "commits": commits_data}
    output_file = generate_filename_from_url(repo_url)
    
    # Write the data to a JSON file
    with open(output_file, "w") as outfile:
        json.dump(outputData, outfile, indent=4)

    print(f"JSON file '{output_file}' has been created.")

# RUN MAIN FUNCTION
logging.warning("starting to gather commits")
for singleUrl, vul_commit_shas in vulData.items():
    try:
        logging.warning(f"processing {singleUrl}")
        gather_commits(singleUrl)
    except Exception as e:
        logging.error(f"Error while processing {singleUrl}: {e}")
logging.warning("finished gathering commits")
