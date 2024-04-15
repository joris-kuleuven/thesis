import json
import os
import shutil
import sys
import tempfile

import pandas as pd
from git import GitCommandError

sys.path.insert(0, "..")
import blacklist as bl
from commitUtils import get_file_name, parse_hunks
from repo_utils import clean_repo, clone_repo


def create_dir_if_not_exist(dir):
    if not os.path.exists(dir):
        #shutil.rmtree(dir) #do not remove
        os.mkdir(dir)


def get_lines(hunks, type):
    added_blocks = []
    for hunk in hunks:
        added_lines = [line[1:] for line in hunk["change_block"] if line.startswith(type)]
        added_block = "\n".join(added_lines)
        added_blocks.append(added_block)
    return "\n\n".join(added_blocks)


def extract_files_in_location(corpus_loc, project, commit_idx, git_commit):
    valid_mod_files = [mod_file for mod_file in git_commit.modified_files if
        not bl.is_blacklisted(get_file_name(mod_file)) and
        not mod_file.added_lines + mod_file.deleted_lines == 0 and
        get_file_name(mod_file).endswith(".php") and
        mod_file.source_code is not None
        ]
    if len(valid_mod_files) == 0:
        print(f"** No valid files in commit")
        return (0, 0)
    dest_dir = os.path.join(corpus_loc, str(commit_idx) + "_" + project + "_" + str(git_commit.hash))
    create_dir_if_not_exist(dest_dir)
    copied_file_sizes = []
    for idx, valid_mod_file in enumerate(valid_mod_files):
        new_filename = os.path.join(dest_dir, str(idx) + "_" + os.path.basename(get_file_name(valid_mod_file)))
        with open(new_filename, "w+") as file:
            file.write(valid_mod_file.source_code)
        copied_file_sizes.append(os.path.getsize(new_filename))
    return (len(copied_file_sizes), sum(copied_file_sizes))


def extract_patches_in_location(corpus_loc, project, commit_idx, git_commit):
    valid_mod_files = [mod_file for mod_file in git_commit.modified_files if
        not bl.is_blacklisted(get_file_name(mod_file)) and
        not mod_file.added_lines + mod_file.deleted_lines == 0 and
        get_file_name(mod_file).endswith(".php")
        ]
    if len(valid_mod_files) == 0:
        print(f"** No valid patches in commit")
        return (0, 0)
    dest_dir = os.path.join(corpus_loc, str(commit_idx) + "_" + project + "_" + str(git_commit.hash))
    create_dir_if_not_exist(dest_dir)
    copied_patch_sizes = []
    for idx, valid_mod_file in enumerate(valid_mod_files):
        patch_dir = os.path.join(dest_dir, str(idx) + "_" + os.path.splitext(os.path.basename(get_file_name(valid_mod_file)))[0])
        create_dir_if_not_exist(patch_dir)
        hunks = parse_hunks(valid_mod_file)
        deleted_lines = get_lines(hunks, "-")
        added_lines = get_lines(hunks, "+")
        deleted_lines_file = os.path.join(patch_dir, "deleted.php")
        added_lines_file = os.path.join(patch_dir, "added.php")
        with open(deleted_lines_file, "w+") as file:
            file.write(deleted_lines)
        copied_patch_sizes.append(os.path.getsize(deleted_lines_file))
        with open(added_lines_file, "w+") as file:
            file.write(added_lines)
        copied_patch_sizes.append(os.path.getsize(added_lines_file))
    return (len(copied_patch_sizes), sum(copied_patch_sizes))




# Check if there are command-line arguments
if len(sys.argv) > 1:
    file_path = sys.argv[1]
else:
    print("No command-line arguments provided. Exiting program.")
    sys.exit(1)

# Load the JSON file
with open(file_path, "r") as f:
    data = json.load(f)

# Access the singleUrl and commits
repo_url = data["singleUrl"]
commit_objects = data["commits"]
commits = [commit["sha"] for commit in commit_objects]

parts = repo_url.strip("/").split("/")
username = parts[-2]
repo_name = parts[-1]

corpus_full_dir = "full" #= os.path.join("/Users/jorismachon/Documents/thesis/BoW_data", "full")#, repo_name)
create_dir_if_not_exist(corpus_full_dir)
corpus_patches_dir = "patches" #os.path.join("/Users/jorismachon/Documents/thesis/BoW_data", "patches")#, repo_name)
create_dir_if_not_exist(corpus_patches_dir)

extracted_files_number = 0
extracted_files_size = 0
extracted_patches_number = 0
extracted_patches_size = 0


repo_dir = tempfile.mkdtemp()
try:
    git_repo = clone_repo(repo_url, repo_dir)
except GitCommandError:
    print("Could not clone the repository: skipping")
project = os.path.basename(os.path.normpath(repo_url))

for commit_idx, commit in enumerate(commits):
    try:
        git_commit = git_repo.get_commit(commit)
    except:
        print(f"** Could not get commit {commit}")
        continue
    print(f"* ({commit_idx+1}) Analyzing Commit {git_commit.hash}")

    number_files, size_files = extract_files_in_location(corpus_full_dir, project, commit_idx + 1, git_commit)
    if (number_files > 0):
        extracted_files_number += number_files
        extracted_files_size += size_files
        print("** Added: {} files ({} KB)".format(number_files, size_files))
        print("** Total: {} files ({} KB)".format(extracted_files_number, extracted_files_size))

    number_patches, size_patches = extract_patches_in_location(corpus_patches_dir, project, commit_idx + 1, git_commit)
    if (number_patches > 0):
        extracted_patches_number += number_patches
        extracted_patches_size += size_patches
        print("** Added: {} patches ({} KB)".format(number_patches, size_patches))
        print("** Total: {} patches ({} KB)".format(extracted_patches_number, extracted_patches_size))

clean_repo(git_repo, repo_dir)
