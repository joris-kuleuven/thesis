from pydriller import Git
from git import GitCommandError, Repo
import os
import re
from pydriller import ModificationType
import json

def get_file_name(file):
    file_path = file.old_path
    # If this happens, then the file has been created in this commit
    if file_path == None:
        file_path = file.new_path
    return file_path

def is_file_valid(file_path):
    # Extension check
    file_extension = os.path.splitext(file_path)[1]
    if file_extension in invalid_extensions:
        return False
    # Excluded files check
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    if re.match(exclusions, file_name, re.IGNORECASE):
        return False
    # Test files
    file_dir = '/' + os.path.dirname(file_path) + '/'
    directory_match = re.match(r"^.*\/tests?\/.*$", file_dir, re.IGNORECASE)
    prefix_match = re.match(r"^test.+", file_name, re.IGNORECASE)
    postfix_match = re.match(r".+test$", file_name, re.IGNORECASE)
    return not (directory_match or prefix_match or postfix_match)

invalid_extensions = ('.txt', '.md', '.man', '.lang', '.loc', '.tex', '.texi', '.rst',
'.gif', '.png', '.jpg', '.jpeg', '.svg', '.ico',
'.css', '.scss', '.less',
'.gradle', '.ini',
'.zip',
'.pdf')
exclusions = r"^(install|changelog(s)?|change(s)?|author(s)?|news|readme|todo|about(s)?|credit(s)?|license|release(s)?|release(s)?|release(_|-)note(s)?|version(s)?|makefile|pom|\.git.*|\.travis|\.classpath|\.project)$"

def get_fix_files(commit):
    fix_files = []
    for mod_file in commit.modified_files:
        file_path = get_file_name(mod_file)
        #print(file_path)
        if not is_file_valid(file_path):
            continue
        fix_files.append(file_path)
    return fix_files

def print_blames(blamed):
    all_blamed_hashes = {blame for blames in blamed.values() for blame in blames}
    print("*** Blamed {} commit(s)".format(len(all_blamed_hashes)))
    
def blame_deleted_lines(git_repo, fix_commit, fix_files):
    print("** Blaming the deleted lines...")
    blames = git_repo.get_commits_last_modified_lines(fix_commit)
    blamed_from_deleted_lines = {}
    for file, blamed_hashes in blames.items():
        if file not in fix_files:
            continue
        blamed_from_deleted_lines[file] = blamed_hashes
    print_blames(blamed_from_deleted_lines)
    return blamed_from_deleted_lines

def is_useless_line(line):
    return not line or \
            line.startswith("//") or \
            line.startswith("/*") or \
            line.startswith("*") or \
            line.startswith("#") or \
            line.startswith("'''") or \
            line.startswith('"""') or \
            line.startswith("=begin") or \
            line.startswith("<#") or \
            line.startswith("--") or \
            line.startswith("{-") or \
            line.startswith("--[[") or \
            line.startswith("<!--")

def parse_hunks(diff):
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
        # Ignore very small hungs, which are very rare
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

def is_valid_hunk(hunk, modified_file, commit):
    # We are interested in change blocks made of added lines only
    if not all(line.startswith("+") for line in hunk["change_block"]):
        print("In validating hunk: hunk is not valid because the lines in the change block are not all added lines")
        return False

    # If the change block is made ONLY of the following invalid lines, it is invalid for the blame
    first_line_block = int(hunk["new_start_line"]) + len(hunk["before_ctx"])
    last_line_block = first_line_block + len(hunk["change_block"]) - 1
    invalid_lines = []

    ## Step 1: useless lines are invalid
    for index, line in enumerate(hunk["change_block"]):
        if is_useless_line(line[1:].strip()):
            invalid_lines.append(index + first_line_block)
            print(f"invalid line detected in commit {commit.hash} because it is useless")
    ## Step 2: if the changed method entirely fits in the changed block, then it is a new method, and its lines are all invalid
    changed_methods = modified_file.changed_methods
    for m in changed_methods:
        if first_line_block <= m.start_line and m.end_line <= last_line_block:
            invalid_lines.extend(range(m.start_line, m.end_line + 1))
            print(f"invalid line detected in commit {commit.hash} because it is a method and fits entirely in the changed block")
    ## Step 3: if a line doesn't belong to any method (constants, global variables, typedefs, etc.), it is invalid
    methods = modified_file.methods
    for i in range(first_line_block, last_line_block + 1):
        inside = False
        for m in methods:
            if m.start_line <= i and i <= m.end_line:
                inside = True
                break
        if not inside:
            invalid_lines.append(i)
            print(f"invalid line detected in commit {commit.hash} because it does not belong to any method")
            

    # Remove duplicates and sort
    invalid_lines = sorted(list(set(invalid_lines)))
    if invalid_lines == list(range(first_line_block, last_line_block + 1)):
        return False
    return True

def blame_context_lines(git_repo, fix_commit, fix_files):
    print("** Blaming the context lines for add-only hunks...")
    blamed_from_context_lines = {}
    for modified_file in fix_commit.modified_files:
        filepath = get_file_name(modified_file)
        # We don't consider new files because they won't blame anything
        if modified_file.change_type == ModificationType.ADD:
            print(f"In blaming context lines: modified file is a new file in commit {fix_commit.hash}")
            continue
        # Consider only the files previously appoved
        if not filepath in fix_files:
            print("In blaming context lines: file path is not in fix files")
            continue
        hunks = parse_hunks(modified_file.diff)
        blamed_hashes = set()
        for hunk in hunks:
            # Do not consider invalid hunks
            if not is_valid_hunk(hunk, modified_file, fix_commit):
                print(f"In blaming context lines: hunk is not valid in commit {fix_commit.hash}")
                continue

            # At this point, we are sure that the hunk is made of added lines only, we can safely consider the "old start line + offset" to blame the entire hunk context only
            start_line = str(hunk["old_start_line"])
            offset = "+" + hunk["old_length"]
            # If the file is not found in the previous commits, it may be due to, rare, double renaming: we ignore these cases
            try:
                blame_output = git_repo.repo.git.blame("-w", "-c", "-l", "-L", start_line + "," + offset, fix_commit.hash + "^", "--", filepath)
            except GitCommandError:
                print(GitCommandError)
                continue
            #print("In blaming context lines: About to make the blames...")
            blamed_hashes = set()
            for blame_line in blame_output.splitlines():
                blame_line_split = blame_line.split("\t")
                blamed_hash = blame_line_split[0]
                #line_number = blame_line_split[3].split(")")[0]
                code = blame_line_split[3].split(")")[1].strip()
                # Should an empty line be blamed, ignore it
                if not code:
                    continue
                blamed_hashes.add(blamed_hash)
            blamed_from_context_lines[filepath] = blamed_hashes
    #print_blames(blamed_from_context_lines)
    return blamed_from_context_lines