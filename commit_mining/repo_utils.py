import shutil

from git import GitCommandError, Repo
from halo import Halo
from pydriller import Git


def clone_repo(repo_url, repo_dir):
    parts = repo_url.split('://', 1)
    # This automatically skips private repositories
    repo_url_no_credentials = parts[0] + "://:@" + parts[1]
    try:
        with Halo(text=f"Cloning from {repo_url}", spinner="dots"):
            Repo.clone_from(repo_url_no_credentials, repo_dir)
    except GitCommandError as ger:
        raise ger
    git_repo = Git(repo_dir)
    git_repo.reset()
    return git_repo


def clean_repo(git_repo, repo_dir):
    git_repo.clear()
    del git_repo
    shutil.rmtree(repo_dir, ignore_errors=True)


def restore_repo(git_repo):
    git_repo.repo.git.reset("--hard")
    git_repo.repo.git.clean("-xdf")
    git_repo.repo.heads[0].checkout()
    git_repo.repo.git.reset("--hard")
    git_repo.repo.git.clean("-xdf")
