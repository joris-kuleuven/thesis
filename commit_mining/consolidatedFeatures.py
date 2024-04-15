import signal
from github import Github
from github import Auth
from git import Repo
from pydriller import Repository
import json
import pandas as pd
from pydriller import Git
import statistics as stat
import logging
import shutil
from commitUtils import get_file_name, get_user_data, previous_changes, get_author_login, is_bugfix_commit, parse_hunks
from utils import print_star
from utils import handler, TimeoutError
import blacklist as bl
import sys

# Check if there are command-line arguments
if len(sys.argv) > 1:
    # Access the command-line arguments
    file_path = sys.argv[1]
else:
    print("No command-line arguments provided. Exiting program.")
    sys.exit(1)

# Set up logging and authentication
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.WARN, filename=f'gatherfeatures.log')
token = ""
auth = Auth.Token(token)
g = Github(auth=auth)
logging.warning("File path: " + file_path)

# Set the timeout duration in seconds
timeout_duration = 300  # 5 minutes

# Install the signal handler for SIGALRM
signal.signal(signal.SIGALRM, handler)

# Load the JSON file
with open(file_path, "r") as f:
    data = json.load(f)

# Access the singleUrl and commits
repo_url = data["singleUrl"]
commits = data["commits"]

# Convert the commits list of dictionaries to a DataFrame
df_commits = pd.DataFrame(commits)
# Rename the 'sha' column to 'commit_sha'
df_commits.rename(columns={"sha": "commit_sha"}, inplace=True)

# Display the DataFrame
print(df_commits.head())

# Print the singleUrl and commits
print("repoUrl:", repo_url)
logging.warning("repoUrl: " + repo_url)
df_commits.head()

parts = repo_url.strip("/").split("/")
username = parts[-2]
repo_name = parts[-1]

localFilePath = f"{username}/{repo_name}"
print("Local file path:", localFilePath)
# Get the repository object
repo = g.get_repo(f"{username}/{repo_name}")
print("Repository object:", repo)
pygh_repo = g.get_repo(f"{username}/{repo_name}")
pydr_repo = Repository(repo_url)
print("Pydriller repository object created")
#jit
cloned_repo = Repo.clone_from(repo_url, localFilePath)
logging.warning("Cloned repository to: " + localFilePath)
pydr_git = Git(localFilePath)
commitsObjectList = list(Repository(localFilePath).traverse_commits())
createdDate = pygh_repo.created_at
print("Created date:", createdDate)

# Get all official commit logins from GitHub
def get_author_lambda(hash):
    print_star()
    return get_author_login(username, repo_name, hash, token)

print("\nGetting authors for ", df_commits.shape[0], " commits")
df_commits['author'] = df_commits['commit_sha'].apply(get_author_lambda)
print("\nCommit authors:\n", df_commits.head())

def get_author_info_lambda(author):
    print_star()
    return get_user_data(author, token)

df_commits['author_info'] = df_commits['author'].apply(get_author_info_lambda)



# join dataframes
merged_df = df_commits

# Convert the commit SHA values in the DataFrame to a set for faster lookup
commit_shas = set(df_commits['commit_sha'])

def compute_process_metrics(git_repo, git_commits, git_commit):
    process_metrics = {}
    past_authors = set()
    valid_modified_files = {}

    process_metrics["sha"] = git_commit.hash
    process_metrics["author"] = git_commit.author.email
    process_metrics["author_date"] = git_commit.author_date
    process_metrics["author_timezone"] = git_commit.author_timezone

    # calculations
    process_metrics["days_after_creation"] = (git_commit.author_date - createdDate).days
    past_contributions = [gc for gc in git_commits if gc.author_date <= git_commit.author_date]
    author_past_contributions = [gc for gc in past_contributions if gc.author.email == process_metrics["author"]]
    process_metrics["past_contributions"] = len(author_past_contributions)
    process_metrics["ratio_past_contributions"] = len(author_past_contributions) / len(past_contributions)
    process_metrics["new_author"] = True if git_commit in author_past_contributions[:-1] else False

    # 30 days
    past_contributions_30_days = [gc for gc in past_contributions if abs((git_commit.author_date - gc.author_date).days) <= 30]
    author_past_contributions_30_days = [gc for gc in past_contributions_30_days if gc.author.email == process_metrics["author"]]
    process_metrics["past_contributions_30_days"] = len(author_past_contributions_30_days)
    process_metrics["ratio_past_contributions_30_days"] = len(author_past_contributions_30_days) / len(past_contributions_30_days)

    # delta maintainability metrics
    process_metrics["dmm_unit_size"] = git_commit.dmm_unit_size
    process_metrics["dmm_unit_complex"] = git_commit.dmm_unit_complexity
    process_metrics["dmm_unit_interf"] = git_commit.dmm_unit_interfacing

    process_metrics["fix"] = True if is_bugfix_commit(git_commit) else False

    # file-level metrics
    nr_of_blacklisted = 0
    for mod_file in git_commit.modified_files:
        filepath = get_file_name(mod_file)
        if bl.is_blacklisted(filepath):
            nr_of_blacklisted += 1
            continue
        if mod_file.added_lines == 0 and mod_file.deleted_lines == 0:
            continue
        prev_changes_distr = previous_changes(git_repo, git_commit.hash, filepath)
        if len(prev_changes_distr) == 0:
                days_since_creation_distr = 0
        else:
            creating_commit = git_repo.get_commit(prev_changes_distr[0])
            days_since_creation_distr = (git_commit.author_date - creating_commit.author_date).days
            if days_since_creation_distr < 0:
                days_since_creation_distr = (git_commit.committer_date - creating_commit.committer_date).days
        past_authors.update({git_repo.get_commit(c).author.email for c in prev_changes_distr}) # change to officialID
        valid_modified_files[filepath] = {
                "added_lines": mod_file.added_lines,
                "deleted_lines": mod_file.deleted_lines,
                "hunks": len(parse_hunks(mod_file)),
                "previous_changes": len(prev_changes_distr),
                "days_since_creation": days_since_creation_distr,
            }
        process_metrics["touched_files"] = len(valid_modified_files)
        process_metrics["past_authors"] = len(past_authors)
        process_metrics.update({
            "sum_added_lines": 0,
            "mean_added_lines": 0,
            "med_added_lines": 0,
            "sum_deleted_lines": 0,
            "mean_deleted_lines": 0,
            "med_deleted_lines": 0,
            "sum_hunks": 0,
            "mean_hunks": 0,
            "med_hunks": 0,
            "sum_previous_changes": 0,
            "mean_previous_changes": 0,
            "med_previous_changes": 0,
            "sum_days_since_creation": 0,
            "mean_days_since_creation": 0,
            "med_days_since_creation": 0,
        })

        if (len(valid_modified_files)) > 0:
            added_lines_distr = [file["added_lines"] for file in valid_modified_files.values() if file["added_lines"]]
            deleted_lines_distr = [file["deleted_lines"] for file in valid_modified_files.values() if file["deleted_lines"]]
            hunks_distr = [f["hunks"] for f in valid_modified_files.values() if f["hunks"]]
            prev_changes_distr = [f["previous_changes"] for f in valid_modified_files.values() if f["previous_changes"]]
            days_since_creation_distr = [f["days_since_creation"] for f in valid_modified_files.values() if f["days_since_creation"]]
            process_metrics.update({
                "sum_added_lines": sum(added_lines_distr),
                "mean_added_lines": stat.mean(added_lines_distr) if len(added_lines_distr) > 0 else 0,
                "med_added_lines": stat.median(added_lines_distr) if len(added_lines_distr) > 0 else 0,
                "sum_deleted_lines": sum(deleted_lines_distr),
                "mean_deleted_lines": stat.mean(deleted_lines_distr) if len(deleted_lines_distr) > 0 else 0,
                "med_deleted_lines": stat.median(deleted_lines_distr) if len(deleted_lines_distr) > 0 else 0,
                "sum_hunks": sum(hunks_distr),
                "mean_hunks": stat.mean(hunks_distr) if len(hunks_distr) > 0 else 0,
                "med_hunks": stat.median(hunks_distr) if len(hunks_distr) > 0 else 0,
                "sum_previous_changes": sum(prev_changes_distr),
                "mean_previous_changes": stat.mean(prev_changes_distr) if len(prev_changes_distr) > 0 else 0,
                "med_previous_changes": stat.median(prev_changes_distr) if len(prev_changes_distr) > 0 else 0,
                "sum_days_since_creation": sum(days_since_creation_distr),
                "mean_days_since_creation": stat.mean(days_since_creation_distr) if len(days_since_creation_distr) > 0 else 0,
                "med_days_since_creation": stat.median(days_since_creation_distr) if len(days_since_creation_distr) > 0 else 0,
            })
            process_metrics["nr_of_blacklisted"] = nr_of_blacklisted
    
    return(process_metrics)

JITmetricsList = list()

# Traverse all commits in the repository
for commit in pydr_repo.traverse_commits():
    # If the commit's hash is in the set of commit SHA values, add it to the list
    if commit.hash in commit_shas:
        print_star(True)
        try:
            signal.alarm(timeout_duration) # Set the alarm for timeout_duration seconds
            JITmetricsList.append(compute_process_metrics(pydr_git, commitsObjectList, commit))
            signal.alarm(0) # Reset the alarm
            commit_shas.remove(commit.hash)
        except TimeoutError as e:
            logging.error("Timeout occurred while processing commit %s", commit.hash)
        except Exception as e:
            logging.error("Error in computing process metrics for commit %s: %s", commit.hash, str(e))
        finally:
            signal.alarm(0) # Reset the alarm
            continue
    else:
        print_star(False)

df_jit = pd.DataFrame(JITmetricsList)

final_df = pd.merge(merged_df, df_jit, left_on='commit_sha', right_on='sha')
final_df.drop('sha', axis=1, inplace=True)

output_path = f'{repo_name}_final_df.json'
final_df.to_json(output_path, orient='records', lines=True)
logging.warning("Final dataframe saved to JSON file: " + f'{repo_name}_final_df.json')
print("Final dataframe saved to JSON file: ", output_path)
shutil.rmtree(localFilePath)
print("Local repository deleted")
