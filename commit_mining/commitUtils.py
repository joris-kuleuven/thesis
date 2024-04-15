import re
import requests
import logging
import statistics as stat

def get_file_name(file): # SOURCE=JIT
    file_path = file.old_path
    # If this happens, then the file has been created in this commit
    if file_path == None:
        file_path = file.new_path
    return file_path

def previous_changes(git_repo, to_hash, file=None): # SOURCE=JIT
    args = ["--no-merges", "--format=%H", f"{to_hash}"]
    if file:
        args.append("--follow")
        args.append("--")
        args.append(file)
    from_creation_commits = git_repo.repo.git.log(*args).splitlines()[::-1][:-1]
    return from_creation_commits

def parse_hunks(mod_file):
    diff = mod_file.diff
    hunk_headers_indexes = []
    diff_lines = diff.splitlines()
    for index, diff_line in enumerate(diff_lines):
        if diff_line.startswith("@@ -"):
            hunk_headers_indexes.append(index)
    
    hunks_text = []
    for index, hunk_line in enumerate(hunk_headers_indexes):
        if not index == len(hunk_headers_indexes) - 1:
            hunk_text = diff_lines[hunk_line:hunk_headers_indexes[index + 1]]
        else:
            hunk_text = diff_lines[hunk_line:]
        hunks_text.append(hunk_text)

    hunks = []
    for hunk_text in hunks_text:
        hunk = {}
        hunk["raw_text"] = diff

        hunk["header"] = hunk_text[0]
        old = re.search("@@ -(.*) \+", hunk["header"]).group(1).strip().split(",")
        # Ignore subprojects commit hunks, which are very rare
        if len(old) < 2:
            continue
        hunk["old_start_line"] = old[0]
        hunk["old_length"] = old[1]
        new = re.search(".*\+(.*) @@", hunk["header"]).group(1).strip().split(",")
        # Ignore very small hunks, which are very rare
        if len(new) < 2:
            continue
        hunk["new_start_line"] = new[0]
        hunk["new_length"] = new[1]
        code_context = hunk["header"][hunk["header"].rfind("@") + 2:].strip()
        hunk["code_context"] = code_context

        change_block = [(i,line) for i, line in enumerate(hunk_text) if line.startswith("+") or line.startswith("-")]
        start_index = change_block[0][0]
        end_index = change_block[-1][0]
        hunk["before_ctx"] = hunk_text[1:start_index]
        hunk["change_block"] = [el[1] for el in change_block]
        hunk["after_ctx"] = hunk_text[end_index + 1:]
        hunks.append(hunk)
    return hunks

def adjust_message(message):
    message_no_carriage = message.replace("\r", "\n")
    one_newline_message = re.sub(r"\n+", "\n", message_no_carriage)
    clear_message = one_newline_message.replace("\n", ". ").replace("\t", " ").replace(",", " ").replace("\"", "'")
    stripped_message = clear_message.strip()
    return re.sub(r" +", " ", stripped_message)

# GitHub API functions
def get_author_login(owner, repo, commit_hash, token):
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_hash}"
    headers = {'Authorization': f'token {token}'}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        if 'author' in data and data['author'] is not None:
            author = data['author']['login']
        else:
            return None
    except:
        print("Error in getting author for commit", commit_hash)
        logging.error("Error in getting author for commit")
        author = None
    return author

def get_user_data(username, token):
    url = f"https://api.github.com/users/{username}"
    headers = {'Authorization': f'token {token}'}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        user_features = {
        'username': username,
        'public_repos': data['public_repos'],
        'followers': data['followers'],
        'following': data['following'],
        'public_gists': data['public_gists'],
        'created_at': data['created_at'],
    }
    except:
        if(username is not None):
            print("Error in getting user data for commit", username)
            logging.error("Error in getting user data for commit")
        else:
            print("Username is None")
            logging.error("Username is None")
        user_features = None

    

    return user_features

def get_commit_author(pygh_repo, commit_sha):
    commit = pygh_repo.get_commit(commit_sha)
    if commit.author is not None:
        return commit.author.login
    else:
        print("Commit author is None")
        return None

def get_official_logins(pydr_repo):
    commitMap = {}
    for commit in pydr_repo.traverse_commits():
        try:
            username = get_commit_author(commit.hash)
            sha = commit.hash
        except:
            username = None
            sha = commit.hash
            logging.error("Username is None for commit ", sha)
        if username is not None:
            commitMap[sha] = username
    return commitMap

def is_bugfix_commit(git_commit):
    bugfixing_keywords = {"bug", "defect", "fix", "error", "repair", "patch", "issue", "exception"}
    msg = adjust_message(git_commit.msg).lower()
    return any(k in msg for k in bugfixing_keywords)