import json
import os
import sys
import tempfile

import pandas as pd
from git import GitCommandError
from halo import Halo

sys.path.insert(0, "..")
from repo_utils import clean_repo, clone_repo
from tokens import extract_token_differences, extract_tokens

absolute_out_filepath = ".."
full_tokens_out_filepath = os.path.join(absolute_out_filepath, "full_tokens.csv")
patches_tokens_out_filepath = os.path.join(absolute_out_filepath, "patches_tokens.csv")
# Check if there are command-line arguments
if len(sys.argv) > 1:
    # Access the command-line arguments
    input_filepath = sys.argv[1]
else:
    print("No command-line arguments provided. Exiting program.")
    sys.exit(1)




enable_tokens = 1

if enable_tokens:
    if len(sys.argv) < 2:
        print("Please, specify a path that contains the corpus (files) for the tokens extraction. Exiting.")
        sys.exit(1)
    corpus_loc = input_filepath #"/Users/jorismachon/Documents/thesis/BoW_data"
    corpus_full_dir = os.path.join(corpus_loc, "full")
    corpus_patches_dir = os.path.join(corpus_loc, "patches",)


if enable_tokens:
    with Halo(text=f"Counting tokens from corpus of full files", spinner="dots"):
        full_tokens = extract_tokens(corpus_full_dir)    
        full_tokens.to_csv(full_tokens_out_filepath, index=False)
    print(f"Tokens from files: {len(full_tokens.columns) - 2}")
    with Halo(text=f"Counting tokens from corpus of patches", spinner="dots"):
        patches_tokens = extract_token_differences(corpus_patches_dir)
        patches_tokens.to_csv(patches_tokens_out_filepath, index=False)
    print(f"Tokens from patches: {len(patches_tokens.columns) - 2}")